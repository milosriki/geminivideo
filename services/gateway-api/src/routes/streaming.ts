/**
 * Streaming Routes
 * SSE endpoints for real-time AI streaming and updates
 */

import { Router, Request, Response } from 'express';
import { getSSEManager } from '../realtime/sse-manager';
import { CouncilScoreStreamEvent, createAIStreamChunk } from '../realtime/events';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { httpClient } from "../index";

const router = Router();

// ============================================================================
// STREAMING AI COUNCIL EVALUATION
// ============================================================================

/**
 * Stream AI Council evaluation in real-time
 * Shows each model's thinking process as it happens
 */
router.get('/stream/council-score', async (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const client = sseManager.initializeConnection(res, req.query.userId as string);

  try {
    const { videoUrl, transcript, features } = req.query;

    if (!videoUrl || !transcript) {
      sseManager.sendError(client, 'Missing required parameters: videoUrl, transcript');
      return;
    }

    // Parse features if provided
    let featureData: any = {};
    if (features && typeof features === 'string') {
      try {
        featureData = JSON.parse(features);
      } catch (e) {
        featureData = {};
      }
    }

    const prompt = `Evaluate this video for viral potential:
Transcript: ${transcript}
Features: ${JSON.stringify(featureData)}

Score on:
1. Psychology triggers (curiosity, urgency, social proof)
2. Hook strength (0-1)
3. Novelty and uniqueness

Provide reasoning and final composite score.`;

    // Stream from each AI model sequentially
    const models = ['gemini', 'claude', 'gpt4', 'perplexity'];
    const scores: any[] = [];

    for (const model of models) {
      // Send stage update
      sseManager.sendEvent(client, {
        type: 'council_score_stream',
        stage: model as any,
        model,
        thinking: '',
        isComplete: false,
        timestamp: new Date().toISOString()
      } as CouncilScoreStreamEvent);

      try {
        // Stream AI response
        const response = await streamAIModel(model, prompt);

        let fullResponse = '';
        for await (const chunk of response) {
          fullResponse += chunk;

          sseManager.sendEvent(client, {
            type: 'council_score_stream',
            stage: model as any,
            model,
            thinking: chunk,
            isComplete: false,
            timestamp: new Date().toISOString()
          } as CouncilScoreStreamEvent);

          // Small delay to make streaming visible
          await new Promise(resolve => setTimeout(resolve, 50));
        }

        // Parse score from response (simplified)
        const score = extractScoreFromResponse(fullResponse);
        scores.push({ model, score, reasoning: fullResponse.slice(0, 500) });

        sseManager.sendEvent(client, {
          type: 'council_score_stream',
          stage: model as any,
          model,
          score,
          reasoning: fullResponse.slice(0, 500),
          isComplete: true,
          timestamp: new Date().toISOString()
        } as CouncilScoreStreamEvent);

      } catch (error: any) {
        console.error(`Error streaming from ${model}:`, error);
        sseManager.sendEvent(client, {
          type: 'council_score_stream',
          stage: model as any,
          model,
          thinking: `Error: ${error.message}`,
          isComplete: true,
          timestamp: new Date().toISOString()
        } as CouncilScoreStreamEvent);
      }
    }

    // Send aggregation stage
    sseManager.sendEvent(client, {
      type: 'council_score_stream',
      stage: 'aggregating',
      thinking: 'Aggregating scores from all models...',
      isComplete: false,
      timestamp: new Date().toISOString()
    } as CouncilScoreStreamEvent);

    // Calculate final composite score
    const compositeScore = scores.reduce((sum, s) => sum + s.score, 0) / scores.length;

    // Send final result
    sseManager.sendEvent(client, {
      type: 'council_score_stream',
      stage: 'complete',
      isComplete: true,
      finalScore: {
        composite: compositeScore,
        psychology: { composite: compositeScore * 0.8 },
        hookStrength: { strength: compositeScore * 0.75 },
        novelty: { composite: compositeScore * 0.85 }
      },
      timestamp: new Date().toISOString()
    } as CouncilScoreStreamEvent);

    // Complete the stream
    sseManager.sendComplete(client, { scores, compositeScore });

  } catch (error: any) {
    console.error('Council score streaming error:', error);
    sseManager.sendError(client, error.message);
  }
});

/**
 * Stream AI creative evaluation
 */
