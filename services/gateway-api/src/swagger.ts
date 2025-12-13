/**
 * OpenAPI/Swagger Documentation
 * Agent 15: API Documentation
 * Created: 2025-12-13
 *
 * Complete API documentation for GeminiVideo Winner Ads system
 */

import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';
import { Express } from 'express';

const swaggerDefinition = {
  openapi: '3.0.0',
  info: {
    title: 'GeminiVideo Winner Ads API',
    version: '1.0.0',
    description: `
# GeminiVideo Winner Ads API

This API provides access to the GeminiVideo winner ad detection, replication, and budget optimization system.

## Features
- **Winner Detection**: Automatically identify high-performing ads based on CTR and ROAS
- **Winner Replication**: Clone successful ad patterns with variations
- **Budget Optimization**: Reallocate budget from underperformers to winners
- **RAG Integration**: Find similar winning patterns using vector search
- **Real-time Analytics**: Track performance metrics and ROI improvements

## Authentication
All endpoints require Bearer token authentication via Firebase Auth.

\`\`\`
Authorization: Bearer <your-token>
\`\`\`

## Rate Limits
- General API: 100 requests/minute
- Video Generation: 10 requests/5 minutes
- Budget Operations: 20 requests/minute
    `,
    contact: {
      name: 'GeminiVideo Support',
      email: 'support@geminivideo.app'
    },
    license: {
      name: 'Proprietary',
      url: 'https://geminivideo.app/terms'
    }
  },
  servers: [
    {
      url: process.env.API_URL || 'https://api.geminivideo.app',
      description: 'Production server'
    },
    {
      url: 'http://localhost:8080',
      description: 'Development server'
    }
  ],
  tags: [
    {
      name: 'Winners',
      description: 'Winner ad detection and management'
    },
    {
      name: 'Budget',
      description: 'Budget allocation and optimization'
    },
    {
      name: 'Analytics',
      description: 'Performance analytics and reporting'
    },
    {
      name: 'Campaigns',
      description: 'Campaign management'
    },
    {
      name: 'Health',
      description: 'System health and status'
    }
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: 'Firebase Auth JWT token'
      },
      apiKey: {
        type: 'apiKey',
        in: 'header',
        name: 'X-API-Key',
        description: 'API key for service-to-service communication'
      }
    },
    schemas: {
      Winner: {
        type: 'object',
        properties: {
          ad_id: { type: 'string', description: 'Unique ad identifier' },
          video_id: { type: 'string', description: 'Associated video ID' },
          campaign_id: { type: 'string', description: 'Parent campaign ID' },
          ctr: { type: 'number', format: 'float', description: 'Click-through rate (0-1)' },
          roas: { type: 'number', format: 'float', description: 'Return on ad spend' },
          impressions: { type: 'integer', description: 'Total impressions' },
          spend: { type: 'number', format: 'float', description: 'Total spend in USD' },
          revenue: { type: 'number', format: 'float', description: 'Total revenue in USD' },
          conversions: { type: 'integer', description: 'Number of conversions' },
          detected_at: { type: 'string', format: 'date-time' },
          creative_dna: { $ref: '#/components/schemas/CreativeDNA' }
        }
      },
      CreativeDNA: {
        type: 'object',
        properties: {
          hook_type: { type: 'string', enum: ['curiosity', 'problem_solution', 'testimonial', 'urgency', 'benefit'] },
          duration_seconds: { type: 'integer' },
          cta_type: { type: 'string', enum: ['shop_now', 'learn_more', 'sign_up', 'buy_now'] },
          color_palette: { type: 'array', items: { type: 'string' } },
          emotion_score: { type: 'number', format: 'float' },
          pace: { type: 'string', enum: ['slow', 'medium', 'fast'] },
          visual_elements: { type: 'array', items: { type: 'string' } }
        }
      },
      CloneRequest: {
        type: 'object',
        required: ['winner_ad_id'],
        properties: {
          winner_ad_id: { type: 'string', description: 'ID of winner ad to clone' },
          variations: { type: 'integer', default: 3, minimum: 1, maximum: 10 },
          variation_types: {
            type: 'array',
            items: { type: 'string', enum: ['hook_swap', 'cta_change', 'color_shift', 'pace_adjust'] }
          }
        }
      },
      CloneResponse: {
        type: 'object',
        properties: {
          success: { type: 'boolean' },
          cloned_ads: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                ad_id: { type: 'string' },
                original_ad_id: { type: 'string' },
                variation_type: { type: 'string' },
                status: { type: 'string', enum: ['pending_review', 'approved', 'active'] },
                created_at: { type: 'string', format: 'date-time' }
              }
            }
          }
        }
      },
      BudgetReallocationRequest: {
        type: 'object',
        properties: {
          account_id: { type: 'string' },
          max_reallocation_percent: { type: 'number', default: 20, minimum: 1, maximum: 50 },
          dry_run: { type: 'boolean', default: false }
        }
      },
      BudgetReallocationResponse: {
        type: 'object',
        properties: {
          success: { type: 'boolean' },
          reallocation: {
            type: 'object',
            properties: {
              status: { type: 'string', enum: ['completed', 'partial', 'no_action', 'dry_run'] },
              from_ads: { type: 'array', items: { type: 'string' } },
              to_ads: { type: 'array', items: { type: 'string' } },
              amount_reallocated: { type: 'number' },
              percentage_reallocated: { type: 'number' },
              timestamp: { type: 'string', format: 'date-time' }
            }
          }
        }
      },
      WinnerStats: {
        type: 'object',
        properties: {
          total_winners_24h: { type: 'integer' },
          total_winners_7d: { type: 'integer' },
          average_winner_ctr: { type: 'number', format: 'float' },
          average_winner_roas: { type: 'number', format: 'float' },
          total_budget_in_winners: { type: 'number' },
          roi_improvement: { type: 'number', format: 'float' },
          top_performing_hook_type: { type: 'string' }
        }
      },
      HealthResponse: {
        type: 'object',
        properties: {
          status: { type: 'string', enum: ['healthy', 'degraded', 'unhealthy'] },
          timestamp: { type: 'string', format: 'date-time' },
          uptime: { type: 'integer' },
          checks: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                status: { type: 'string' },
                latency: { type: 'number' }
              }
            }
          },
          version: { type: 'string' }
        }
      },
      Error: {
        type: 'object',
        properties: {
          success: { type: 'boolean', example: false },
          error: {
            type: 'object',
            properties: {
              code: { type: 'string' },
              message: { type: 'string' },
              requestId: { type: 'string' }
            }
          }
        }
      }
    },
    responses: {
      Unauthorized: {
        description: 'Authentication required',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      Forbidden: {
        description: 'Access denied',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      NotFound: {
        description: 'Resource not found',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      },
      RateLimited: {
        description: 'Rate limit exceeded',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/Error' }
          }
        }
      }
    }
  },
  paths: {
    '/api/winners/recent': {
      get: {
        tags: ['Winners'],
        summary: 'Get recent winners',
        description: 'Returns a list of recently detected winning ads based on CTR and ROAS thresholds',
        operationId: 'getRecentWinners',
        security: [{ bearerAuth: [] }],
        parameters: [
          {
            name: 'limit',
            in: 'query',
            schema: { type: 'integer', default: 10, minimum: 1, maximum: 100 }
          },
          {
            name: 'min_ctr',
            in: 'query',
            schema: { type: 'number', default: 0.03 },
            description: 'Minimum CTR threshold (0-1)'
          },
          {
            name: 'min_roas',
            in: 'query',
            schema: { type: 'number', default: 2.0 },
            description: 'Minimum ROAS threshold'
          },
          {
            name: 'days_back',
            in: 'query',
            schema: { type: 'integer', default: 7 },
            description: 'Number of days to look back'
          }
        ],
        responses: {
          '200': {
            description: 'List of winners',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    winners: { type: 'array', items: { $ref: '#/components/schemas/Winner' } },
                    meta: {
                      type: 'object',
                      properties: {
                        total: { type: 'integer' },
                        min_ctr: { type: 'number' },
                        min_roas: { type: 'number' }
                      }
                    }
                  }
                }
              }
            }
          },
          '401': { $ref: '#/components/responses/Unauthorized' },
          '429': { $ref: '#/components/responses/RateLimited' }
        }
      }
    },
    '/api/winners/{winnerId}': {
      get: {
        tags: ['Winners'],
        summary: 'Get winner details',
        description: 'Returns detailed information about a specific winning ad',
        operationId: 'getWinnerById',
        security: [{ bearerAuth: [] }],
        parameters: [
          {
            name: 'winnerId',
            in: 'path',
            required: true,
            schema: { type: 'string' }
          }
        ],
        responses: {
          '200': {
            description: 'Winner details',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    winner: { $ref: '#/components/schemas/Winner' }
                  }
                }
              }
            }
          },
          '404': { $ref: '#/components/responses/NotFound' }
        }
      }
    },
    '/api/winners/clone-winner': {
      post: {
        tags: ['Winners'],
        summary: 'Clone a winning ad',
        description: 'Creates variations of a winning ad for A/B testing',
        operationId: 'cloneWinner',
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/CloneRequest' }
            }
          }
        },
        responses: {
          '200': {
            description: 'Cloned ads created',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/CloneResponse' }
              }
            }
          },
          '400': {
            description: 'Invalid request',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' }
              }
            }
          }
        }
      }
    },
    '/api/winners/similar': {
      get: {
        tags: ['Winners'],
        summary: 'Find similar winners',
        description: 'Uses RAG to find winners with similar creative DNA',
        operationId: 'findSimilarWinners',
        security: [{ bearerAuth: [] }],
        parameters: [
          {
            name: 'ad_id',
            in: 'query',
            required: true,
            schema: { type: 'string' }
          },
          {
            name: 'k',
            in: 'query',
            schema: { type: 'integer', default: 5, minimum: 1, maximum: 20 }
          }
        ],
        responses: {
          '200': {
            description: 'Similar winners found',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    similar_winners: {
                      type: 'array',
                      items: {
                        type: 'object',
                        properties: {
                          ad_id: { type: 'string' },
                          similarity_score: { type: 'number' },
                          creative_dna: { $ref: '#/components/schemas/CreativeDNA' }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    '/api/winners/stats': {
      get: {
        tags: ['Analytics'],
        summary: 'Get winner statistics',
        description: 'Returns aggregated statistics about winning ads',
        operationId: 'getWinnerStats',
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Winner statistics',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    success: { type: 'boolean' },
                    stats: { $ref: '#/components/schemas/WinnerStats' }
                  }
                }
              }
            }
          }
        }
      }
    },
    '/api/winners/budget/reallocate': {
      post: {
        tags: ['Budget'],
        summary: 'Reallocate budget to winners',
        description: 'Automatically reallocates budget from underperforming ads to winners',
        operationId: 'reallocateBudget',
        security: [{ bearerAuth: [] }],
        requestBody: {
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/BudgetReallocationRequest' }
            }
          }
        },
        responses: {
          '200': {
            description: 'Budget reallocation result',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/BudgetReallocationResponse' }
              }
            }
          }
        }
      }
    },
    '/health': {
      get: {
        tags: ['Health'],
        summary: 'Health check',
        description: 'Returns system health status and component checks',
        operationId: 'healthCheck',
        responses: {
          '200': {
            description: 'System healthy',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/HealthResponse' }
              }
            }
          },
          '503': {
            description: 'System unhealthy',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/HealthResponse' }
              }
            }
          }
        }
      }
    },
    '/health/ready': {
      get: {
        tags: ['Health'],
        summary: 'Readiness check',
        description: 'Returns whether service is ready to accept traffic',
        operationId: 'readinessCheck',
        responses: {
          '200': { description: 'Service ready' },
          '503': { description: 'Service not ready' }
        }
      }
    },
    '/health/live': {
      get: {
        tags: ['Health'],
        summary: 'Liveness check',
        description: 'Returns whether service is alive',
        operationId: 'livenessCheck',
        responses: {
          '200': { description: 'Service alive' }
        }
      }
    },
    '/metrics': {
      get: {
        tags: ['Health'],
        summary: 'Prometheus metrics',
        description: 'Returns Prometheus-format metrics for monitoring',
        operationId: 'getMetrics',
        responses: {
          '200': {
            description: 'Metrics in Prometheus format',
            content: {
              'text/plain': {
                schema: { type: 'string' }
              }
            }
          }
        }
      }
    }
  }
};

const swaggerOptions = {
  swaggerDefinition,
  apis: ['./src/routes/*.ts', './src/index.ts']
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

export function setupSwagger(app: Express): void {
  // Serve swagger docs
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec, {
    customCss: '.swagger-ui .topbar { display: none }',
    customSiteTitle: 'GeminiVideo API Documentation'
  }));

  // Serve raw swagger JSON
  app.get('/api-docs.json', (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.send(swaggerSpec);
  });

  console.log('📚 Swagger documentation available at /api-docs');
}

export { swaggerSpec };
