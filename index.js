/**
 * @BLACKROAD OPERATOR - Central Intelligence Router
 * BlackRoad OS, Inc. © 2026
 *
 * The brain of the 30,000 agent empire.
 * Routes all @blackroad mentions through waterfall cascade.
 * Dispatches deployment tasks to AI agents across all orgs.
 */

import { TASK_TEMPLATES, TASK_TYPES } from './tasks.js';
import { Dispatcher } from './dispatcher.js';

// Organization mapping
const ORGANIZATIONS = {
  'os': 'BlackRoad-OS',
  'ai': 'BlackRoad-AI',
  'cloud': 'BlackRoad-Cloud',
  'education': 'BlackRoad-Education',
  'foundation': 'BlackRoad-Foundation',
  'gov': 'BlackRoad-Gov',
  'hardware': 'BlackRoad-Hardware',
  'interactive': 'BlackRoad-Interactive',
  'labs': 'BlackRoad-Labs',
  'media': 'BlackRoad-Media',
  'security': 'BlackRoad-Security',
  'studio': 'BlackRoad-Studio',
  'ventures': 'BlackRoad-Ventures',
  'archive': 'BlackRoad-Archive'
};

// Product to organization mapping
const PRODUCTS = {
  'roadcommand': { org: 'os', dept: 'products', priority: 'critical' },
  'roadwork': { org: 'education', dept: 'products', priority: 'high' },
  'pitstop': { org: 'os', dept: 'products', priority: 'high' },
  'fastlane': { org: 'studio', dept: 'products', priority: 'medium' },
  'backroad': { org: 'media', dept: 'products', priority: 'medium' },
  'loadroad': { org: 'os', dept: 'products', priority: 'high' },
  'roadcoin': { org: 'ventures', dept: 'products', priority: 'high' },
  'lucidia': { org: 'ai', dept: 'products', priority: 'critical' },
  'roadflow': { org: 'os', dept: 'products', priority: 'medium' },
  'video-studio': { org: 'studio', dept: 'products', priority: 'medium' },
  'writing-studio': { org: 'studio', dept: 'products', priority: 'medium' }
};

/**
 * Parse intent from natural language mention
 */
function parseIntent(mention) {
  const lower = mention.toLowerCase();

  // Extract product mentions
  const products = Object.keys(PRODUCTS).filter(p => lower.includes(p));

  // Extract action keywords
  const actions = {
    deploy: /deploy|push|release|ship/i.test(mention),
    enhance: /enhance|improve|upgrade|add|feature/i.test(mention),
    fix: /fix|bug|issue|problem|error/i.test(mention),
    test: /test|qa|verify|validate/i.test(mention),
    docs: /document|docs|guide|readme/i.test(mention),
    review: /review|audit|check|inspect/i.test(mention),
    monitor: /monitor|status|health|check/i.test(mention)
  };

  const primaryAction = Object.keys(actions).find(a => actions[a]) || 'general';

  // Extract Pi mentions
  const pis = ['octavia', 'shellfish', 'aria', 'alice', 'lucidia'].filter(p =>
    lower.includes(p)
  );

  return {
    products,
    action: primaryAction,
    pis,
    urgency: lower.includes('urgent') || lower.includes('asap') ? 'urgent' : 'normal',
    original: mention
  };
}

/**
 * Route to appropriate organization
 */
function routeToOrg(intent, fallbackOrg) {
  if (intent.products.length > 0) {
    const product = PRODUCTS[intent.products[0]];
    return ORGANIZATIONS[product.org];
  }

  // Check for org-specific keywords
  if (intent.original.includes('infrastructure') || intent.pis.length > 0) {
    return 'BlackRoad-Cloud';
  }
  if (intent.original.includes('ai') || intent.original.includes('model')) {
    return 'BlackRoad-AI';
  }
  if (intent.original.includes('design') || intent.original.includes('ui')) {
    return 'BlackRoad-Studio';
  }

  // Default to fallback or OS
  return fallbackOrg || 'BlackRoad-OS';
}

/**
 * Find appropriate department
 */
function findDepartment(intent, org) {
  if (intent.products.length > 0) {
    return 'products';
  }

  switch (intent.action) {
    case 'deploy':
      return 'infrastructure';
    case 'enhance':
    case 'fix':
      return 'products';
    case 'test':
      return 'testing';
    case 'docs':
      return 'documentation';
    case 'review':
      return 'security';
    case 'monitor':
      return 'infrastructure';
    default:
      return 'general';
  }
}

/**
 * Assign to best available agent
 */