router.get('/stream/evaluate-creative', async (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const client = sseManager.initializeConnection(res, req.query.userId as string);

  try {
    const { creativeId, content, type } = req.query;

    if (!content) {
      sseManager.sendError(client, 'Missing required parameter: content');
      return;
    }

    const prompt = `Evaluate this ${type || 'creative'} for marketing effectiveness:
${content}

Analyze:
1. Messaging clarity and impact
2. Call-to-action strength
3. Target audience alignment
4. Emotional resonance
5. Predicted performance`;

    // Stream from primary AI model
    const model = 'gemini';
    const response = await streamAIModel(model, prompt);

    for await (const chunk of response) {
      sseManager.sendChunk(client, chunk);
      await new Promise(resolve => setTimeout(resolve, 30));
    }

    sseManager.sendComplete(client);

  } catch (error: any) {
    console.error('Creative evaluation streaming error:', error);
    sseManager.sendError(client, error.message);
  }
});

/**
 * Stream video render progress frame-by-frame
 */
router.get('/stream/render-progress/:jobId', async (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const client = sseManager.initializeConnection(res, req.query.userId as string);

  const { jobId } = req.params;

  try {
    // Subscribe to job progress channel (would integrate with actual render system)
    // For now, simulate progress
    sseManager.sendEvent(client, {
      type: 'video_render_progress',
      jobId,
      currentFrame: 0,
      totalFrames: 1000,
      progress: 0,
      fps: 30,
      estimatedTimeRemaining: 60,
      stage: 'preparing',
      timestamp: new Date().toISOString()
    } as any);

    // In production, this would subscribe to Redis channel for actual progress
    // For demo, simulate progress
    let frame = 0;
    const totalFrames = 1000;
    const stages = ['preparing', 'rendering', 'encoding', 'uploading', 'complete'];
    let stageIndex = 0;

    const progressInterval = setInterval(() => {
      frame += 50;
      const progress = frame / totalFrames;

      if (progress >= 0.25 && stageIndex === 0) stageIndex = 1;
      if (progress >= 0.70 && stageIndex === 1) stageIndex = 2;
      if (progress >= 0.85 && stageIndex === 2) stageIndex = 3;
      if (progress >= 0.95 && stageIndex === 3) stageIndex = 4;

      sseManager.sendEvent(client, {
        type: 'video_render_progress',
        jobId,
        currentFrame: frame,
        totalFrames,
        progress: Math.min(progress, 1),
        fps: 30,
        estimatedTimeRemaining: Math.max(0, (totalFrames - frame) / 30),
        stage: stages[stageIndex],
        timestamp: new Date().toISOString()
      } as any);

      if (frame >= totalFrames) {
        clearInterval(progressInterval);
        sseManager.sendComplete(client, { jobId, status: 'completed' });
      }
    }, 500);

    // Clean up on disconnect
    res.on('close', () => {
      clearInterval(progressInterval);
    });

  } catch (error: any) {
    console.error('Render progress streaming error:', error);
    sseManager.sendError(client, error.message);
  }
});

/**
 * Stream live campaign metrics
 */
router.get('/stream/campaign-metrics/:campaignId', async (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const client = sseManager.initializeConnection(res, req.query.userId as string);

  const { campaignId } = req.params;

  try {
    // In production, subscribe to campaign metrics channel
    // For demo, send periodic updates
    let updateCount = 0;
    const maxUpdates = 20;

    const metricsInterval = setInterval(() => {
      updateCount++;

      sseManager.sendEvent(client, {
        type: 'campaign_metrics',
        campaignId,
        metrics: {
          impressions: 10000 + updateCount * 500,
          clicks: 500 + updateCount * 25,
          ctr: 0.05 + (updateCount * 0.001),
          spend: 1000 + updateCount * 50,
          conversions: 50 + updateCount * 3,
          roas: 3.5 + (updateCount * 0.1)
        },
        change: {
          impressions: 500,
          clicks: 25,
          ctr: 0.001,
          spend: 50
        },
        timestamp: new Date().toISOString()
      } as any);

      if (updateCount >= maxUpdates) {
        clearInterval(metricsInterval);
        sseManager.sendComplete(client);
      }
    }, 2000);

    // Clean up on disconnect
    res.on('close', () => {
      clearInterval(metricsInterval);
    });

  } catch (error: any) {
    console.error('Campaign metrics streaming error:', error);
    sseManager.sendError(client, error.message);
  }
});

