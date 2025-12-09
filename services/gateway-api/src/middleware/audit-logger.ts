import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';

interface AuditLogEntry {
  action: string;
  resource: string;
  resource_id?: string;
  user_id?: string;
  ip_address: string;
  user_agent: string;
  request_body?: any;
  response_status: number;
  duration_ms: number;
}

let pgPool: Pool;

export function initializeAuditLogger(pool: Pool) {
  pgPool = pool;
}

export async function logAuditEvent(entry: AuditLogEntry): Promise<void> {
  if (!pgPool) {
    console.warn('Audit logger not initialized');
    return;
  }

  try {
    await pgPool.query(
      `INSERT INTO audit_log (action, resource, resource_id, user_id, ip_address, user_agent, request_body, response_status, duration_ms, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())`,
      [
        entry.action,
        entry.resource,
        entry.resource_id,
        entry.user_id,
        entry.ip_address,
        entry.user_agent,
        JSON.stringify(entry.request_body),
        entry.response_status,
        entry.duration_ms
      ]
    );
  } catch (error) {
    console.error('Failed to log audit event:', error);
  }
}

export function auditLogger(options: { resources?: string[] } = {}) {
  return (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const originalSend = res.send;

    res.send = function(body: any) {
      const duration = Date.now() - startTime;

      // Determine action from method
      const actionMap: { [key: string]: string } = {
        GET: 'READ',
        POST: 'CREATE',
        PUT: 'UPDATE',
        PATCH: 'UPDATE',
        DELETE: 'DELETE'
      };

      const action = actionMap[req.method] || req.method;
      const resource = req.baseUrl.replace('/api/', '').split('/')[0];
      const resourceId = req.params.id || req.params.campaignId || req.params.adId;

      // Log audit event
      logAuditEvent({
        action,
        resource,
        resource_id: resourceId,
        user_id: (req as any).user?.id,
        ip_address: req.ip || req.connection.remoteAddress || 'unknown',
        user_agent: req.headers['user-agent'] || 'unknown',
        request_body: ['POST', 'PUT', 'PATCH'].includes(req.method) ? req.body : undefined,
        response_status: res.statusCode,
        duration_ms: duration
      });

      return originalSend.call(this, body);
    };

    next();
  };
}

export default auditLogger;
