import React, { Fragment, useState } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import { BoardSelector } from './BoardSelector';
import { useAuth } from '@/contexts/AuthContext';
import { apiUrl } from '@/config/api';

interface AdDetail {
  id: string;
  thumbnail: string;
  platform: 'meta' | 'tiktok' | 'youtube';
  brand: string;
  hook: string;
  views: number;
  likes: number;
  shares?: number;
  comments?: number;
  date: string;
  style: string;
  script?: string;
  impressions?: number;
  ctr?: number;
  engagement?: number;
}

interface AdDetailModalProps {
  ad: AdDetail | null;
  isOpen: boolean;
  onClose: () => void;
  boards?: Array<{ id: string; name: string; count?: number }>;
  selectedBoardId?: string | null;
  onSaveToBoard?: (boardId: string) => void;
  onCreateBoard?: () => void;
}

const XIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const ClipboardIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const SparklesIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  </svg>
);

const BookmarkIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
  </svg>
);

const getPlatformBadge = (platform: string) => {
  const badges = {
    meta: { color: 'bg-blue-600', label: 'Meta' },
    tiktok: { color: 'bg-pink-500', label: 'TikTok' },
    youtube: { color: 'bg-red-600', label: 'YouTube' },
  };
  return badges[platform as keyof typeof badges] || { color: 'bg-gray-600', label: platform };
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

export const AdDetailModal: React.FC<AdDetailModalProps> = ({
  ad,
  isOpen,
  onClose,
  boards = [],
  selectedBoardId = null,
  onSaveToBoard,
  onCreateBoard,
}) => {
  const navigate = useNavigate();
  const { currentUser, getIdToken } = useAuth();
  const [copiedScript, setCopiedScript] = useState(false);
  const [isCreatingSimilar, setIsCreatingSimilar] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!ad) return null;

  const platformBadge = getPlatformBadge(ad.platform);

  const handleCopyScript = () => {
    if (ad.script) {
      navigator.clipboard.writeText(ad.script);
      setCopiedScript(true);
      setTimeout(() => setCopiedScript(false), 2000);
    }
  };

  const handleCreateSimilar = async () => {
    setIsCreatingSimilar(true);
    setError(null);

    try {
      if (!currentUser) {
        throw new Error('You must be logged in to create ads');
      }

      const token = await getIdToken();
      const response = await fetch(apiUrl('/ads/create-similar'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          sourceAdId: ad.id,
          platform: ad.platform,
          style: ad.style,
          hook: ad.hook,
          userId: currentUser.uid
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create similar ad');
      }

      const newAd = await response.json();

      // Navigate to the AI creative studio with the new ad as template
      navigate('/studio/ai-creative', {
        state: { templateAd: newAd }
      });
    } catch (error) {
      console.error('Failed to create similar ad:', error);
      setError(error instanceof Error ? error.message : 'Failed to create similar ad. Please try again.');
    } finally {
      setIsCreatingSimilar(false);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-zinc-900 border border-zinc-800 shadow-2xl transition-all">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-zinc-800">
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 ${platformBadge.color} rounded-lg text-sm font-semibold`}>
                      {platformBadge.label}
                    </span>
                    <Dialog.Title className="text-xl font-bold text-white">
                      {ad.brand}
                    </Dialog.Title>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                  >
                    <XIcon className="w-5 h-5 text-zinc-400" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6 max-h-[calc(90vh-200px)] overflow-y-auto">
                  {/* Video Preview */}
                  <div className="aspect-video bg-zinc-950 rounded-lg mb-6 flex items-center justify-center border border-zinc-800">
                    <div className="text-center">
                      <div className="text-6xl font-bold text-zinc-700 mb-2">
                        {ad.brand.charAt(0)}
                      </div>
                      <div className="text-sm text-zinc-600">Video Preview</div>
                    </div>
                  </div>

                  {/* Tabs */}
                  <Tab.Group>
                    <Tab.List className="flex gap-2 border-b border-zinc-800 mb-6">
                      <Tab as={Fragment}>
                        {({ selected }) => (
                          <button
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                              selected
                                ? 'border-indigo-500 text-white'
                                : 'border-transparent text-zinc-400 hover:text-white'
                            }`}
                          >
                            Overview
                          </button>
                        )}
                      </Tab>
                      <Tab as={Fragment}>
                        {({ selected }) => (
                          <button
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                              selected
                                ? 'border-indigo-500 text-white'
                                : 'border-transparent text-zinc-400 hover:text-white'
                            }`}
                          >
                            Script
                          </button>
                        )}
                      </Tab>
                      <Tab as={Fragment}>
                        {({ selected }) => (
                          <button
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                              selected
                                ? 'border-indigo-500 text-white'
                                : 'border-transparent text-zinc-400 hover:text-white'
                            }`}
                          >
                            Analytics
                          </button>
                        )}
                      </Tab>
                    </Tab.List>

                    <Tab.Panels>
                      {/* Overview Panel */}
                      <Tab.Panel className="space-y-6">
                        {/* Hook */}
                        <div>
                          <h3 className="text-sm font-semibold text-zinc-400 mb-2">Hook</h3>
                          <p className="text-lg font-medium text-white">{ad.hook}</p>
                        </div>

                        {/* Metadata Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
                            <div className="text-xs text-zinc-500 mb-1">Platform</div>
                            <div className="font-semibold text-white">{platformBadge.label}</div>
                          </div>
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
                            <div className="text-xs text-zinc-500 mb-1">Style</div>
                            <div className="font-semibold text-white capitalize">{ad.style}</div>
                          </div>
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
                            <div className="text-xs text-zinc-500 mb-1">Date</div>
                            <div className="font-semibold text-white">{ad.date}</div>
                          </div>
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
                            <div className="text-xs text-zinc-500 mb-1">Views</div>
                            <div className="font-semibold text-white">{formatNumber(ad.views)}</div>
                          </div>
                        </div>

                        {/* Engagement Stats */}
                        <div>
                          <h3 className="text-sm font-semibold text-zinc-400 mb-3">Engagement</h3>
                          <div className="grid grid-cols-3 gap-4">
                            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 text-center">
                              <div className="text-2xl font-bold text-white mb-1">
                                {formatNumber(ad.likes)}
                              </div>
                              <div className="text-xs text-zinc-500">Likes</div>
                            </div>
                            {ad.comments !== undefined && (
                              <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 text-center">
                                <div className="text-2xl font-bold text-white mb-1">
                                  {formatNumber(ad.comments)}
                                </div>
                                <div className="text-xs text-zinc-500">Comments</div>
                              </div>
                            )}
                            {ad.shares !== undefined && (
                              <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 text-center">
                                <div className="text-2xl font-bold text-white mb-1">
                                  {formatNumber(ad.shares)}
                                </div>
                                <div className="text-xs text-zinc-500">Shares</div>
                              </div>
                            )}
                          </div>
                        </div>
                      </Tab.Panel>

                      {/* Script Panel */}
                      <Tab.Panel>
                        <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-semibold text-zinc-400">Full Script</h3>
                            <button
                              onClick={handleCopyScript}
                              className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors"
                            >
                              <ClipboardIcon className="w-4 h-4" />
                              {copiedScript ? 'Copied!' : 'Copy'}
                            </button>
                          </div>
                          <div className="text-white whitespace-pre-wrap">
                            {ad.script || 'Script not available for this ad.'}
                          </div>
                        </div>
                      </Tab.Panel>

                      {/* Analytics Panel */}
                      <Tab.Panel className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 text-center">
                            <div className="text-3xl font-bold text-indigo-400 mb-2">
                              {ad.impressions ? formatNumber(ad.impressions) : 'N/A'}
                            </div>
                            <div className="text-sm text-zinc-500">Impressions</div>
                          </div>
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 text-center">
                            <div className="text-3xl font-bold text-green-400 mb-2">
                              {ad.ctr ? `${ad.ctr}%` : 'N/A'}
                            </div>
                            <div className="text-sm text-zinc-500">CTR</div>
                          </div>
                          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 text-center">
                            <div className="text-3xl font-bold text-purple-400 mb-2">
                              {ad.engagement ? `${ad.engagement}%` : 'N/A'}
                            </div>
                            <div className="text-sm text-zinc-500">Engagement Rate</div>
                          </div>
                        </div>

                        <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
                          <h3 className="text-sm font-semibold text-zinc-400 mb-4">
                            Performance Insights
                          </h3>
                          <div className="space-y-3 text-sm text-zinc-300">
                            <p>• High engagement rate indicates strong audience resonance</p>
                            <p>• Video style is performing well in this niche</p>
                            <p>• Hook captures attention within first 3 seconds</p>
                          </div>
                        </div>
                      </Tab.Panel>
                    </Tab.Panels>
                  </Tab.Group>
                </div>

                {/* Footer Actions */}
                <div className="flex items-center justify-between gap-4 p-6 border-t border-zinc-800 bg-zinc-950/50">
                  <div className="flex items-center gap-3">
                    {boards.length > 0 && onSaveToBoard && (
                      <BoardSelector
                        boards={boards}
                        selectedBoardId={selectedBoardId}
                        onSelectBoard={onSaveToBoard}
                        onCreateBoard={onCreateBoard}
                      />
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleCopyScript}
                      className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg font-medium transition-colors"
                    >
                      <ClipboardIcon className="w-4 h-4" />
                      Copy Script
                    </button>
                    <button
                      onClick={handleCreateSimilar}
                      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
                    >
                      <SparklesIcon className="w-4 h-4" />
                      Create Similar
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default AdDetailModal;
