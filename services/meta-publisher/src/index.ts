import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8003;

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'meta-publisher' });
});

// POST /publish/meta - Publish video to Meta platforms
app.post('/publish/meta', async (req, res) => {
  try {
    const { videoUrl, caption, platform } = req.body;
    
    // TODO: Implement real Meta Marketing API integration
    // For now, return a placeholder creative ID
    const creativeId = `meta_creative_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    console.log(`Publishing to Meta ${platform}:`, {
      videoUrl,
      caption: caption?.substring(0, 50),
      creativeId
    });
    
    res.json({
      creativeId,
      status: 'published',
      platform,
      message: 'Video published successfully (stub)'
    });
  } catch (error: any) {
    console.error('Publish error:', error.message);
    res.status(500).json({ error: 'Failed to publish', details: error.message });
  }
});

// GET /performance/metrics - Get performance metrics
app.get('/performance/metrics', async (req, res) => {
  try {
    const { creativeId, days = 7 } = req.query;
    
    // TODO: Implement real Meta Marketing API metrics fetching
    // For now, return static placeholder metrics
    const metrics = generatePlaceholderMetrics(creativeId as string, Number(days));
    
    res.json(metrics);
  } catch (error: any) {
    console.error('Get metrics error:', error.message);
    res.status(500).json({ error: 'Failed to fetch metrics', details: error.message });
  }
});

// POST /internal/metrics/ingest - Ingest metrics from Meta
app.post('/internal/metrics/ingest', async (req, res) => {
  try {
    // TODO: Implement periodic metrics fetching and storage
    // This would be called by a scheduled job to pull latest metrics
    
    res.json({
      message: 'Metrics ingestion stub',
      ingested: 0
    });
  } catch (error: any) {
    console.error('Ingest metrics error:', error.message);
    res.status(500).json({ error: 'Failed to ingest metrics', details: error.message });
  }
});

function generatePlaceholderMetrics(creativeId: string | undefined, days: number) {
  // Generate placeholder metrics for testing
  const metrics = [];
  const now = new Date();
  
  for (let i = 0; i < days; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    const impressions = Math.floor(Math.random() * 10000) + 1000;
    const clicks = Math.floor(impressions * (Math.random() * 0.05 + 0.01)); // 1-6% CTR
    const conversions = Math.floor(clicks * (Math.random() * 0.1 + 0.02)); // 2-12% CVR
    const spend = Math.floor(Math.random() * 500) + 100;
    
    metrics.push({
      creativeId: creativeId || 'all',
      date: date.toISOString().split('T')[0],
      impressions,
      clicks,
      conversions,
      ctr: (clicks / impressions * 100).toFixed(2),
      cvr: (conversions / clicks * 100).toFixed(2),
      cpc: (spend / clicks).toFixed(2),
      cpa: (spend / conversions).toFixed(2),
      spend: spend.toFixed(2)
    });
  }
  
  return metrics.reverse(); // Most recent first
}

app.listen(PORT, () => {
  console.log(`Meta Publisher API listening on port ${PORT}`);
});