/**
 * Stream A/B test results as they update
 */
router.get('/stream/ab-test-results/:testId', async (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const client = sseManager.initializeConnection(res, req.query.userId as string);

  const { testId } = req.params;

  try {
    // In production, subscribe to A/B test results channel
    // For demo, simulate real-time test results
    const variants = ['A', 'B', 'C'];
    let updateCount = 0;
    const maxUpdates = 15;

    const testInterval = setInterval(() => {
      updateCount++;

      for (const variantId of variants) {
        const baseMetrics = {
          A: { impressions: 5000, clicks: 250, conversions: 25 },
          B: { impressions: 5000, clicks: 300, conversions: 35 },
          C: { impressions: 5000, clicks: 275, conversions: 28 }
        }[variantId] || { impressions: 5000, clicks: 250, conversions: 25 };

        sseManager.sendEvent(client, {
          type: 'ab_test_result',
          testId,
          variantId,
          metrics: {
            impressions: baseMetrics.impressions + updateCount * 100,
            clicks: baseMetrics.clicks + updateCount * 5,
            ctr: (baseMetrics.clicks + updateCount * 5) / (baseMetrics.impressions + updateCount * 100),
            conversions: baseMetrics.conversions + updateCount * 2,
            confidence: Math.min(0.95, 0.5 + (updateCount * 0.03))
          },
          isWinner: variantId === 'B' && updateCount > 10,
          statisticalSignificance: Math.min(0.95, 0.5 + (updateCount * 0.03)),
          timestamp: new Date().toISOString()
        } as any);
      }

      if (updateCount >= maxUpdates) {
        clearInterval(testInterval);
        sseManager.sendComplete(client, { winner: 'B' });
      }
    }, 2000);

    // Clean up on disconnect
    res.on('close', () => {
      clearInterval(testInterval);
    });

  } catch (error: any) {
    console.error('A/B test streaming error:', error);
    sseManager.sendError(client, error.message);
  }
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Stream from AI model (simulated for demo)
 */
async function* streamAIModel(model: string, prompt: string): AsyncGenerator<string> {
  // In production, integrate with actual AI APIs

  if (model === 'gemini' && process.env.GEMINI_API_KEY) {
    try {
      const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
      const geminiModel = genAI.getGenerativeModel({ model: 'gemini-pro' });
      const result = await geminiModel.generateContentStream(prompt);

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          yield text;
        }
      }
      return;
    } catch (error) {
      console.error('Gemini streaming error:', error);
    }
  }

  // Fallback: Simulate streaming for demo
  const responses = {
    gemini: `Analyzing video... This content shows strong curiosity triggers with an incomplete narrative hook. The surprise element is moderate. Overall psychology score: 0.78. Hook strength: 0.82 (curiosity gap type). Novelty: 0.75 (good uniqueness). Final composite: 0.79`,
    claude: `Evaluating creative elements... The hook utilizes social proof effectively with testimonial-style framing. Urgency markers are present but subtle. Psychology composite: 0.82. Hook effectiveness: 0.85 (social proof + urgency). Novelty assessment: 0.72. Composite score: 0.80`,
    gpt4: `Assessment in progress... Strong pattern interrupt detected in opening. Emotional story arc well-developed. Psychology score: 0.76. Hook strength: 0.79 (emotional story). Novelty: 0.80 (unique angle). Overall: 0.78`,
    perplexity: `Cross-referencing with viral patterns... Content aligns with current trending formats. Good empathy triggers. Psychology: 0.81. Hook: 0.76 (pattern interrupt). Novelty: 0.77. Final: 0.79`
  };

  const response = responses[model as keyof typeof responses] || responses.gemini;
  const words = response.split(' ');

  for (const word of words) {
    yield word + ' ';
    await new Promise(resolve => setTimeout(resolve, 50));
  }
}

/**
 * Extract score from AI response (simplified)
 */
function extractScoreFromResponse(response: string): number {
  // Look for patterns like "score: 0.78" or "0.78"
  const matches = response.match(/(?:score|composite)[:\s]+(\d+\.?\d*)/i);
  if (matches && matches[1]) {
    return parseFloat(matches[1]);
  }

  // Look for decimal numbers
  const numbers = response.match(/0\.\d+/g);
  if (numbers && numbers.length > 0) {
    return parseFloat(numbers[numbers.length - 1]);
  }

  // Default
  return 0.75;
}

export default router;
