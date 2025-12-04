import { Express } from 'express';
import analyticsRouter from './analytics';
import campaignsRouter from './campaigns';
import councilRouter from './council';
import contentRouter from './content';
import downloadsRouter from './downloads';

export function registerRoutes(app: Express): void {
  // Analytics endpoints
  app.use(analyticsRouter);

  // Campaign management
  app.use(campaignsRouter);

  // Council of Titans evaluation
  app.use(councilRouter);

  // Content: avatars, trending, insights
  app.use(contentRouter);

  // Download endpoints
  app.use(downloadsRouter);

  console.log('✅ All new routes registered');
}

export {
  analyticsRouter,
  campaignsRouter,
  councilRouter,
  contentRouter,
  downloadsRouter
};
