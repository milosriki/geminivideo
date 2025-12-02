import { ReactNode } from 'react';

interface PageWrapperProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageWrapper({
  title,
  description,
  actions,
  children,
}: PageWrapperProps) {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{title}</h1>
          {description && (
            <p className="text-zinc-400 mt-1">{description}</p>
          )}
        </div>
        {actions && <div className="flex gap-3">{actions}</div>}
      </div>

      {/* Page Content */}
      {children}
    </div>
  );
}
