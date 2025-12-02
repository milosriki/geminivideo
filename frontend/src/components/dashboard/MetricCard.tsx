import React, { useEffect, useState } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  format?: 'number' | 'currency' | 'percentage' | 'multiplier';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  change,
  changeLabel,
  icon,
  format = 'number',
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const targetValue = typeof value === 'number' ? value : parseFloat(value.replace(/[^0-9.-]/g, '')) || 0;

  useEffect(() => {
    const duration = 1000;
    const steps = 30;
    const stepDuration = duration / steps;
    const increment = targetValue / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setDisplayValue(targetValue);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.min(increment * currentStep, targetValue));
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [targetValue]);

  const formatValue = (val: number): string => {
    switch (format) {
      case 'currency':
        return `$${val.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
      case 'percentage':
        return `${val.toFixed(0)}%`;
      case 'multiplier':
        return `${val.toFixed(1)}x`;
      default:
        return val >= 1000
          ? val.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
          : val.toFixed(0);
    }
  };

  const isPositive = change !== undefined && change >= 0;
  const changeColor = isPositive ? 'text-emerald-500' : 'text-red-500';

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg shadow-black/20 hover:border-zinc-700 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-zinc-400 text-sm font-medium uppercase tracking-wide">
          {label}
        </span>
        {icon && (
          <div className="text-zinc-500">
            {icon}
          </div>
        )}
      </div>

      <div className="text-3xl font-bold text-white mb-2">
        {formatValue(displayValue)}
      </div>

      {(change !== undefined || changeLabel) && (
        <div className="flex items-center gap-1.5">
          {change !== undefined && (
            <>
              <span className={changeColor}>
                {isPositive ? (
                  <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                )}
              </span>
              <span className={`text-sm font-medium ${changeColor}`}>
                {isPositive ? '+' : ''}{typeof change === 'number' && change % 1 !== 0 ? change.toFixed(1) : change}
                {changeLabel?.includes('%') ? '%' : ''}
              </span>
            </>
          )}
          {changeLabel && (
            <span className="text-zinc-500 text-sm">
              {changeLabel}
            </span>
          )}
        </div>
      )}

      {/* Mini sparkline placeholder */}
      <div className="mt-3 h-8 flex items-end gap-0.5">
        {[40, 55, 45, 60, 50, 70, 65, 80, 75, 90, 85, 95].map((height, i) => (
          <div
            key={i}
            className="flex-1 bg-gradient-to-t from-indigo-600/30 to-indigo-500/50 rounded-t"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
};

export default MetricCard;
