import React, { useState } from 'react';
import CampaignBuilder from './CampaignBuilder';

/**
 * Example usage of the CampaignBuilder component
 *
 * This demonstrates how to integrate the Campaign Builder UI
 * into your application.
 */

const CampaignBuilderExample: React.FC = () => {
  const [showBuilder, setShowBuilder] = useState(false);
  const [completedCampaign, setCompletedCampaign] = useState<any>(null);

  const handleCampaignComplete = (campaign: any) => {
    console.log('Campaign created:', campaign);
    setCompletedCampaign(campaign);
    setShowBuilder(false);

    // Show success message
    alert(`Campaign "${campaign.name}" has been launched successfully!`);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Campaign Builder Demo</h1>

        {!showBuilder ? (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-2xl font-bold mb-4">Create Your First Campaign</h2>
              <p className="text-gray-400 mb-6">
                Use our AI-powered campaign builder to create high-performing ad campaigns
                in minutes. Get real-time ROAS predictions, audience size estimates, and
                optimization recommendations.
              </p>
              <button
                onClick={() => setShowBuilder(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                Start Building Campaign
              </button>
            </div>

            {completedCampaign && (
              <div className="bg-green-900/20 border border-green-500/50 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-green-400">
                  Last Campaign Created
                </h3>
                <div className="space-y-2 text-sm">
                  <p><strong>Name:</strong> {completedCampaign.name}</p>
                  <p><strong>Objective:</strong> {completedCampaign.objective}</p>
                  <p><strong>Budget:</strong> ${completedCampaign.budget?.amount} {completedCampaign.budget?.type}</p>
                  <p><strong>Creatives:</strong> {completedCampaign.creatives?.length || 0}</p>
                  <p><strong>Status:</strong> {completedCampaign.status}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-4">Features</h3>
              <ul className="grid md:grid-cols-2 gap-3 text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>6-step guided campaign creation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Real-time ROAS predictions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Audience size estimation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Budget optimizer suggestions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Drag & drop creative upload</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Asset library integration</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>A/B test variant setup</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Placement previews (Feed, Stories, Reels)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Campaign templates</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Form validation</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Save draft functionality</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">✓</span>
                  <span>Direct Meta API integration</span>
                </li>
              </ul>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-4">API Endpoints Used</h3>
              <div className="space-y-2 text-sm font-mono">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded">GET</span>
                  <span className="text-gray-400">/api/assets</span>
                  <span className="text-gray-500">- Load asset library</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded">POST</span>
                  <span className="text-gray-400">/api/campaigns/predict</span>
                  <span className="text-gray-500">- Get AI predictions</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded">POST</span>
                  <span className="text-gray-400">/api/campaigns/draft</span>
                  <span className="text-gray-500">- Save campaign draft</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded">POST</span>
                  <span className="text-gray-400">/api/campaigns/launch</span>
                  <span className="text-gray-500">- Launch campaign to Meta</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded">POST</span>
                  <span className="text-gray-400">/api/creatives/upload</span>
                  <span className="text-gray-500">- Upload creative files</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <CampaignBuilder onComplete={handleCampaignComplete} />
            <button
              onClick={() => setShowBuilder(false)}
              className="mt-6 text-gray-400 hover:text-white underline transition-colors"
            >
              Cancel and Go Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignBuilderExample;
