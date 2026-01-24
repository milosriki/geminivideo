/**
 * Real-time Streaming Example Component
 * Demonstrates SSE and WebSocket usage
 */

import React, { useState } from 'react';
import {
  useCouncilScoreStream,
  useRenderProgressStream,
  useCampaignMetricsStream
} from '../hooks/useSSE';
import { useRealtimeAlerts, useLiveMetrics } from '../hooks/useWebSocket';

export const CouncilScoreStreamExample: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [transcript, setTranscript] = useState('');

  const {
    stages,
    currentStage,
    finalScore,
    isConnected,
    isLoading,
    error,
    startStreaming,
    stopStreaming
  } = useCouncilScoreStream(
    videoUrl || null,
    transcript || null
  );

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">AI Council Score Stream</h2>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-2">Video URL</label>
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            placeholder="https://example.com/video.mp4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Transcript</label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            rows={3}
            placeholder="Video transcript..."
          />
        </div>

        <button
          onClick={startStreaming}
          disabled={!videoUrl || !transcript || isConnected}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Start Evaluation
        </button>

        {isConnected && (
          <button
            onClick={stopStreaming}
            className="ml-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Stop
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded mb-4">
          <p className="text-red-800">Error: {error.message}</p>
        </div>
      )}

      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Connecting...</p>
        </div>
      )}

      {currentStage && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Current Stage: {currentStage}</h3>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {['gemini', 'claude', 'gpt4', 'perplexity'].map(model => (
          <div
            key={model}
            className={`p-4 border rounded ${
              stages[model]?.isComplete ? 'bg-green-50 border-green-200' : 'bg-gray-50'
            }`}
          >
            <h4 className="font-semibold text-lg mb-2 capitalize">{model}</h4>

            {stages[model] ? (
              <>
                <div className="text-sm text-gray-600 mb-2">
                  {stages[model].thinking && (
                    <p className="whitespace-pre-wrap">{stages[model].thinking}</p>
                  )}
                </div>

                {stages[model].score !== undefined && (
                  <div className="mt-2">
                    <span className="font-medium">Score: </span>
                    <span className="text-lg text-blue-600">
                      {(stages[model].score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}

                {stages[model].isComplete && (
                  <div className="mt-2 text-green-600 font-medium">✓ Complete</div>
                )}
              </>
            ) : (
              <p className="text-gray-400">Waiting...</p>
            )}
          </div>
        ))}
      </div>

      {finalScore && (
        <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg">
          <h3 className="text-xl font-bold mb-4">Final Score</h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {(finalScore.composite * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Composite</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-semibold text-purple-600">
                {(finalScore.psychology.composite * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Psychology</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-semibold text-green-600">
                {(finalScore.hookStrength.strength * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Hook Strength</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-semibold text-orange-600">
                {(finalScore.novelty.composite * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Novelty</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const RenderProgressStreamExample: React.FC<{ jobId: string }> = ({ jobId }) => {
  const {
    progress,
    currentFrame,
    totalFrames,
    stage,
    fps,
    estimatedTime,
    isConnected,
    error
  } = useRenderProgressStream(jobId);

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">Video Render Progress</h2>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded mb-4">
          <p className="text-red-800">Error: {error.message}</p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span className="font-medium">Progress</span>
            <span className="text-blue-600">{(progress * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-300"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Stage:</span>
            <p className="font-semibold capitalize">{stage}</p>
          </div>

          <div>
            <span className="text-sm text-gray-600">Frame:</span>
            <p className="font-semibold">{currentFrame} / {totalFrames}</p>
          </div>

          <div>
            <span className="text-sm text-gray-600">FPS:</span>
            <p className="font-semibold">{fps}</p>
          </div>

          <div>
            <span className="text-sm text-gray-600">Time Remaining:</span>
            <p className="font-semibold">{Math.round(estimatedTime)}s</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

export const LiveMetricsExample: React.FC<{ campaignId: string }> = ({ campaignId }) => {
  const {
    metrics,
    change,
    isConnected,
    error,
    startStreaming,
    stopStreaming
  } = useCampaignMetricsStream(campaignId);

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Live Campaign Metrics</h2>

        <div className="space-x-2">
          {!isConnected ? (
            <button
              onClick={startStreaming}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Start Live Updates
            </button>
          ) : (
            <button
              onClick={stopStreaming}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Stop Updates
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded mb-4">
          <p className="text-red-800">Error: {error.message}</p>
        </div>
      )}

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard
            label="Impressions"
            value={metrics.impressions?.toLocaleString()}
            delta={change?.impressions}
          />
          <MetricCard
            label="Clicks"
            value={metrics.clicks?.toLocaleString()}
            delta={change?.clicks}
          />
          <MetricCard
            label="CTR"
            value={`${((metrics.ctr || 0) * 100).toFixed(2)}%`}
            delta={change?.ctr ? Number((change.ctr * 100).toFixed(2)) : undefined}
          />
          <MetricCard
            label="Spend"
            value={`$${metrics.spend?.toFixed(2)}`}
            delta={change?.spend}
            isDollar
          />
          <MetricCard
            label="Conversions"
            value={metrics.conversions?.toLocaleString()}
          />
          <MetricCard
            label="ROAS"
            value={`${metrics.roas?.toFixed(2)}x`}
          />
        </div>
      )}

      <div className="mt-4 flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
        <span className="text-sm text-gray-600">
          {isConnected ? 'Live' : 'Not Connected'}
        </span>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{
  label: string;
  value: string | number;
  delta?: number;
  isDollar?: boolean;
}> = ({ label, value, delta, isDollar }) => {
  const deltaColor = delta && delta > 0 ? 'text-green-600' : delta && delta < 0 ? 'text-red-600' : 'text-gray-600';

  return (
    <div className="p-4 bg-gray-50 rounded">
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
      {delta !== undefined && delta !== null && (
        <div className={`text-sm font-medium ${deltaColor}`}>
          {delta > 0 ? '↑' : delta < 0 ? '↓' : ''}
          {isDollar ? '$' : ''}{Math.abs(delta)}
        </div>
      )}
    </div>
  );
};

export const RealtimeAlertsExample: React.FC = () => {
  const { alerts, isConnected, clearAlerts, dismissAlert } = useRealtimeAlerts('demo-user');

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Real-time Alerts</h2>

        <button
          onClick={clearAlerts}
          className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
        >
          Clear All
        </button>
      </div>

      <div className="flex items-center space-x-2 mb-4">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm text-gray-600">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      <div className="space-y-2">
        {alerts.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No alerts</p>
        ) : (
          alerts.map(alert => (
            <div
              key={alert.alertId}
              className={`p-4 border-l-4 rounded ${
                alert.severity === 'critical'
                  ? 'bg-red-50 border-red-500'
                  : alert.severity === 'warning'
                  ? 'bg-yellow-50 border-yellow-500'
                  : 'bg-blue-50 border-blue-500'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold">{alert.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                </div>

                <button
                  onClick={() => dismissAlert(alert.alertId)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
