/**
 * Emotion Recognition Service
 * Uses Gemini Vision API for facial emotion analysis in video frames
 *
 * Emotions detected: joy, surprise, anger, sadness, fear, disgust, neutral
 * Use cases:
 * - Analyze viewer emotional response to ads
 * - Optimize hook moments based on emotional peaks
 * - A/B test creatives by emotional impact score
 */

import { GoogleGenerativeAI } from '@google/generative-ai';

// Emotion categories with marketing relevance scores
export interface EmotionResult {
  timestamp: number;
  emotions: {
    joy: number;
    surprise: number;
    anger: number;
    sadness: number;
    fear: number;
    disgust: number;
    neutral: number;
  };
  dominantEmotion: string;
  confidence: number;
  marketingScore: number; // 0-100, higher = better for engagement
}

export interface VideoEmotionAnalysis {
  videoId: string;
  duration: number;
  frameCount: number;
  emotionTimeline: EmotionResult[];
  summary: {
    averageMarketingScore: number;
    emotionalPeaks: { timestamp: number; emotion: string; intensity: number }[];
    recommendedHookMoments: number[];
    emotionalArc: 'rising' | 'falling' | 'peak-valley' | 'steady';
  };
}

export class EmotionRecognitionService {
  private genAI: GoogleGenerativeAI;
  private model: string = 'gemini-2.0-flash-exp';

  constructor(apiKey?: string) {
    const key = apiKey || process.env.GEMINI_API_KEY || process.env.GOOGLE_AI_API_KEY;
    if (!key) {
      throw new Error('Gemini API key required for emotion recognition');
    }
    this.genAI = new GoogleGenerativeAI(key);
  }

  /**
   * Analyze emotions in a single video frame
   */
  async analyzeFrame(
    imageBase64: string,
    timestamp: number
  ): Promise<EmotionResult> {
    const model = this.genAI.getGenerativeModel({ model: this.model });

    const prompt = `Analyze the facial expressions and emotions in this image.

Return a JSON object with these exact fields:
{
  "emotions": {
    "joy": 0.0-1.0,
    "surprise": 0.0-1.0,
    "anger": 0.0-1.0,
    "sadness": 0.0-1.0,
    "fear": 0.0-1.0,
    "disgust": 0.0-1.0,
    "neutral": 0.0-1.0
  },
  "dominantEmotion": "string",
  "confidence": 0.0-1.0
}

If no faces are detected, return neutral with low confidence.
Only return valid JSON, no other text.`;

    try {
      const result = await model.generateContent([
        prompt,
        {
          inlineData: {
            mimeType: 'image/jpeg',
            data: imageBase64,
          },
        },
      ]);

      const responseText = result.response.text();
      const parsed = JSON.parse(responseText.replace(/```json\n?|\n?```/g, ''));

      // Calculate marketing score (joy + surprise are best for ads)
      const marketingScore = Math.round(
        (parsed.emotions.joy * 40 +
          parsed.emotions.surprise * 30 +
          (1 - parsed.emotions.anger) * 10 +
          (1 - parsed.emotions.sadness) * 10 +
          (1 - parsed.emotions.fear) * 5 +
          (1 - parsed.emotions.disgust) * 5)
      );

      return {
        timestamp,
        emotions: parsed.emotions,
        dominantEmotion: parsed.dominantEmotion,
        confidence: parsed.confidence,
        marketingScore: Math.min(100, Math.max(0, marketingScore)),
      };
    } catch (error) {
      console.error('Emotion analysis failed:', error);
      return {
        timestamp,
        emotions: {
          joy: 0,
          surprise: 0,
          anger: 0,
          sadness: 0,
          fear: 0,
          disgust: 0,
          neutral: 1,
        },
        dominantEmotion: 'neutral',
        confidence: 0,
        marketingScore: 50,
      };
    }
  }

