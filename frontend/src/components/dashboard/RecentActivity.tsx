import React from 'react';

interface ActivityItem {
  id: number;
  type: 'video' | 'campaign' | 'analysis' | 'ai' | 'export';
  message: string;
  time: string;
}

interface RecentActivityProps {
  activities?: ActivityItem[];
  maxItems?: number;
}

const mockActivity: ActivityItem[] = [
  { id: 1, type: 'video', message: 'Video "Hook Test #47" generated', time: '2 min ago' },
  { id: 2, type: 'campaign', message: 'Campaign "Black Friday" launched', time: '1 hour ago' },
  { id: 3, type: 'analysis', message: 'Competitor ad analyzed successfully', time: '2 hours ago' },
  { id: 4, type: 'ai', message: 'AI generated 5 new hook variations', time: '3 hours ago' },
  { id: 5, type: 'export', message: 'Exported "Q4 Performance" report', time: '5 hours ago' },
  { id: 6, type: 'video', message: 'Video "Product Demo v2" rendered', time: '6 hours ago' },
  { id: 7, type: 'campaign', message: 'Campaign "Holiday Sale" paused', time: '8 hours ago' },
];

const getActivityIcon = (type: ActivityItem['type']) => {
  switch (type) {
    case 'video':
      return (
        <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m22 8-6 4 6 4V8Z" />
            <rect x="2" y="6" width="14" height="12" rx="2" ry="2" strokeWidth={2} />
          </svg>
        </div>
      );
    case 'campaign':
      return (
        <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      );
    case 'analysis':
      return (
        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
      );
    case 'ai':
      return (
        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
          </svg>
        </div>
      );
    case 'export':
      return (
        <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
      );
  }
};

export const RecentActivity: React.FC<RecentActivityProps> = ({
  activities = mockActivity,
  maxItems = 5,
}) => {
  const displayedActivities = activities.slice(0, maxItems);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-5 shadow-lg shadow-black/20 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold text-base sm:text-lg">Recent Activity</h3>
        <button className="text-indigo-400 hover:text-indigo-300 text-xs sm:text-sm font-medium transition-colors">
          View all
        </button>
      </div>

      <div className="space-y-3">
        {displayedActivities.map((activity) => (
          <div
            key={activity.id}
            className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 rounded-lg hover:bg-zinc-800/50 transition-colors cursor-pointer"
          >
            {getActivityIcon(activity.type)}
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm truncate">{activity.message}</p>
              <p className="text-zinc-500 text-xs mt-0.5">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>

      {activities.length > maxItems && (
        <div className="mt-4 pt-3 border-t border-zinc-800">
          <p className="text-zinc-500 text-sm text-center">
            +{activities.length - maxItems} more activities
          </p>
        </div>
      )}
    </div>
  );
};

export default RecentActivity;
