import React from 'react';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  route: string;
  color: string;
  description?: string;
}

interface QuickActionsProps {
  onActionClick?: (action: QuickAction) => void;
}

const defaultActions: QuickAction[] = [
  {
    id: 'new-campaign',
    label: 'New Campaign',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    ),
    route: '/campaigns/new',
    color: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
    description: 'Start a new ad campaign',
  },
  {
    id: 'generate-video',
    label: 'Generate Video',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m22 8-6 4 6 4V8Z" />
        <rect x="2" y="6" width="14" height="12" rx="2" ry="2" strokeWidth={2} />
      </svg>
    ),
    route: '/videos/generate',
    color: 'bg-gradient-to-br from-purple-500 to-purple-600',
    description: 'AI-powered video creation',
  },
  {
    id: 'analyze-competitor',
    label: 'Analyze Competitor',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    route: '/analysis/competitor',
    color: 'bg-gradient-to-br from-cyan-500 to-cyan-600',
    description: 'Spy on competitor ads',
  },
  {
    id: 'view-analytics',
    label: 'View Analytics',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    route: '/analytics',
    color: 'bg-gradient-to-br from-emerald-500 to-emerald-600',
    description: 'Performance insights',
  },
];

export const QuickActions: React.FC<QuickActionsProps> = ({ onActionClick }) => {
  const handleClick = (action: QuickAction) => {
    if (onActionClick) {
      onActionClick(action);
    } else {
      console.log(`Navigate to: ${action.route}`);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg shadow-black/20">
      <h3 className="text-white font-semibold text-lg mb-4">Quick Actions</h3>

      <div className="grid grid-cols-1 gap-3">
        {defaultActions.map((action) => (
          <button
            key={action.id}
            onClick={() => handleClick(action)}
            className="group flex items-center gap-4 p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 hover:border-zinc-600 transition-all duration-200 text-left hover:scale-[1.02]"
          >
            <div className={`w-10 h-10 rounded-lg ${action.color} flex items-center justify-center text-white shadow-lg`}>
              {action.icon}
            </div>
            <div className="flex-1">
              <p className="text-white font-medium group-hover:text-indigo-300 transition-colors">
                {action.label}
              </p>
              {action.description && (
                <p className="text-zinc-500 text-sm">{action.description}</p>
              )}
            </div>
            <svg
              className="w-5 h-5 text-zinc-600 group-hover:text-zinc-400 group-hover:translate-x-1 transition-all"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;