  /**
   * Analyze emotions across video frames
   * Samples frames at specified interval for efficiency
   */
  async analyzeVideo(
    frames: { base64: string; timestamp: number }[],
    options: { sampleRate?: number } = {}
  ): Promise<VideoEmotionAnalysis> {
    const { sampleRate = 1 } = options; // Analyze every Nth frame

    const sampled = frames.filter((_, i) => i % sampleRate === 0);
    const emotionTimeline: EmotionResult[] = [];

    // Process frames in parallel batches of 5
    const batchSize = 5;
    for (let i = 0; i < sampled.length; i += batchSize) {
      const batch = sampled.slice(i, i + batchSize);
      const results = await Promise.all(
        batch.map((frame) => this.analyzeFrame(frame.base64, frame.timestamp))
      );
      emotionTimeline.push(...results);
    }

    // Calculate summary statistics
    const avgScore =
      emotionTimeline.reduce((sum, e) => sum + e.marketingScore, 0) /
      emotionTimeline.length;

    // Find emotional peaks (moments of high intensity)
    const peaks = emotionTimeline
      .filter((e) => e.confidence > 0.7 && e.dominantEmotion !== 'neutral')
      .sort((a, b) => {
        const intensityA = Math.max(...Object.values(a.emotions));
        const intensityB = Math.max(...Object.values(b.emotions));
        return intensityB - intensityA;
      })
      .slice(0, 5)
      .map((e) => ({
        timestamp: e.timestamp,
        emotion: e.dominantEmotion,
        intensity: Math.max(...Object.values(e.emotions)),
      }));

    // Find best hook moments (high joy/surprise, good for ad starts)
    const hookMoments = emotionTimeline
      .filter(
        (e) =>
          e.emotions.joy > 0.6 || e.emotions.surprise > 0.6
      )
      .map((e) => e.timestamp)
      .slice(0, 3);

    // Determine emotional arc
    const firstHalf = emotionTimeline.slice(0, emotionTimeline.length / 2);
    const secondHalf = emotionTimeline.slice(emotionTimeline.length / 2);
    const firstAvg =
      firstHalf.reduce((s, e) => s + e.marketingScore, 0) / firstHalf.length;
    const secondAvg =
      secondHalf.reduce((s, e) => s + e.marketingScore, 0) / secondHalf.length;

    let emotionalArc: 'rising' | 'falling' | 'peak-valley' | 'steady';
    const diff = secondAvg - firstAvg;
    if (Math.abs(diff) < 5) emotionalArc = 'steady';
    else if (diff > 10) emotionalArc = 'rising';
    else if (diff < -10) emotionalArc = 'falling';
    else emotionalArc = 'peak-valley';

    return {
      videoId: `video_${Date.now()}`,
      duration: frames[frames.length - 1]?.timestamp || 0,
      frameCount: frames.length,
      emotionTimeline,
      summary: {
        averageMarketingScore: Math.round(avgScore),
        emotionalPeaks: peaks,
        recommendedHookMoments: hookMoments,
        emotionalArc,
      },
    };
  }

  /**
   * Get emotion-based creative recommendations
   */
  getCreativeRecommendations(analysis: VideoEmotionAnalysis): string[] {
    const recommendations: string[] = [];
    const { summary } = analysis;

    if (summary.averageMarketingScore < 50) {
      recommendations.push(
        'Consider adding more energetic/joyful moments to increase engagement'
      );
    }

    if (summary.emotionalArc === 'falling') {
      recommendations.push(
        'Emotional intensity drops toward the end - consider a stronger CTA moment'
      );
    }

    if (summary.recommendedHookMoments.length === 0) {
      recommendations.push(
        'No strong emotional hooks detected - add a surprising or joyful opening'
      );
    }

    if (summary.emotionalPeaks.some((p) => p.emotion === 'anger')) {
      recommendations.push(
        'Anger detected in some frames - review for potential negative associations'
      );
    }

    if (summary.averageMarketingScore > 70) {
      recommendations.push(
        'Strong emotional content - good candidate for broad audience targeting'
      );
    }

    return recommendations;
  }
}

export default EmotionRecognitionService;
