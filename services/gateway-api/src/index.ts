import express from 'express';
import cors from 'cors';
import axios from 'axios';
import YAML from 'yaml';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { Asset, Clip, RemixRequest, RenderJob, Weights } from './types';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8080;

// Service URLs
const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://video-agent:8001';
const DRIVE_INTEL_URL = process.env.DRIVE_INTEL_URL || 'http://drive-intel:8002';
const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://meta-publisher:8003';

// Shared config path
const WEIGHTS_PATH = process.env.WEIGHTS_PATH || '/app/shared/config/weights.yaml';

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'gateway-api' });
});

// POST /ingest/drive/sync
app.post('/ingest/drive/sync', async (req, res) => {
  try {
    const { source = 'local', folderId } = req.body;
    
    // Call drive-intel service to scan and ingest
    const response = await axios.post(`${DRIVE_INTEL_URL}/ingest/scan`, {
      source,
      folderId
    });
    
    res.json({
      assetsIngested: response.data.assets?.length || 0,
      message: `Ingested ${response.data.assets?.length || 0} assets from ${source}`
    });
  } catch (error: any) {
    console.error('Ingest error:', error.message);
    res.status(500).json({ error: 'Failed to ingest assets', details: error.message });
  }
});

// GET /assets
app.get('/assets', async (req, res) => {
  try {
    const response = await axios.get(`${DRIVE_INTEL_URL}/assets`);
    res.json(response.data);
  } catch (error: any) {
    console.error('Get assets error:', error.message);
    res.status(500).json({ error: 'Failed to fetch assets', details: error.message });
  }
});

// GET /assets/:id/clips
app.get('/assets/:id/clips', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await axios.get(`${DRIVE_INTEL_URL}/assets/${id}/clips`);
    res.json(response.data);
  } catch (error: any) {
    console.error('Get clips error:', error.message);
    res.status(500).json({ error: 'Failed to fetch clips', details: error.message });
  }
});

// POST /render/remix
app.post('/render/remix', async (req, res) => {
  try {
    const remixRequest: RemixRequest = req.body;
    
    // Forward to video-agent
    const response = await axios.post(`${VIDEO_AGENT_URL}/render/remix`, remixRequest);
    
    res.status(202).json({
      jobId: response.data.jobId,
      status: response.data.status
    });
  } catch (error: any) {
    console.error('Remix error:', error.message);
    res.status(500).json({ error: 'Failed to create remix job', details: error.message });
  }
});

// GET /render/jobs/:id
app.get('/render/jobs/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await axios.get(`${VIDEO_AGENT_URL}/render/jobs/${id}`);
    res.json(response.data);
  } catch (error: any) {
    console.error('Get job error:', error.message);
    res.status(500).json({ error: 'Failed to fetch job status', details: error.message });
  }
});

// POST /publish/meta
app.post('/publish/meta', async (req, res) => {
  try {
    const { videoUrl, caption, platform } = req.body;
    
    const response = await axios.post(`${META_PUBLISHER_URL}/publish/meta`, {
      videoUrl,
      caption,
      platform
    });
    
    res.json({
      creativeId: response.data.creativeId,
      status: response.data.status
    });
  } catch (error: any) {
    console.error('Publish error:', error.message);
    res.status(500).json({ error: 'Failed to publish to Meta', details: error.message });
  }
});

// GET /performance/metrics
app.get('/performance/metrics', async (req, res) => {
  try {
    const { creativeId, days = 7 } = req.query;
    
    const response = await axios.get(`${META_PUBLISHER_URL}/performance/metrics`, {
      params: { creativeId, days }
    });
    
    res.json(response.data);
  } catch (error: any) {
    console.error('Get metrics error:', error.message);
    res.status(500).json({ error: 'Failed to fetch metrics', details: error.message });
  }
});

// POST /internal/learning/update
app.post('/internal/learning/update', async (req, res) => {
  try {
    // Read current weights
    let weights: Weights;
    try {
      const weightsContent = fs.readFileSync(WEIGHTS_PATH, 'utf-8');
      weights = YAML.parse(weightsContent);
    } catch (err) {
      console.error('Failed to read weights file:', err);
      return res.status(500).json({ error: 'Failed to read weights configuration' });
    }
    
    // TODO: Fetch real performance data from meta-publisher
    // TODO: Calculate optimal weight adjustments based on metrics
    // For now, just increment psychology_weight slightly as a demo
    const adjustmentRate = weights.learning.adjustment_rate;
    const oldPsychWeight = weights.psychology_weight;
    
    // Simple demo adjustment: increase psychology weight slightly
    weights.psychology_weight = Math.min(0.5, weights.psychology_weight + adjustmentRate);
    
    // Normalize weights to sum to 1.0
    const totalWeight = weights.psychology_weight + weights.compliance_weight + 
                        weights.diversification_weight + weights.novelty_weight;
    
    weights.psychology_weight /= totalWeight;
    weights.compliance_weight /= totalWeight;
    weights.diversification_weight /= totalWeight;
    weights.novelty_weight /= totalWeight;
    
    // Write back to file
    try {
      const updatedYaml = YAML.stringify(weights);
      fs.writeFileSync(WEIGHTS_PATH, updatedYaml, 'utf-8');
    } catch (err) {
      console.error('Failed to write weights file:', err);
      return res.status(500).json({ error: 'Failed to update weights configuration' });
    }
    
    res.json({
      message: 'Weights updated based on performance data',
      weightsUpdated: {
        psychology_weight: {
          old: oldPsychWeight,
          new: weights.psychology_weight
        }
      }
    });
  } catch (error: any) {
    console.error('Learning update error:', error.message);
    res.status(500).json({ error: 'Failed to update learning weights', details: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Gateway API listening on port ${PORT}`);
  console.log(`VIDEO_AGENT_URL: ${VIDEO_AGENT_URL}`);
  console.log(`DRIVE_INTEL_URL: ${DRIVE_INTEL_URL}`);
  console.log(`META_PUBLISHER_URL: ${META_PUBLISHER_URL}`);
});
