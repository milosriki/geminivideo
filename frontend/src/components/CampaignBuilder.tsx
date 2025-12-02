import React, { useState, useCallback } from 'react';
import { SparklesIcon, WandIcon, CheckIcon, UploadIcon, TagIcon } from './icons';

interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  budget: number;
  spent: number;
  platform: 'meta' | 'google' | 'tiktok' | 'youtube';
  startDate: string;
  endDate: string;
  objective: string;
  targeting: {
    ageRange: [number, number];
    gender: 'all' | 'male' | 'female';
    interests: string[];
    locations: string[];
  };
  creatives: CampaignCreative[];
}

interface CampaignCreative {
  id: string;
  name: string;
  type: 'video' | 'image' | 'carousel';
  status: 'pending' | 'approved' | 'rejected';
  thumbnail?: string;
  metrics?: {
    impressions: number;
    clicks: number;
    conversions: number;
    ctr: number;
  };
}

interface CampaignBuilderProps {
  campaignId?: string;
  onSave?: (campaign: Partial<Campaign>) => void;
  onPublish?: (campaign: Campaign) => void;
}

const PLATFORMS = [
  { id: 'meta', name: 'Meta (Facebook/Instagram)', color: 'bg-blue-600' },
  { id: 'google', name: 'Google Ads', color: 'bg-red-500' },
  { id: 'tiktok', name: 'TikTok', color: 'bg-pink-500' },
  { id: 'youtube', name: 'YouTube', color: 'bg-red-600' },
];

const OBJECTIVES = [
  'Brand Awareness',
  'Traffic',
  'Engagement',
  'Leads',
  'App Promotion',
  'Sales',
  'Video Views',
  'Conversions',
];

