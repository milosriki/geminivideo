/**
 * Meta Publisher Service - Main entry point
 */
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { config } from './config';
import { logger } from './logger';
import { publishRouter } from './routes/publish';
import { insightsRouter } from './routes/insights';

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Request logging
app.use((req: Request, res: Response, next: NextFunction) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({ 
    status: 'healthy', 
    service: 'meta-publisher',
    dryRun: config.dryRun
  });
});

// Routes
app.use('/publish', publishRouter);
app.use('/insights', insightsRouter);

// Error handling
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error(`Error: ${err.message}`, { error: err });
  res.status(500).json({ error: err.message });
});

// Start server
const PORT = process.env.PORT || 8003;
app.listen(PORT, () => {
  logger.info(`Meta Publisher listening on port ${PORT}`);
  if (config.dryRun) {
    logger.warn('Running in DRY-RUN mode - no actual Meta API calls will be made');
  }
});

export default app;
