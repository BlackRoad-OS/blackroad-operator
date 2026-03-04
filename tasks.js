/**
 * @BLACKROAD OPERATOR - Agent Deployment Tasks
 * BlackRoad OS, Inc. © 2026
 *
 * Deployment task definitions, templates, and pipeline stages
 * for dispatching work across the 30,000 agent network.
 */

// Deployment task types
export const TASK_TYPES = {
  DEPLOY_SERVICE: 'deploy_service',
  DEPLOY_MODEL: 'deploy_model',
  DEPLOY_WORKER: 'deploy_worker',
  DEPLOY_SITE: 'deploy_site',
  DEPLOY_API: 'deploy_api',
  DEPLOY_DATABASE: 'deploy_database',
  DEPLOY_PIPELINE: 'deploy_pipeline',
  ROLLBACK: 'rollback',
  SCALE: 'scale',
  MIGRATE: 'migrate',
  SYNC_AGENTS: 'sync_agents',
  CHAIN: 'chain'
};

// Pipeline stages every deployment flows through
export const PIPELINE_STAGES = [
  'queued',
  'validating',
  'building',
  'testing',
  'deploying',
  'verifying',
  'completed',
  'failed',
  'rolled_back'
];

// Deployment task templates - pre-built workflows agents can execute
export const TASK_TEMPLATES = {
  // Full-stack service deployment across orgs
  'service-deploy': {
    type: TASK_TYPES.DEPLOY_SERVICE,
    stages: ['validate', 'build', 'test', 'deploy', 'verify'],
    required_agents: 3,
    roles: ['builder', 'tester', 'deployer'],
    timeout_ms: 300000,
    retry: { max_attempts: 3, backoff_ms: 5000 }
  },

  // AI model deployment to inference endpoints
  'model-deploy': {
    type: TASK_TYPES.DEPLOY_MODEL,
    stages: ['validate', 'package', 'benchmark', 'deploy', 'smoke-test'],
    required_agents: 2,
    roles: ['ml-engineer', 'deployer'],
    timeout_ms: 600000,
    retry: { max_attempts: 2, backoff_ms: 10000 }
  },

  // Cloudflare Worker deployment
  'worker-deploy': {
    type: TASK_TYPES.DEPLOY_WORKER,
    stages: ['validate', 'bundle', 'deploy', 'verify'],
    required_agents: 1,
    roles: ['deployer'],
    timeout_ms: 120000,
    retry: { max_attempts: 3, backoff_ms: 3000 }
  },

  // Static site / frontend deployment
  'site-deploy': {
    type: TASK_TYPES.DEPLOY_SITE,
    stages: ['validate', 'build', 'optimize', 'deploy', 'cdn-purge'],
    required_agents: 2,
    roles: ['builder', 'deployer'],
    timeout_ms: 180000,
    retry: { max_attempts: 3, backoff_ms: 5000 }
  },

  // API endpoint deployment
  'api-deploy': {
    type: TASK_TYPES.DEPLOY_API,
    stages: ['validate', 'build', 'test', 'deploy', 'health-check'],
    required_agents: 2,
    roles: ['builder', 'deployer'],
    timeout_ms: 240000,
    retry: { max_attempts: 3, backoff_ms: 5000 }
  },

  // Database migration
  'db-migrate': {
    type: TASK_TYPES.DEPLOY_DATABASE,
    stages: ['validate', 'backup', 'migrate', 'verify', 'cleanup'],
    required_agents: 2,
    roles: ['dba', 'deployer'],
    timeout_ms: 600000,
    retry: { max_attempts: 1, backoff_ms: 0 }
  },

  // Multi-step pipeline deployment
  'pipeline-deploy': {
    type: TASK_TYPES.DEPLOY_PIPELINE,
    stages: ['validate', 'provision', 'configure', 'deploy', 'integrate', 'verify'],
    required_agents: 4,
    roles: ['architect', 'builder', 'deployer', 'tester'],
    timeout_ms: 900000,
    retry: { max_attempts: 2, backoff_ms: 15000 }
  },

  // Rollback to previous version
  'rollback': {
    type: TASK_TYPES.ROLLBACK,
    stages: ['identify', 'rollback', 'verify'],
    required_agents: 1,
    roles: ['deployer'],
    timeout_ms: 120000,
    retry: { max_attempts: 2, backoff_ms: 3000 }
  },

  // Scale agents up/down
  'scale': {
    type: TASK_TYPES.SCALE,
    stages: ['evaluate', 'provision', 'configure', 'verify'],
    required_agents: 1,
    roles: ['orchestrator'],
    timeout_ms: 180000,
    retry: { max_attempts: 3, backoff_ms: 5000 }
  },

  // Sync state across agent clusters
  'agent-sync': {
    type: TASK_TYPES.SYNC_AGENTS,
    stages: ['snapshot', 'diff', 'propagate', 'verify'],
    required_agents: 2,
    roles: ['orchestrator', 'verifier'],
    timeout_ms: 300000,
    retry: { max_attempts: 3, backoff_ms: 5000 }
  },

  // Chained multi-agent task
  'chain-deploy': {
    type: TASK_TYPES.CHAIN,
    stages: ['plan', 'execute-sequence', 'verify-all'],
    required_agents: 5,
    roles: ['planner', 'builder', 'deployer', 'tester', 'verifier'],
    timeout_ms: 1200000,
    retry: { max_attempts: 1, backoff_ms: 0 }
  }
};

