import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getValidationStatus } from '../../services/api';

interface StatusCardProps {
    title: string;
    value: string | number | undefined;
    icon: string;
    color?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({ title, value, icon, color = 'blue' }) => (
    <div className={`bg-gray-800/60 border border-gray-700/60 rounded-lg p-4 flex flex-col items-center justify-center space-y-2`}>
        <div className="text-3xl">{icon}</div>
        <div className="text-sm text-gray-400 uppercase tracking-wider">{title}</div>
        <div className={`text-2xl font-bold text-${color}-400`}>
            {value !== undefined ? value : '-'}
        </div>
    </div>
);

export const ValidationStatusPanel: React.FC = () => {
    const { data: validationStatus, isLoading } = useQuery({
        queryKey: ['validation-status'],
        queryFn: getValidationStatus
    });

    if (isLoading) {
        return <div className="text-center text-gray-400 py-4">Loading validation status...</div>;
    }

    return (
        <div className="validation-status space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>🔍</span> Prediction Validation Status
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatusCard
                    title="Total Predictions"
                    value={validationStatus?.totalPredictions}
                    icon="📊"
                    color="blue"
                />
                <StatusCard
                    title="Validated"
                    value={validationStatus?.validatedPredictions}
                    icon="✅"
                    color="green"
                />
                <StatusCard
                    title="Pending Validation"
                    value={validationStatus?.pendingPredictions}
                    icon="⏳"
                    color="yellow"
                />
                <StatusCard
                    title="Avg. Validation Time"
                    value={validationStatus?.averageValidationTime ? `${validationStatus.averageValidationTime} days` : undefined}
                    icon="⏱️"
                    color="purple"
                />
            </div>
        </div>
    );
};
