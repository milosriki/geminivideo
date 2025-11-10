/**
 * Meta API Service
 */
import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';
import { config } from '../config';
import { logger } from '../logger';

interface PublishAdRequest {
  videoUrl?: string;
  fileHash?: string;
  placements: string[];
  campaign?: string;
  adSetId?: string;
  pageId: string;
}

interface PublishAdResponse {
  creativeId: string;
  adId: string;
  dryRun: boolean;
}

export class MetaService {
  private baseUrl = 'https://graph.facebook.com/v18.0';

  private get isDryRun(): boolean {
    return config.dryRun || !config.metaAccessToken;
  }

  async publishAd(request: PublishAdRequest): Promise<PublishAdResponse> {
    if (this.isDryRun) {
      // Dry run mode - return stubbed IDs
      logger.info('Dry run: Would publish ad', { request });
      return {
        creativeId: `creative_${Date.now()}`,
        adId: `ad_${Date.now()}`,
        dryRun: true
      };
    }

    try {
      // Step 1: Upload/reference video
      let videoId: string;
      if (request.videoUrl) {
        videoId = await this.uploadVideoFromUrl(request.videoUrl, request.pageId);
      } else if (request.fileHash) {
        videoId = request.fileHash;
      } else {
        throw new Error('No video source provided');
      }

      // Step 2: Create ad creative
      const creativeId = await this.createAdCreative(videoId, request.pageId);

      // Step 3: Create ad
      const adId = await this.createAd(creativeId, request.adSetId);

      return {
        creativeId,
        adId,
        dryRun: false
      };
    } catch (error: any) {
      logger.error('Meta API error', { error: error.message });
      throw error;
    }
  }

  async uploadVideo(videoPath: string): Promise<any> {
    if (this.isDryRun) {
      logger.info('Dry run: Would upload video', { videoPath });
      return {
        videoId: `video_${Date.now()}`,
        dryRun: true
      };
    }

    // Validate videoPath to prevent path traversal
    const path = require('path');
    const normalizedPath = path.normalize(videoPath);
    if (normalizedPath.includes('..') || !normalizedPath.startsWith('/app/data/outputs')) {
      throw new Error('Invalid video path');
    }

    try {
      const formData = new FormData();
      formData.append('source', fs.createReadStream(normalizedPath));
      formData.append('access_token', config.metaAccessToken);

      const response = await axios.post(
        `${this.baseUrl}/${config.metaAdAccountId}/advideos`,
        formData,
        {
          headers: formData.getHeaders(),
          maxContentLength: Infinity,
          maxBodyLength: Infinity
        }
      );

      return {
        videoId: response.data.id,
        dryRun: false
      };
    } catch (error: any) {
      logger.error('Video upload failed', { error: error.message });
      throw error;
    }
  }

  private async uploadVideoFromUrl(videoUrl: string, pageId: string): Promise<string> {
    try {
      // Validate pageId to prevent URL injection
      if (!/^[0-9]+$/.test(pageId)) {
        throw new Error('Invalid page ID format');
      }

      // Validate video URL scheme
      const url = new URL(videoUrl);
      if (!['http:', 'https:'].includes(url.protocol)) {
        throw new Error('Invalid video URL protocol');
      }

      const response = await axios.post(
        `${this.baseUrl}/${pageId}/videos`,
        {
          file_url: videoUrl,
          access_token: config.metaAccessToken
        }
      );

      return response.data.id;
    } catch (error: any) {
      logger.error('Video URL upload failed', { error: error.message });
      throw error;
    }
  }

  private async createAdCreative(videoId: string, pageId: string): Promise<string> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/${config.metaAdAccountId}/adcreatives`,
        {
          name: `Creative ${Date.now()}`,
          object_story_spec: {
            page_id: pageId,
            video_data: {
              video_id: videoId,
              call_to_action: {
                type: 'LEARN_MORE'
              }
            }
          },
          access_token: config.metaAccessToken
        }
      );

      return response.data.id;
    } catch (error: any) {
      logger.error('Creative creation failed', { error: error.message });
      throw error;
    }
  }

  private async createAd(creativeId: string, adSetId?: string): Promise<string> {
    if (!adSetId) {
      throw new Error('adSetId required for ad creation');
    }

    try {
      const response = await axios.post(
        `${this.baseUrl}/${config.metaAdAccountId}/ads`,
        {
          name: `Ad ${Date.now()}`,
          adset_id: adSetId,
          creative: { creative_id: creativeId },
          status: 'PAUSED',
          access_token: config.metaAccessToken
        }
      );

      return response.data.id;
    } catch (error: any) {
      logger.error('Ad creation failed', { error: error.message });
      throw error;
    }
  }

  async getInsights(adId: string, datePreset: string): Promise<any> {
    if (this.isDryRun) {
      logger.info('Dry run: Would fetch insights', { adId, datePreset });
      return {
        data: [{
          impressions: 1000,
          clicks: 50,
          spend: '10.50',
          ctr: 0.05,
          cpc: '0.21'
        }],
        dryRun: true
      };
    }

    // Validate adId to prevent URL injection
    if (!/^[0-9]+$/.test(adId)) {
      throw new Error('Invalid ad ID format');
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${adId}/insights`,
        {
          params: {
            fields: 'impressions,clicks,spend,ctr,cpc,reach,frequency',
            date_preset: datePreset,
            access_token: config.metaAccessToken
          }
        }
      );

      return {
        data: response.data.data,
        dryRun: false
      };
    } catch (error: any) {
      logger.error('Insights fetch failed', { error: error.message });
      throw error;
    }
  }
}