/**
 * Create a deployment task from a template
 */
export function createDeploymentTask(templateName, params) {
  const template = TASK_TEMPLATES[templateName];
  if (!template) {
    throw new Error(`Unknown deployment template: ${templateName}`);
  }

  const taskId = `deploy-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  return {
    task_id: taskId,
    template: templateName,
    type: template.type,
    stages: template.stages.map(stage => ({
      name: stage,
      status: 'pending',
      started_at: null,
      completed_at: null,
      agent_id: null,
      output: null
    })),
    required_agents: template.required_agents,
    roles: template.roles,
    assigned_agents: {},
    timeout_ms: template.timeout_ms,
    retry: { ...template.retry, attempts: 0 },
    params: params || {},
    status: 'queued',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    completed_at: null
  };
}

/**
 * Advance a deployment task to its next stage
 */
export function advanceStage(task, stageOutput) {
  const currentIdx = task.stages.findIndex(s => s.status === 'running');

  if (currentIdx >= 0) {
    task.stages[currentIdx].status = 'completed';
    task.stages[currentIdx].completed_at = new Date().toISOString();
    task.stages[currentIdx].output = stageOutput || null;
  }

  const nextIdx = task.stages.findIndex(s => s.status === 'pending');

  if (nextIdx >= 0) {
    task.stages[nextIdx].status = 'running';
    task.stages[nextIdx].started_at = new Date().toISOString();
    task.status = 'running';
  } else {
    task.status = 'completed';
    task.completed_at = new Date().toISOString();
  }

  task.updated_at = new Date().toISOString();
  return task;
}

/**
 * Fail a deployment task at the current stage
 */
export function failStage(task, error) {
  const currentIdx = task.stages.findIndex(s => s.status === 'running');

  if (currentIdx >= 0) {
    task.stages[currentIdx].status = 'failed';
    task.stages[currentIdx].completed_at = new Date().toISOString();
    task.stages[currentIdx].output = { error };
  }

  if (task.retry.attempts < task.retry.max_attempts) {
    task.retry.attempts++;
    task.status = 'retrying';
    // Reset the failed stage to pending for retry
    if (currentIdx >= 0) {
      task.stages[currentIdx].status = 'pending';
      task.stages[currentIdx].started_at = null;
      task.stages[currentIdx].completed_at = null;
      task.stages[currentIdx].output = null;
    }
  } else {
    task.status = 'failed';
  }

  task.updated_at = new Date().toISOString();
  return task;
}
