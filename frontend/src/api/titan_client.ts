import { API_BASE_URL } from '../config/api';

export interface VideoAnalysis {
    hook_style: string;
    pacing: string;
    emotional_trigger: string;
    visual_elements: string[];
    reasoning: string;
}

export interface CampaignRequest {
    assets: string[];
    target_audience: string;
}

export const titanClient = {
    /**
     * Analyzes a video to extract the winning pattern.
     */
    analyzeVideo: async (videoUri: string): Promise<VideoAnalysis> => {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: videoUri, filename: 'upload.mp4' }), // Match gateway-api expectations
        });

        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Generates a new campaign based on provided assets and AI direction.
     */
    generateCampaign: async (request: CampaignRequest): Promise<any> => {
        // Placeholder for the generate endpoint which would use VeoDirector
        const response = await fetch(`${API_BASE_URL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Generation failed: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Retrieves dashboard metrics from the Cortex Data Engine.
     */
    getDashboardMetrics: async (days: number = 30): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/api/metrics?days=${days}`, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch metrics: ${response.statusText}`);
        }

        return response.json();
    }
};
