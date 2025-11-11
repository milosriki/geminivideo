import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import knowledgeRouter from './knowledge';

dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'gateway-api',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Knowledge router
app.use('/knowledge', knowledgeRouter);

// Example scoring endpoint
app.post('/score/clip', (req: Request, res: Response) => {
  const { clip_id, features } = req.body;
  
  // Placeholder response
  res.json({
    clip_id,
    scores: {
      psychology: { composite: 0.75 },
      hook_strength: { strength: 0.80 },
      novelty: { composite: 0.70 },
      composite: 0.75
    },
    predicted_band: 'high',
    predicted_ctr: 0.05
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Gateway API listening on port ${PORT}`);
});

export default app;
