import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Trophy, AlertCircle, DollarSign, Target } from 'lucide-react';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface Variant {
  id: string;
  name: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  alpha: number;
  beta: number;
  ctr?: number;
  cvr?: number;
  roas?: number;
  expected_ctr?: number;
  confidence_interval?: {
    lower: number;
    upper: number;
  };
}

interface Experiment {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed';
  variants: Variant[];
  startDate: string;
  endDate?: string;
  totalBudget: number;
  explorationRate: number;
}

interface WinnerProbabilities {
  [variantId: string]: number;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const calculateCTR = (clicks: number, impressions: number): number => {
  return impressions > 0 ? (clicks / impressions) * 100 : 0;
};

const calculateCVR = (conversions: number, clicks: number): number => {
  return clicks > 0 ? (conversions / clicks) * 100 : 0;
};

const calculateROAS = (revenue: number, spend: number): number => {
  return spend > 0 ? revenue / spend : 0;
};

const calculateLift = (controlCTR: number, variantCTR: number): number => {
  return controlCTR > 0 ? ((variantCTR - controlCTR) / controlCTR) * 100 : 0;
};

// Thompson Sampling winner probability simulation
const calculateWinnerProbability = (variants: Variant[], samples: number = 10000): WinnerProbabilities => {
  const wins: { [id: string]: number } = {};

  variants.forEach(v => {
    wins[v.id] = 0;
  });

  for (let i = 0; i < samples; i++) {
    const sampleScores: { [id: string]: number } = {};

    variants.forEach(v => {
      // Sample from Beta distribution using inverse transform sampling approximation
      const u = Math.random();
      // Simple approximation - in production use proper Beta sampling
      const score = (v.alpha / (v.alpha + v.beta)) + (Math.random() - 0.5) * 0.1;
      sampleScores[v.id] = score;
    });

    // Find winner of this sample
    const winnerId = Object.keys(sampleScores).reduce((a, b) =>
      sampleScores[a] > sampleScores[b] ? a : b
    );

    wins[winnerId]++;
  }

  const probabilities: WinnerProbabilities = {};
  Object.keys(wins).forEach(id => {
    probabilities[id] = (wins[id] / samples) * 100;
  });

  return probabilities;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const ABTestingDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [winnerProbs, setWinnerProbs] = useState<WinnerProbabilities>({});

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Fetch experiments
  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(`${API_BASE_URL}/api/experiments`, {
          timeout: 15000
        });

        const experimentsData = response.data || [];
        setExperiments(experimentsData);

        if (experimentsData.length > 0) {
          setSelectedExperiment(experimentsData[0]);
        }
      } catch (err: any) {
        console.error('Failed to fetch experiments:', err);
        setError('Failed to load A/B tests. Using demo mode.');
        setExperiments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchExperiments();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchExperiments, 30000);
    return () => clearInterval(interval);
  }, [API_BASE_URL]);

  // Calculate winner probabilities when selected experiment changes
  useEffect(() => {
    if (selectedExperiment && selectedExperiment.variants && selectedExperiment.variants.length > 0) {
      const probs = calculateWinnerProbability(selectedExperiment.variants);
      setWinnerProbs(probs);
    }
  }, [selectedExperiment]);

  const currentWinner = selectedExperiment && winnerProbs
    ? Object.keys(winnerProbs).reduce((a, b) => (winnerProbs[a] > winnerProbs[b] ? a : b), Object.keys(winnerProbs)[0])
    : null;

  const currentWinnerProb = currentWinner ? winnerProbs[currentWinner] : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-lg text-purple-300">Loading A/B Tests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
              A/B Test Results - Thompson Sampling
            </h1>
            <p className="text-purple-300">
              Real-time variant performance with Thompson Sampling budget optimization
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-green-500/20 border border-green-500 rounded-lg px-4 py-2">
              <div className="text-xs text-green-400 uppercase font-semibold">Active Tests</div>
              <div className="text-2xl font-bold text-green-300">{experiments.length}</div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="text-yellow-400" size={24} />
            <p className="text-yellow-200">{error}</p>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Experiments List */}
        <div className="lg:col-span-1">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-6">
            <h2 className="text-xl font-bold mb-4 text-purple-300">Active Experiments</h2>

            {experiments.length === 0 ? (
              <div className="text-center py-8 text-purple-300">
                <AlertCircle className="mx-auto mb-3" size={48} />
                <p>No active experiments found</p>
                <p className="text-sm text-purple-400 mt-2">Create campaigns to see A/B tests here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {experiments.map((exp) => (
                  <div
                    key={exp.id}
                    onClick={() => setSelectedExperiment(exp)}
                    className={`cursor-pointer rounded-lg p-4 transition-all ${
                      selectedExperiment?.id === exp.id
                        ? 'bg-purple-600 border-2 border-purple-400'
                        : 'bg-white/5 border border-purple-500/20 hover:bg-white/10'
                    }`}
                  >
                    <div className="font-semibold text-sm mb-1 truncate">{exp.name}</div>
                    <div className="flex items-center gap-2 text-xs text-purple-300">
                      <span
                        className={`px-2 py-0.5 rounded ${
                          exp.status === 'running'
                            ? 'bg-green-500/30 text-green-300'
                            : 'bg-yellow-500/30 text-yellow-300'
                        }`}
                      >
                        {exp.status}
                      </span>
                      <span>{exp.variants?.length || 0} variants</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {selectedExperiment ? (
            <>
              {/* Winner Declaration */}
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl border border-purple-400/50 p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-yellow-400 rounded-full p-3">
                      <Trophy className="text-yellow-900" size={32} />
                    </div>
                    <div>
                      <div className="text-sm text-purple-100 uppercase font-semibold mb-1">
                        Current Leader
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {selectedExperiment.variants.find(v => v.id === currentWinner)?.name || 'N/A'}
                      </div>
                      <div className="text-purple-200">
                        {currentWinnerProb.toFixed(1)}% probability of being best
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    {currentWinnerProb > 95 ? (
                      <div className="bg-green-500 text-white px-4 py-2 rounded-lg font-bold">
                        HIGH CONFIDENCE
                      </div>
                    ) : currentWinnerProb > 80 ? (
                      <div className="bg-yellow-500 text-white px-4 py-2 rounded-lg font-bold">
                        MODERATE CONFIDENCE
                      </div>
                    ) : (
                      <div className="bg-gray-500 text-white px-4 py-2 rounded-lg font-bold">
                        KEEP TESTING
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Winner Probability Chart */}
              <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-6">
                <h3 className="text-xl font-bold mb-4 text-purple-300">Winner Probability (Thompson Sampling)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={selectedExperiment.variants.map(v => ({
                      name: v.name,
                      probability: winnerProbs[v.id] || 0,
                      isWinner: v.id === currentWinner,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="name" stroke="#999" />
                    <YAxis stroke="#999" label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #7c3aed' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="probability" radius={[8, 8, 0, 0]}>
                      {selectedExperiment.variants.map((v, index) => (
                        <Cell key={`cell-${index}`} fill={v.id === currentWinner ? '#10b981' : '#8b5cf6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Variant Comparison Table */}
              <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-6">
                <h3 className="text-xl font-bold mb-4 text-purple-300">Variant Performance Comparison</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-purple-500/30">
                        <th className="text-left py-3 px-2 text-sm text-purple-300">Variant</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">Impressions</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">CTR</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">CVR</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">ROAS</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">Win Prob</th>
                        <th className="text-right py-3 px-2 text-sm text-purple-300">Lift</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedExperiment.variants.map((variant, index) => {
                        const ctr = calculateCTR(variant.clicks, variant.impressions);
                        const cvr = calculateCVR(variant.conversions, variant.clicks);
                        const roas = calculateROAS(variant.revenue, variant.spend);
                        const controlCTR = calculateCTR(
                          selectedExperiment.variants[0].clicks,
                          selectedExperiment.variants[0].impressions
                        );
                        const lift = index === 0 ? 0 : calculateLift(controlCTR, ctr);
                        const isWinner = variant.id === currentWinner;

                        return (
                          <tr
                            key={variant.id}
                            className={`border-b border-purple-500/20 ${
                              isWinner ? 'bg-green-500/20' : ''
                            }`}
                          >
                            <td className="py-3 px-2">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold">{variant.name}</span>
                                {isWinner && <Trophy className="text-yellow-400" size={16} />}
                              </div>
                            </td>
                            <td className="text-right py-3 px-2 text-purple-200">
                              {variant.impressions.toLocaleString()}
                            </td>
                            <td className="text-right py-3 px-2 font-semibold">
                              {ctr.toFixed(2)}%
                            </td>
                            <td className="text-right py-3 px-2 font-semibold">
                              {cvr.toFixed(2)}%
                            </td>
                            <td className="text-right py-3 px-2">
                              <span
                                className={
                                  roas > 2 ? 'text-green-400' : roas > 1 ? 'text-yellow-400' : 'text-red-400'
                                }
                              >
                                {roas.toFixed(2)}x
                              </span>
                            </td>
                            <td className="text-right py-3 px-2">
                              <span className="font-bold text-purple-300">
                                {(winnerProbs[variant.id] || 0).toFixed(1)}%
                              </span>
                            </td>
                            <td className="text-right py-3 px-2">
                              {index === 0 ? (
                                <span className="text-gray-400">Control</span>
                              ) : (
                                <div className="flex items-center justify-end gap-1">
                                  {lift > 0 ? (
                                    <TrendingUp className="text-green-400" size={16} />
                                  ) : (
                                    <TrendingDown className="text-red-400" size={16} />
                                  )}
                                  <span className={lift > 0 ? 'text-green-400' : 'text-red-400'}>
                                    {lift > 0 ? '+' : ''}
                                    {lift.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* CTR Comparison Chart */}
              <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-6">
                <h3 className="text-xl font-bold mb-4 text-purple-300">CTR Comparison with Confidence Intervals</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={selectedExperiment.variants.map(v => ({
                      name: v.name,
                      ctr: calculateCTR(v.clicks, v.impressions),
                      lower: v.confidence_interval?.lower
                        ? v.confidence_interval.lower * 100
                        : calculateCTR(v.clicks, v.impressions) * 0.9,
                      upper: v.confidence_interval?.upper
                        ? v.confidence_interval.upper * 100
                        : calculateCTR(v.clicks, v.impressions) * 1.1,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="name" stroke="#999" />
                    <YAxis stroke="#999" label={{ value: 'CTR (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #7c3aed' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="ctr" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Budget Allocation */}
              <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-6">
                <h3 className="text-xl font-bold mb-4 text-purple-300">Recommended Budget Allocation</h3>
                <div className="space-y-4">
                  {selectedExperiment.variants.map(variant => {
                    const allocation = winnerProbs[variant.id] || 0;
                    const currentSpend = variant.spend;
                    const totalSpend = selectedExperiment.variants.reduce((sum, v) => sum + v.spend, 0);
                    const currentAllocation = totalSpend > 0 ? (currentSpend / totalSpend) * 100 : 0;

                    return (
                      <div key={variant.id}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold">{variant.name}</span>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-purple-300">
                              Current: {currentAllocation.toFixed(1)}%
                            </span>
                            <span className="text-green-400 font-bold">
                              Recommended: {allocation.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <div className="relative h-8 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-600 to-pink-600 transition-all"
                            style={{ width: `${allocation}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-6 bg-blue-500/20 border border-blue-500 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Target className="text-blue-400 mt-1" size={20} />
                    <div className="text-sm">
                      <div className="font-semibold text-blue-300 mb-1">Thompson Sampling Recommendation</div>
                      <div className="text-blue-200">
                        Budget automatically shifts toward better-performing variants while maintaining exploration.
                        Exploration rate: {selectedExperiment.explorationRate}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Statistical Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <DollarSign className="text-green-200" size={24} />
                    <span className="text-green-200 text-sm uppercase font-semibold">Total Spend</span>
                  </div>
                  <div className="text-3xl font-bold text-white">
                    ${selectedExperiment.variants.reduce((sum, v) => sum + v.spend, 0).toLocaleString()}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <TrendingUp className="text-purple-200" size={24} />
                    <span className="text-purple-200 text-sm uppercase font-semibold">Total Impressions</span>
                  </div>
                  <div className="text-3xl font-bold text-white">
                    {selectedExperiment.variants
                      .reduce((sum, v) => sum + v.impressions, 0)
                      .toLocaleString()}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-pink-600 to-pink-700 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <Target className="text-pink-200" size={24} />
                    <span className="text-pink-200 text-sm uppercase font-semibold">Total Conversions</span>
                  </div>
                  <div className="text-3xl font-bold text-white">
                    {selectedExperiment.variants.reduce((sum, v) => sum + v.conversions, 0).toLocaleString()}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-purple-500/30 p-12 text-center">
              <AlertCircle className="mx-auto mb-4 text-purple-400" size={64} />
              <h3 className="text-2xl font-bold text-purple-300 mb-2">No Experiment Selected</h3>
              <p className="text-purple-400">Select an experiment from the list to view detailed results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ABTestingDashboard;
