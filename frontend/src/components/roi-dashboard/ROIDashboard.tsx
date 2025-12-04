import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';
import { getROIPerformance, getPredictionAccuracy } from '../../services/api';

interface MetricCardProps {
    title: string;
    value: string | number | undefined;
    trend?: any[];
    target?: number;
    color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, trend, target, color = 'indigo' }) => {
    const isPositive = trend && trend.length > 1 && trend[trend.length - 1].value > trend[trend.length - 2].value;

    return (
        <div className={`bg-gray-800/60 border border-gray-700/60 rounded-lg p-6 space-y-4`}>
            <div className="flex justify-between items-start">
                <div>
                    <div className="text-sm text-gray-400 uppercase tracking-wider">{title}</div>
                    <div className={`text-3xl font-bold text-${color}-400 mt-1`}>
                        {value !== undefined ? value : '-'}
                    </div>
                </div>
                {target && (
                    <div className="text-xs text-gray-500 bg-gray-700/50 px-2 py-1 rounded">
                        Target: {target}
                    </div>
                )}
            </div>

            {trend && (
                <div className="h-16">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trend}>
                            <defs>
                                <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={color === 'indigo' ? '#6366f1' : '#10b981'} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={color === 'indigo' ? '#6366f1' : '#10b981'} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke={color === 'indigo' ? '#6366f1' : '#10b981'}
                                fill={`url(#gradient-${title})`}
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export const ROIDashboard: React.FC = () => {
    const { data: roiData, isLoading: roiLoading } = useQuery({
        queryKey: ['roi-performance'],
        queryFn: getROIPerformance
    });

    const { data: accuracyData, isLoading: accuracyLoading } = useQuery({
        queryKey: ['prediction-accuracy'],
        queryFn: () => getPredictionAccuracy()
    });

    if (roiLoading || accuracyLoading) {
        return <div className="text-center text-gray-400 py-8">Loading ROI analytics...</div>;
    }

    // Transform trend data for charts
    const roiTrendData = roiData?.roiTrend?.map((item: any) => ({
        date: new Date(item.date).toLocaleDateString(),
        value: item.roi
    })) || [];

    const accuracyTrendData = accuracyData?.accuracyTrend?.map((item: any) => ({
        date: new Date(item.date).toLocaleDateString(),
        value: item.accuracy * 100 // Convert to percentage
    })) || [];

    const predictionVsActualData = accuracyData?.predictionVsActual?.map((item: any) => ({
        id: item.predictionId.substring(0, 8),
        predicted: item.predictedCtr,
        actual: item.actualCtr,
        difference: item.difference
    })) || [];

    return (
        <div className="roi-dashboard space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <MetricCard
                    title="Current ROI"
                    value={roiData?.currentRoi ? `${roiData.currentRoi}x` : undefined}
                    trend={roiTrendData}
                    target={25}
                    color="green"
                />
                <MetricCard
                    title="Prediction Accuracy"
                    value={accuracyData?.overallAccuracy ? `${(accuracyData.overallAccuracy * 100).toFixed(1)}%` : undefined}
                    trend={accuracyTrendData}
                    target={85}
                    color="indigo"
                />
            </div>

            <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                    <span>🎯</span> Prediction vs Actual Performance
                </h3>
                <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={predictionVsActualData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="id" stroke="#9ca3af" fontSize={12} />
                            <YAxis stroke="#9ca3af" fontSize={12} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" name="Predicted CTR" strokeWidth={2} />
                            <Line type="monotone" dataKey="actual" stroke="#10b981" name="Actual CTR" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};
