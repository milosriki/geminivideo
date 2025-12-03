import React from 'react';
import Skeleton, { SkeletonTableRow, SkeletonText } from '../ui/Skeleton';

export interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  showActions?: boolean;
}

const TableSkeleton: React.FC<TableSkeletonProps> = ({
  rows = 5,
  columns = 5,
  showHeader = true,
  showActions = false,
}) => {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-zinc-800">
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Table Header */}
          {showHeader && (
            <thead className="bg-zinc-900/50 border-b border-zinc-800">
              <tr>
                {Array.from({ length: columns }).map((_, i) => (
                  <th key={i} className="px-6 py-4 text-left">
                    <SkeletonText width={i === 0 ? '150px' : '120px'} height="16px" />
                  </th>
                ))}
                {showActions && (
                  <th className="px-6 py-4 text-right">
                    <SkeletonText width="80px" height="16px" className="ml-auto" />
                  </th>
                )}
              </tr>
            </thead>
          )}

          {/* Table Body */}
          <tbody className="divide-y divide-zinc-800">
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <tr key={rowIndex} className="bg-zinc-900/20 hover:bg-zinc-900/40 transition-colors">
                {Array.from({ length: columns }).map((_, colIndex) => (
                  <td key={colIndex} className="px-6 py-4">
                    {colIndex === 0 ? (
                      // First column - with avatar/icon
                      <div className="flex items-center space-x-3">
                        <Skeleton width="40px" height="40px" rounded circle />
                        <div className="space-y-1">
                          <SkeletonText width="150px" height="16px" />
                          <SkeletonText width="100px" height="14px" />
                        </div>
                      </div>
                    ) : (
                      // Other columns
                      <SkeletonText
                        width={
                          colIndex === 1 ? '180px' :
                          colIndex === 2 ? '120px' :
                          colIndex === 3 ? '100px' :
                          '140px'
                        }
                        height="16px"
                      />
                    )}
                  </td>
                ))}
                {showActions && (
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <Skeleton width="32px" height="32px" rounded />
                      <Skeleton width="32px" height="32px" rounded />
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Compact table variant
export const CompactTableSkeleton: React.FC<Pick<TableSkeletonProps, 'rows' | 'columns'>> = ({
  rows = 8,
  columns = 4,
}) => {
  return (
    <div className="w-full space-y-2">
      {/* Header */}
      <div className="flex items-center space-x-4 px-4 py-2 bg-zinc-900/30 rounded">
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className={i === 0 ? 'flex-1' : 'w-24'}>
            <SkeletonText width="100%" height="14px" />
          </div>
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 px-4 py-3 bg-zinc-900/20 rounded hover:bg-zinc-900/30 transition-colors">
          {Array.from({ length: columns }).map((_, j) => (
            <div key={j} className={j === 0 ? 'flex-1' : 'w-24'}>
              <SkeletonText width="100%" height="14px" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

// List variant (alternative to table)
export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 5 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 bg-zinc-900/30 rounded-lg border border-zinc-800">
          <Skeleton width="56px" height="56px" rounded />
          <div className="flex-1 space-y-2">
            <SkeletonText width="60%" height="18px" />
            <SkeletonText width="40%" height="14px" />
          </div>
          <div className="space-y-2 text-right">
            <SkeletonText width="80px" height="16px" />
            <SkeletonText width="100px" height="14px" />
          </div>
        </div>
      ))}
    </div>
  );
};

export default TableSkeleton;
