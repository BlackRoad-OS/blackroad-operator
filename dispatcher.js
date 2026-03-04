/**
 * @BLACKROAD OPERATOR - Agent Deployment Dispatcher
 * BlackRoad OS, Inc. © 2026
 *
 * Coordinates multi-agent deployments. Assigns roles, dispatches
 * stages to agents, and tracks progress through the pipeline.
 */

import { createDeploymentTask, advanceStage, failStage, TASK_TEMPLATES } from './tasks.js';

/**
 * Dispatcher - orchestrates agent deployment workflows
 */
export class Dispatcher {
  constructor(env) {
    this.env = env;
  }

  /**
   * Launch a deployment from a template
   */
  async launch(templateName, params, sourceOrg) {
    const task = createDeploymentTask(templateName, params);
    task.source_org = sourceOrg || 'BlackRoad-OS';

    // Recruit agents for each role
    const agents = await this.recruitAgents(task);
    task.assigned_agents = agents;

    if (Object.keys(agents).length < task.required_agents) {
      task.status = 'waiting_for_agents';
    } else {
      // Kick off the first stage
      advanceStage(task);
      const firstStage = task.stages.find(s => s.status === 'running');
      if (firstStage) {
        const role = task.roles[0];
        firstStage.agent_id = agents[role] || null;
      }
    }

    // Persist
    await this.saveTask(task);
    await this.logEvent(task.task_id, 'launched', {
      template: templateName,
      agents,
      params
    });

    return task;
  }

  /**
   * Recruit agents for required roles
   */
  async recruitAgents(task) {
    const registry = await this.env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};
    const assigned = {};

    for (const role of task.roles) {
      const candidates = Object.entries(registry)
        .filter(([id, agent]) =>
          agent.status === 'active' &&
          agent.current_tasks < (agent.max_tasks || 10) &&
          (agent.roles || []).includes(role)
        )
        .sort(([, a], [, b]) => a.current_tasks - b.current_tasks);

      if (candidates.length > 0) {
        const [agentId, agent] = candidates[0];
        assigned[role] = agentId;

        // Increment task count
        registry[agentId].current_tasks = (agent.current_tasks || 0) + 1;
      }
    }

    // Save updated registry
    await this.env.AGENT_REGISTRY.put('agents', JSON.stringify(registry));
    return assigned;
  }

  /**
   * Report progress on a stage (called by agents)
   */
  async reportProgress(taskId, agentId, stageOutput) {
    const task = await this.getTask(taskId);
    if (!task) throw new Error(`Task not found: ${taskId}`);

    const currentStage = task.stages.find(s => s.status === 'running');
    if (!currentStage) throw new Error('No running stage');

    if (currentStage.agent_id && currentStage.agent_id !== agentId) {
      throw new Error('Agent not assigned to current stage');
    }

    // Move to next stage
    advanceStage(task, stageOutput);

    // Assign next stage agent
    const nextStage = task.stages.find(s => s.status === 'running');
    if (nextStage) {
      const stageIdx = task.stages.indexOf(nextStage);
      const role = task.roles[Math.min(stageIdx, task.roles.length - 1)];
      nextStage.agent_id = task.assigned_agents[role] || null;
    }

    // If completed, release agents
    if (task.status === 'completed') {
      await this.releaseAgents(task);
    }

    await this.saveTask(task);
    await this.logEvent(taskId, 'stage_completed', { agent: agentId, output: stageOutput });

    return task;
  }

  /**
   * Report a failure on the current stage
   */
  async reportFailure(taskId, agentId, error) {
    const task = await this.getTask(taskId);
    if (!task) throw new Error(`Task not found: ${taskId}`);

    failStage(task, error);

    if (task.status === 'failed') {
      await this.releaseAgents(task);
    }

    await this.saveTask(task);
    await this.logEvent(taskId, 'stage_failed', { agent: agentId, error });

    return task;
  }

  /**
   * Chain multiple deployments in sequence
   */
  async launchChain(steps, sourceOrg) {
    const chainId = `chain-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const chain = {
      chain_id: chainId,
      steps: steps.map((step, i) => ({
        order: i,
        template: step.template,
        params: step.params || {},
        task_id: null,
        status: i === 0 ? 'ready' : 'waiting'
      })),
      status: 'running',
      source_org: sourceOrg || 'BlackRoad-OS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Launch the first step
    const firstTask = await this.launch(chain.steps[0].template, chain.steps[0].params, sourceOrg);
    chain.steps[0].task_id = firstTask.task_id;
    chain.steps[0].status = 'running';

    await this.env.WATERFALL_LOG.put(chainId, JSON.stringify(chain));
    return chain;
  }

  /**
   * Get deployment status overview
   */
  async getDeploymentStatus(taskId) {
    const task = await this.getTask(taskId);
    if (!task) return null;

    const completedStages = task.stages.filter(s => s.status === 'completed').length;
    const totalStages = task.stages.length;
    const currentStage = task.stages.find(s => s.status === 'running');

    return {
      task_id: task.task_id,
      template: task.template,
      status: task.status,
      progress: `${completedStages}/${totalStages}`,
      progress_pct: Math.round((completedStages / totalStages) * 100),
      current_stage: currentStage ? currentStage.name : null,
      assigned_agents: task.assigned_agents,
      created_at: task.created_at,
      updated_at: task.updated_at,
      completed_at: task.completed_at
    };
  }

  /**
   * List all active deployments
   */
  async listActiveDeployments() {
    const tasks = await this.env.WATERFALL_LOG.list({ prefix: 'deploy-', limit: 200 });
    const active = [];

    for (const key of tasks.keys) {
      const task = await this.env.WATERFALL_LOG.get(key.name, { type: 'json' });
      if (task && ['queued', 'running', 'retrying', 'waiting_for_agents'].includes(task.status)) {
        active.push(await this.getDeploymentStatus(task.task_id));
      }
    }

    return active;
  }

  /**
   * Release agents when a task completes or fails
   */
  async releaseAgents(task) {
    const registry = await this.env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

    for (const agentId of Object.values(task.assigned_agents)) {
      if (registry[agentId]) {
        registry[agentId].current_tasks = Math.max(0, (registry[agentId].current_tasks || 1) - 1);
      }
    }

    await this.env.AGENT_REGISTRY.put('agents', JSON.stringify(registry));
  }

  // --- Storage helpers ---

  async getTask(taskId) {
    return this.env.WATERFALL_LOG.get(taskId, { type: 'json' });
  }

  async saveTask(task) {
    await this.env.WATERFALL_LOG.put(task.task_id, JSON.stringify(task));
  }

  async logEvent(taskId, event, data) {
    const logKey = `log-${taskId}-${Date.now()}`;
    await this.env.WATERFALL_LOG.put(logKey, JSON.stringify({
      task_id: taskId,
      event,
      data,
      timestamp: new Date().toISOString()
    }));
  }
}