async function assignAgent(env, department, intent) {
  // Query agent registry
  const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

  // Filter by department and availability
  const available = Object.entries(registry)
    .filter(([id, agent]) =>
      agent.department === department &&
      agent.status === 'active' &&
      agent.current_tasks < agent.max_tasks
    )
    .map(([id, agent]) => ({ id, ...agent }));

  if (available.length === 0) {
    // No agents available, queue task
    return null;
  }

  // Sort by workload (fewest tasks first)
  available.sort((a, b) => a.current_tasks - b.current_tasks);

  return available[0].id;
}

/**
 * JSON response helper
 */
function jsonResponse(data, status = 200, corsHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

/**
 * Main waterfall handler
 */
export default {
  async fetch(request, env, ctx) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);
    const dispatcher = new Dispatcher(env);

    // ─── Health check ───
    if (url.pathname === '/health') {
      return jsonResponse({
        status: 'operational',
        version: '1.1.0',
        features: ['waterfall', 'deployments', 'agent-health'],
        timestamp: new Date().toISOString()
      }, 200, corsHeaders);
    }

    // ─── Waterfall endpoint ───
    if (url.pathname === '/api/waterfall' && request.method === 'POST') {
      try {
        const { mention, org, repo, type } = await request.json();

        // Parse intent
        const intent = parseIntent(mention);

        // Route to organization
        const targetOrg = routeToOrg(intent, org);

        // Find department
        const department = findDepartment(intent, targetOrg);

        // Assign agent
        const agent = await assignAgent(env, department, intent);

        // Create task ID
        const taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Log to KV
        await env.WATERFALL_LOG.put(taskId, JSON.stringify({
          task_id: taskId,
          intent,
          org: targetOrg,
          department,
          agent,
          source_repo: repo,
          source_type: type,
          status: agent ? 'assigned' : 'queued',
          created_at: new Date().toISOString()
        }));

        return jsonResponse({
          status: 'cascaded',
          task_id: taskId,
          assigned_to: agent || 'queued',
          organization: targetOrg,
          department
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Agent registration ───
    if (url.pathname === '/api/agents/register' && request.method === 'POST') {
      try {
        const agent = await request.json();

        // Validate
        if (!agent.agent_id || !agent.org || !agent.department) {
          return jsonResponse({ error: 'Missing required fields: agent_id, org, department' }, 400, corsHeaders);
        }

        // Get current registry
        const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

        // Add agent
        registry[agent.agent_id] = {
          ...agent,
          roles: agent.roles || [],
          registered_at: new Date().toISOString(),
          last_heartbeat: new Date().toISOString(),
          current_tasks: 0,
          max_tasks: agent.max_tasks || 10,
          status: 'active'
        };

        // Save registry
        await env.AGENT_REGISTRY.put('agents', JSON.stringify(registry));

        return jsonResponse({
          status: 'registered',
          agent_id: agent.agent_id
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Agent heartbeat ───
    if (url.pathname === '/api/agents/heartbeat' && request.method === 'POST') {
      try {
        const { agent_id, status: agentStatus, metrics } = await request.json();

        if (!agent_id) {
          return jsonResponse({ error: 'Missing agent_id' }, 400, corsHeaders);
        }

        const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

        if (!registry[agent_id]) {
          return jsonResponse({ error: 'Agent not registered' }, 404, corsHeaders);
        }

        registry[agent_id].last_heartbeat = new Date().toISOString();
        if (agentStatus) registry[agent_id].status = agentStatus;
        if (metrics) registry[agent_id].metrics = metrics;

        await env.AGENT_REGISTRY.put('agents', JSON.stringify(registry));

        return jsonResponse({
          status: 'ok',
          agent_id,
          acknowledged: new Date().toISOString()
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Agent list ───
    if (url.pathname === '/api/agents' && request.method === 'GET') {
      const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

      // Optionally filter by status or org
      const filterStatus = url.searchParams.get('status');
      const filterOrg = url.searchParams.get('org');
      const filterRole = url.searchParams.get('role');

      let agents = Object.entries(registry);

      if (filterStatus) {
        agents = agents.filter(([, a]) => a.status === filterStatus);
      }
      if (filterOrg) {
        agents = agents.filter(([, a]) => a.org === filterOrg);
      }
      if (filterRole) {
        agents = agents.filter(([, a]) => (a.roles || []).includes(filterRole));
      }

      return jsonResponse({
        total: agents.length,
        agents: Object.fromEntries(agents)
      }, 200, corsHeaders);
    }

    // ─── Deploy: launch a deployment ───
    if (url.pathname === '/api/deploy' && request.method === 'POST') {
      try {
        const { template, params, org } = await request.json();

        if (!template || !TASK_TEMPLATES[template]) {
          return jsonResponse({
            error: 'Invalid template',
            available: Object.keys(TASK_TEMPLATES)
          }, 400, corsHeaders);
        }

        const task = await dispatcher.launch(template, params || {}, org);

        return jsonResponse({
          status: 'deployment_launched',
          task_id: task.task_id,
          template,
          stages: task.stages.map(s => s.name),
          assigned_agents: task.assigned_agents,
          deployment_status: task.status
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Deploy: chain multiple deployments ───
    if (url.pathname === '/api/deploy/chain' && request.method === 'POST') {
      try {
        const { steps, org } = await request.json();

        if (!steps || !Array.isArray(steps) || steps.length === 0) {
          return jsonResponse({ error: 'steps must be a non-empty array' }, 400, corsHeaders);
        }

        // Validate each step has a valid template
        for (const step of steps) {
          if (!step.template || !TASK_TEMPLATES[step.template]) {
            return jsonResponse({
              error: `Invalid template: ${step.template}`,
              available: Object.keys(TASK_TEMPLATES)
            }, 400, corsHeaders);
          }
        }

        const chain = await dispatcher.launchChain(steps, org);

        return jsonResponse({
          status: 'chain_launched',
          chain_id: chain.chain_id,
          total_steps: chain.steps.length,
          steps: chain.steps.map(s => ({
            template: s.template,
            status: s.status,
            task_id: s.task_id
          }))
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Deploy: report progress (agents call this) ───
    if (url.pathname === '/api/deploy/progress' && request.method === 'POST') {
      try {
        const { task_id, agent_id, output } = await request.json();

        if (!task_id || !agent_id) {
          return jsonResponse({ error: 'Missing task_id or agent_id' }, 400, corsHeaders);
        }

        const task = await dispatcher.reportProgress(task_id, agent_id, output);

        return jsonResponse({
          status: 'progress_recorded',
          task_id: task.task_id,
          deployment_status: task.status,
          current_stage: task.stages.find(s => s.status === 'running')?.name || null,
          completed_stages: task.stages.filter(s => s.status === 'completed').length,
          total_stages: task.stages.length
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Deploy: report failure (agents call this) ───
    if (url.pathname === '/api/deploy/fail' && request.method === 'POST') {
      try {
        const { task_id, agent_id, error: failError } = await request.json();

        if (!task_id || !agent_id) {
          return jsonResponse({ error: 'Missing task_id or agent_id' }, 400, corsHeaders);
        }

        const task = await dispatcher.reportFailure(task_id, agent_id, failError);

        return jsonResponse({
          status: task.status === 'retrying' ? 'retrying' : 'deployment_failed',
          task_id: task.task_id,
          deployment_status: task.status,
          retry_attempt: task.retry.attempts,
          max_retries: task.retry.max_attempts
        }, 200, corsHeaders);

      } catch (error) {
        return jsonResponse({ error: error.message }, 500, corsHeaders);
      }
    }

    // ─── Deploy: get status ───
    if (url.pathname.startsWith('/api/deploy/status/') && request.method === 'GET') {
      const taskId = url.pathname.replace('/api/deploy/status/', '');
      const status = await dispatcher.getDeploymentStatus(taskId);

      if (!status) {
        return jsonResponse({ error: 'Deployment not found' }, 404, corsHeaders);
      }

      return jsonResponse(status, 200, corsHeaders);
    }

    // ─── Deploy: list active deployments ───
    if (url.pathname === '/api/deploy/active' && request.method === 'GET') {
      const active = await dispatcher.listActiveDeployments();

      return jsonResponse({
        total: active.length,
        deployments: active
      }, 200, corsHeaders);
    }

    // ─── Deploy: list available templates ───
    if (url.pathname === '/api/deploy/templates' && request.method === 'GET') {
      const templates = Object.entries(TASK_TEMPLATES).map(([name, tmpl]) => ({
        name,
        type: tmpl.type,
        stages: tmpl.stages,
        required_agents: tmpl.required_agents,
        roles: tmpl.roles,
        timeout_ms: tmpl.timeout_ms
      }));

      return jsonResponse({ templates }, 200, corsHeaders);
    }

    // ─── Task history ───
    if (url.pathname === '/api/tasks' && request.method === 'GET') {
      const limit = parseInt(url.searchParams.get('limit') || '100');
      const prefix = url.searchParams.get('prefix') || '';

      const tasks = await env.WATERFALL_LOG.list({ limit, prefix: prefix || undefined });
      const taskData = await Promise.all(
        tasks.keys.map(async (key) => {
          const data = await env.WATERFALL_LOG.get(key.name, { type: 'json' });
          return data;
        })
      );

      return jsonResponse({
        total: tasks.keys.length,
        tasks: taskData.filter(Boolean)
      }, 200, corsHeaders);
    }

    // Default 404
    return new Response('Not Found', { status: 404 });
  }
};
