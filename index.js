/**
 * @BLACKROAD OPERATOR - Central Intelligence Router
 * BlackRoad OS, Inc. © 2026
 *
 * The brain of the 30,000 agent empire.
 * Routes all @blackroad mentions through waterfall cascade.
 */

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
 * Main waterfall handler
 */
export default {
  async fetch(request, env, ctx) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'operational',
        version: '1.0.0',
        timestamp: new Date().toISOString()
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Waterfall endpoint
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

        // If agent assigned, notify them
        if (agent) {
          // TODO: Implement hash-calling notification
          // await notifyAgent(agent, taskId, intent);
        }

        return new Response(JSON.stringify({
          status: 'cascaded',
          task_id: taskId,
          assigned_to: agent || 'queued',
          organization: targetOrg,
          department
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

      } catch (error) {
        return new Response(JSON.stringify({
          error: error.message
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Agent registration endpoint
    if (url.pathname === '/api/agents/register' && request.method === 'POST') {
      try {
        const agent = await request.json();

        // Validate
        if (!agent.agent_id || !agent.org || !agent.department) {
          return new Response(JSON.stringify({
            error: 'Missing required fields'
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        // Get current registry
        const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

        // Add agent
        registry[agent.agent_id] = {
          ...agent,
          registered_at: new Date().toISOString(),
          current_tasks: 0,
          max_tasks: 10,
          status: 'active'
        };

        // Save registry
        await env.AGENT_REGISTRY.put('agents', JSON.stringify(registry));

        return new Response(JSON.stringify({
          status: 'registered',
          agent_id: agent.agent_id
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

      } catch (error) {
        return new Response(JSON.stringify({
          error: error.message
        }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }

    // Agent list endpoint
    if (url.pathname === '/api/agents' && request.method === 'GET') {
      const registry = await env.AGENT_REGISTRY.get('agents', { type: 'json' }) || {};

      return new Response(JSON.stringify({
        total: Object.keys(registry).length,
        agents: registry
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Task history endpoint
    if (url.pathname === '/api/tasks' && request.method === 'GET') {
      // List recent tasks from KV
      const tasks = await env.WATERFALL_LOG.list({ limit: 100 });
      const taskData = await Promise.all(
        tasks.keys.map(async (key) => {
          const data = await env.WATERFALL_LOG.get(key.name, { type: 'json' });
          return data;
        })
      );

      return new Response(JSON.stringify({
        total: tasks.keys.length,
        tasks: taskData
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Default 404
    return new Response('Not Found', { status: 404 });
  }
};