export const CampaignBuilder: React.FC<CampaignBuilderProps> = ({
  campaignId,
  onSave,
  onPublish
}) => {
  const [step, setStep] = useState(1);
  const [campaign, setCampaign] = useState<Partial<Campaign>>({
    name: '',
    status: 'draft',
    platform: 'meta',
    budget: 500,
    objective: 'Conversions',
    targeting: {
      ageRange: [18, 65],
      gender: 'all',
      interests: [],
      locations: [],
    },
    creatives: [],
  });
  const [newInterest, setNewInterest] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const steps = [
    { id: 1, name: 'Campaign Basics', icon: TagIcon },
    { id: 2, name: 'Targeting', icon: SparklesIcon },
    { id: 3, name: 'Creatives', icon: WandIcon },
    { id: 4, name: 'Review & Launch', icon: CheckIcon },
  ];

  const handlePlatformSelect = (platformId: string) => {
    setCampaign(prev => ({ ...prev, platform: platformId as Campaign['platform'] }));
  };

  const addInterest = () => {
    if (newInterest.trim() && campaign.targeting) {
      setCampaign(prev => ({
        ...prev,
        targeting: {
          ...prev.targeting!,
          interests: [...(prev.targeting?.interests || []), newInterest.trim()],
        },
      }));
      setNewInterest('');
    }
  };

  const addLocation = () => {
    if (newLocation.trim() && campaign.targeting) {
      setCampaign(prev => ({
        ...prev,
        targeting: {
          ...prev.targeting!,
          locations: [...(prev.targeting?.locations || []), newLocation.trim()],
        },
      }));
      setNewLocation('');
    }
  };

  const removeInterest = (interest: string) => {
    setCampaign(prev => ({
      ...prev,
      targeting: {
        ...prev.targeting!,
        interests: prev.targeting?.interests.filter(i => i !== interest) || [],
      },
    }));
  };

  const removeLocation = (location: string) => {
    setCampaign(prev => ({
      ...prev,
      targeting: {
        ...prev.targeting!,
        locations: prev.targeting?.locations.filter(l => l !== location) || [],
      },
    }));
  };

  const handleSave = useCallback(async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      onSave?.(campaign);
    } finally {
      setIsLoading(false);
    }
  }, [campaign, onSave]);

  const handlePublish = useCallback(async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      const completeCampaign: Campaign = {
        id: campaignId || `campaign_${Date.now()}`,
        name: campaign.name || 'Untitled Campaign',
        status: 'active',
        budget: campaign.budget || 500,
        spent: 0,
        platform: campaign.platform || 'meta',
        startDate: new Date().toISOString(),
        endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        objective: campaign.objective || 'Conversions',
        targeting: campaign.targeting || {
          ageRange: [18, 65],
          gender: 'all',
          interests: [],
          locations: [],
        },
        creatives: campaign.creatives || [],
      };
      onPublish?.(completeCampaign);
    } finally {
      setIsLoading(false);
    }
  }, [campaign, campaignId, onPublish]);

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Campaign Name
              </label>
              <input
                type="text"
                value={campaign.name || ''}
                onChange={e => setCampaign(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter campaign name..."
                className="w-full p-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Platform
              </label>
              <div className="grid grid-cols-2 gap-3">
                {PLATFORMS.map(platform => (
                  <button
                    key={platform.id}
                    onClick={() => handlePlatformSelect(platform.id)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      campaign.platform === platform.id
                        ? 'border-indigo-500 bg-indigo-900/30'
                        : 'border-gray-700 bg-gray-800/60 hover:border-gray-600'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full ${platform.color} mb-2`} />
                    <span className="text-sm font-medium">{platform.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Objective
              </label>
              <select
                value={campaign.objective || ''}
                onChange={e => setCampaign(prev => ({ ...prev, objective: e.target.value }))}
                className="w-full p-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                {OBJECTIVES.map(obj => (
                  <option key={obj} value={obj}>{obj}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Daily Budget ($)
              </label>
              <input
                type="number"
                value={campaign.budget || 500}
                onChange={e => setCampaign(prev => ({ ...prev, budget: Number(e.target.value) }))}
                min={1}
                className="w-full p-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Age Range
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="number"
                  value={campaign.targeting?.ageRange[0] || 18}
                  onChange={e => setCampaign(prev => ({
                    ...prev,
                    targeting: {
                      ...prev.targeting!,
                      ageRange: [Number(e.target.value), prev.targeting?.ageRange[1] || 65],
                    },
                  }))}
                  min={13}
                  max={65}
                  className="w-24 p-2 bg-gray-800/60 border border-gray-700 rounded-lg"
                />
                <span className="text-gray-400">to</span>
                <input
                  type="number"
                  value={campaign.targeting?.ageRange[1] || 65}
                  onChange={e => setCampaign(prev => ({
                    ...prev,
                    targeting: {
                      ...prev.targeting!,
                      ageRange: [prev.targeting?.ageRange[0] || 18, Number(e.target.value)],
                    },
                  }))}
                  min={13}
                  max={65}
                  className="w-24 p-2 bg-gray-800/60 border border-gray-700 rounded-lg"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Gender
              </label>
              <div className="flex gap-3">
                {['all', 'male', 'female'].map(gender => (
                  <button
                    key={gender}
                    onClick={() => setCampaign(prev => ({
                      ...prev,
                      targeting: { ...prev.targeting!, gender: gender as 'all' | 'male' | 'female' },
                    }))}
                    className={`px-4 py-2 rounded-lg border transition-all ${
                      campaign.targeting?.gender === gender
                        ? 'border-indigo-500 bg-indigo-900/30 text-indigo-300'
                        : 'border-gray-700 bg-gray-800/60 hover:border-gray-600'
                    }`}
                  >
                    {gender.charAt(0).toUpperCase() + gender.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Interests
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newInterest}
                  onChange={e => setNewInterest(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addInterest()}
                  placeholder="Add interest..."
                  className="flex-1 p-2 bg-gray-800/60 border border-gray-700 rounded-lg"
                />
                <button
                  onClick={addInterest}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {campaign.targeting?.interests.map(interest => (
                  <span
                    key={interest}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-900/30 border border-indigo-700 rounded-full text-sm"
                  >
                    {interest}
                    <button
                      onClick={() => removeInterest(interest)}
                      className="hover:text-red-400"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Locations
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newLocation}
                  onChange={e => setNewLocation(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addLocation()}
                  placeholder="Add location..."
                  className="flex-1 p-2 bg-gray-800/60 border border-gray-700 rounded-lg"
                />
                <button
                  onClick={addLocation}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {campaign.targeting?.locations.map(location => (
                  <span
                    key={location}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-green-900/30 border border-green-700 rounded-full text-sm"
                  >
                    {location}
                    <button
                      onClick={() => removeLocation(location)}
                      className="hover:text-red-400"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors cursor-pointer">
              <UploadIcon className="w-12 h-12 mx-auto text-gray-500 mb-4" />
              <p className="text-gray-300 font-medium">Upload Creatives</p>
              <p className="text-sm text-gray-500 mt-1">
                Drag & drop videos or images, or click to browse
              </p>
            </div>

            {campaign.creatives && campaign.creatives.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {campaign.creatives.map(creative => (
                  <div
                    key={creative.id}
                    className="bg-gray-800/60 border border-gray-700 rounded-lg overflow-hidden"
                  >
                    <div className="aspect-video bg-gray-900 flex items-center justify-center">
                      {creative.thumbnail ? (
                        <img src={creative.thumbnail} alt={creative.name} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-gray-500">No preview</span>
                      )}
                    </div>
                    <div className="p-3">
                      <p className="font-medium text-sm truncate">{creative.name}</p>
                      <span className={`text-xs ${
                        creative.status === 'approved' ? 'text-green-400' :
                        creative.status === 'rejected' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {creative.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No creatives added yet</p>
                <p className="text-sm mt-1">Upload videos or images to use in your campaign</p>
              </div>
            )}

            <button className="w-full py-3 bg-indigo-600/20 border border-indigo-600 text-indigo-400 rounded-lg hover:bg-indigo-600/30 transition-colors flex items-center justify-center gap-2">
              <SparklesIcon className="w-5 h-5" />
              Generate AI Creatives
            </button>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Campaign Summary</h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-400">Name</dt>
                  <dd className="font-medium">{campaign.name || 'Untitled'}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-400">Platform</dt>
                  <dd className="font-medium capitalize">{campaign.platform}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-400">Objective</dt>
                  <dd className="font-medium">{campaign.objective}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-400">Daily Budget</dt>
                  <dd className="font-medium">${campaign.budget}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-400">Age Range</dt>
                  <dd className="font-medium">
                    {campaign.targeting?.ageRange[0]} - {campaign.targeting?.ageRange[1]}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-400">Gender</dt>
                  <dd className="font-medium capitalize">{campaign.targeting?.gender}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-sm text-gray-400 mb-1">Interests</dt>
                  <dd className="flex flex-wrap gap-1">
                    {campaign.targeting?.interests.length ? (
                      campaign.targeting.interests.map(i => (
                        <span key={i} className="px-2 py-0.5 bg-indigo-900/30 rounded text-sm">{i}</span>
                      ))
                    ) : (
                      <span className="text-gray-500 text-sm">None specified</span>
                    )}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-sm text-gray-400 mb-1">Locations</dt>
                  <dd className="flex flex-wrap gap-1">
                    {campaign.targeting?.locations.length ? (
                      campaign.targeting.locations.map(l => (
                        <span key={l} className="px-2 py-0.5 bg-green-900/30 rounded text-sm">{l}</span>
                      ))
                    ) : (
                      <span className="text-gray-500 text-sm">All locations</span>
                    )}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-sm text-gray-400">Creatives</dt>
                  <dd className="font-medium">{campaign.creatives?.length || 0} creatives</dd>
                </div>
              </dl>
            </div>

            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
              <p className="text-sm text-yellow-300">
                <strong>Ready to launch?</strong> Your campaign will start running immediately after publishing.
                You can pause or edit it at any time from the dashboard.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-8">
          {campaignId ? 'Edit Campaign' : 'Create New Campaign'}
        </h1>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((s, i) => (
            <React.Fragment key={s.id}>
              <button
                onClick={() => setStep(s.id)}
                className={`flex flex-col items-center ${
                  step >= s.id ? 'text-indigo-400' : 'text-gray-500'
                }`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${
                  step >= s.id ? 'bg-indigo-600' : 'bg-gray-700'
                }`}>
                  <s.icon className="w-5 h-5" />
                </div>
                <span className="text-xs font-medium hidden sm:block">{s.name}</span>
              </button>
              {i < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-2 ${
                  step > s.id ? 'bg-indigo-600' : 'bg-gray-700'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step Content */}
        <div className="bg-gray-800/40 border border-gray-700 rounded-xl p-6 mb-6">
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep(prev => Math.max(1, prev - 1))}
            disabled={step === 1}
            className="px-6 py-2 border border-gray-600 rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="px-6 py-2 border border-gray-600 rounded-lg hover:bg-gray-800 transition-colors"
            >
              Save Draft
            </button>
            {step < 4 ? (
              <button
                onClick={() => setStep(prev => Math.min(4, prev + 1))}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handlePublish}
                disabled={isLoading}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
              >
                {isLoading ? 'Publishing...' : 'Publish Campaign'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CampaignBuilder;
