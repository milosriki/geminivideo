import React from 'react';
import {
  RocketLaunchIcon,
  FolderIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  VideoCameraIcon,
  UserGroupIcon,
  DocumentIcon,
  InboxIcon,
} from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

export interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: React.ReactNode;
}

// Preset component type
type PresetComponent = React.FC<Partial<EmptyStateProps>>;

// Compound component interface
interface EmptyStateComponent extends React.FC<EmptyStateProps> {
  Campaigns: PresetComponent;
  Assets: PresetComponent;
  Analytics: PresetComponent;
  Search: PresetComponent;
  Videos: PresetComponent;
  Team: PresetComponent;
  Documents: PresetComponent;
  Generic: PresetComponent;
}

const EmptyStateBase: React.FC<EmptyStateProps> = ({
  icon: Icon = InboxIcon,
  title,
  description,
  actionLabel,
  onAction,
  children,
}) => {
  return (
    <motion.div
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Icon */}
      <motion.div
        className="mb-6"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.4 }}
      >
        <div className="w-20 h-20 rounded-full bg-zinc-800/50 flex items-center justify-center">
          <Icon className="w-10 h-10 text-zinc-500" />
        </div>
      </motion.div>

      {/* Title */}
      <motion.h3
        className="text-xl font-semibold text-white mb-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        {title}
      </motion.h3>

      {/* Description */}
      {description && (
        <motion.p
          className="text-zinc-400 max-w-md mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          {description}
        </motion.p>
      )}

      {/* Action Button */}
      {actionLabel && onAction && (
        <motion.button
          onClick={onAction}
          className="px-6 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-zinc-950"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {actionLabel}
        </motion.button>
      )}

      {/* Custom Children */}
      {children && (
        <motion.div
          className="mt-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.4 }}
        >
          {children}
        </motion.div>
      )}
    </motion.div>
  );
};

// Create compound component
const EmptyState = EmptyStateBase as EmptyStateComponent;

// Preset Components
EmptyState.Campaigns = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={RocketLaunchIcon}
    title="No campaigns yet"
    description="Create your first campaign to start generating and managing video content at scale."
    actionLabel="Create Campaign"
    {...props}
  />
);

EmptyState.Assets = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={FolderIcon}
    title="No assets uploaded"
    description="Upload your first video, image, or audio file to get started with your content library."
    actionLabel="Upload Assets"
    {...props}
  />
);

EmptyState.Analytics = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={ChartBarIcon}
    title="No data available"
    description="Analytics data will appear here once you start generating and publishing content."
    {...props}
  />
);

EmptyState.Search = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={MagnifyingGlassIcon}
    title="No results found"
    description="Try adjusting your search terms or filters to find what you're looking for."
    {...props}
  />
);

EmptyState.Videos = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={VideoCameraIcon}
    title="No videos yet"
    description="Start creating videos using our AI-powered tools or upload your existing content."
    actionLabel="Create Video"
    {...props}
  />
);

EmptyState.Team = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={UserGroupIcon}
    title="No team members"
    description="Invite team members to collaborate on your video projects and campaigns."
    actionLabel="Invite Team"
    {...props}
  />
);

EmptyState.Documents = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={DocumentIcon}
    title="No documents"
    description="Upload documents to generate video scripts and content ideas automatically."
    actionLabel="Upload Document"
    {...props}
  />
);

EmptyState.Generic = (props: Partial<EmptyStateProps>) => (
  <EmptyStateBase
    icon={InboxIcon}
    title="Nothing here"
    description="This section is currently empty."
    {...props}
  />
);

export { EmptyState };
export default EmptyState;
