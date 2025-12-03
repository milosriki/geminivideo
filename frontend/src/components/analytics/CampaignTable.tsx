import React, { useState, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

type CampaignStatus = 'Active' | 'Paused' | 'Completed' | 'Draft';

interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  spend: number;
  revenue: number;
  roas: number;
  conversions: number;
}

type SortKey = keyof Campaign;
type SortDirection = 'asc' | 'desc';

const CAMPAIGNS_PER_PAGE = 10;

const StatusBadge: React.FC<{ status: CampaignStatus }> = ({ status }) => {
  const styles = {
    Active: 'bg-green-900/50 text-green-400 border-green-800',
    Paused: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
    Completed: 'bg-blue-900/50 text-blue-400 border-blue-800',
    Draft: 'bg-zinc-800 text-zinc-500 border-zinc-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${styles[status]}`}
    >
      {status}
    </span>
  );
};

const SortIcon: React.FC<{ active: boolean; direction: SortDirection }> = ({
  active,
  direction,
}) => {
  if (!active) {
    return (
      <svg className="w-4 h-4 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
        />
      </svg>
    );
  }

  return direction === 'asc' ? (
    <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
};

export const CampaignTable: React.FC = () => {
  const [sortKey, setSortKey] = useState<SortKey>('spend');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch campaigns from API
  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/campaigns`);
        if (!response.ok) {
          throw new Error(response.status.toString());
        }
        const data = await response.json();
        // Backend returns { campaigns: [...] } wrapper
        setCampaigns(data.campaigns || data || []);
        setError(null);
      } catch (err) {
        setError('Data source not configured. Please configure campaigns in the backend.');
        setCampaigns([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCampaigns();
  }, []);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  const sortedCampaigns = useMemo(() => {
    return [...campaigns].sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });
  }, [campaigns, sortKey, sortDirection]);

  const totalPages = Math.ceil(sortedCampaigns.length / CAMPAIGNS_PER_PAGE);
  const paginatedCampaigns = sortedCampaigns.slice(
    (currentPage - 1) * CAMPAIGNS_PER_PAGE,
    currentPage * CAMPAIGNS_PER_PAGE
  );

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Show loading state
  if (loading) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
        <div className="flex items-center justify-center py-12">
          <div className="text-zinc-400">Loading campaigns...</div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-red-400 mb-2">Error loading campaigns</div>
          <div className="text-zinc-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  // Show empty state
  if (campaigns.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="text-zinc-400">No campaigns available</div>
          <div className="text-zinc-500 text-sm mt-1">Create your first campaign to get started</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-zinc-800">
        <h2 className="text-base sm:text-lg font-semibold text-white">Campaign Performance</h2>
        <p className="text-xs sm:text-sm text-zinc-500 mt-1">
          {sortedCampaigns.length} campaigns tracked
        </p>
      </div>

      {/* Table - Horizontal scroll wrapper for mobile */}
      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle">
          <div className="overflow-hidden">
        <table className="min-w-full w-full">
          <thead>
            <tr className="bg-zinc-900/80 border-b border-zinc-800">
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-2">
                  Campaign Name
                  <SortIcon active={sortKey === 'name'} direction={sortDirection} />
                </div>
              </th>
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center gap-2">
                  Status
                  <SortIcon active={sortKey === 'status'} direction={sortDirection} />
                </div>
              </th>
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('spend')}
              >
                <div className="flex items-center justify-end gap-2">
                  Spend
                  <SortIcon active={sortKey === 'spend'} direction={sortDirection} />
                </div>
              </th>
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('revenue')}
              >
                <div className="flex items-center justify-end gap-2">
                  Revenue
                  <SortIcon active={sortKey === 'revenue'} direction={sortDirection} />
                </div>
              </th>
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('roas')}
              >
                <div className="flex items-center justify-end gap-2">
                  ROAS
                  <SortIcon active={sortKey === 'roas'} direction={sortDirection} />
                </div>
              </th>
              <th
                className="px-4 sm:px-6 py-3 sm:py-4 text-right text-xs font-semibold text-zinc-400 uppercase tracking-wider cursor-pointer hover:text-zinc-300 transition-colors whitespace-nowrap"
                onClick={() => handleSort('conversions')}
              >
                <div className="flex items-center justify-end gap-2">
                  Conversions
                  <SortIcon active={sortKey === 'conversions'} direction={sortDirection} />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {paginatedCampaigns.map((campaign, index) => (
              <motion.tr
                key={campaign.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.03 }}
                className="hover:bg-zinc-800/50 transition-colors cursor-pointer"
              >
                <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium text-white whitespace-nowrap">{campaign.name}</td>
                <td className="px-4 sm:px-6 py-3 sm:py-4">
                  <StatusBadge status={campaign.status} />
                </td>
                <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-right text-zinc-300 whitespace-nowrap">
                  {formatCurrency(campaign.spend)}
                </td>
                <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-right text-green-400 font-medium whitespace-nowrap">
                  {formatCurrency(campaign.revenue)}
                </td>
                <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-right font-semibold text-white whitespace-nowrap">
                  {campaign.roas > 0 ? `${campaign.roas.toFixed(2)}x` : '-'}
                </td>
                <td className="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-right text-zinc-300 whitespace-nowrap">
                  {campaign.conversions.toLocaleString()}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
          </div>
        </div>
      </div>

      {/* Pagination */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0">
        <div className="text-xs sm:text-sm text-zinc-500 text-center sm:text-left">
          Showing {(currentPage - 1) * CAMPAIGNS_PER_PAGE + 1} to{' '}
          {Math.min(currentPage * CAMPAIGNS_PER_PAGE, sortedCampaigns.length)} of{' '}
          {sortedCampaigns.length} campaigns
        </div>

        <div className="flex items-center gap-1 sm:gap-2 flex-wrap justify-center">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-2 sm:px-3 py-2 text-xs sm:text-sm rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[44px] sm:min-h-0"
          >
            Prev
          </button>

          {/* Show fewer page numbers on mobile */}
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((page) => {
              // On mobile, show only current, prev, and next pages
              if (window.innerWidth < 640) {
                return Math.abs(page - currentPage) <= 1;
              }
              return true;
            })
            .map((page) => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`px-2 sm:px-3 py-2 text-xs sm:text-sm rounded-lg transition-colors min-h-[44px] sm:min-h-0 ${
                  currentPage === page
                    ? 'bg-indigo-600 text-white'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200'
                }`}
              >
                {page}
              </button>
            ))}

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-2 sm:px-3 py-2 text-xs sm:text-sm rounded-lg bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[44px] sm:min-h-0"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
