/**
 * Gateway API - Main entry point
 */
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { config } from './config';
import { logger } from './logger';
import { assetsRouter } from './routes/assets';
import { renderRouter } from './routes/render';
import { predictRouter } from './routes/predict';
import { learningRouter } from './routes/learning';

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
  res.json({ status: 'healthy', service: 'gateway-api' });
});

// Routes
app.use('/assets', assetsRouter);
app.use('/render', renderRouter);
app.use('/predict', predictRouter);
app.use('/internal/learning', learningRouter);

// Error handling
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error(`Error: ${err.message}`, { error: err });
  res.status(500).json({ error: err.message });
});

// Start server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  logger.info(`Gateway API listening on port ${PORT}`);
});

export default app;
