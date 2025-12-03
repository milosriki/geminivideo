import React, { useState, useEffect, useRef } from 'react';
import './ABTestingDashboard.css';

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
  alpha: number; // Beta distribution param (successes + 1)
  beta: number;  // Beta distribution param (failures + 1)
}

interface Experiment {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed';
  variants: Variant[];
  startDate: Date;
  endDate?: Date;
  totalBudget: number;
  explorationRate: number;
}

interface PullHistory {
  timestamp: Date;
  variantId: string;
  reward: number;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Beta function approximation
const betaFunction = (a: number, b: number): number => {
  return (gamma(a) * gamma(b)) / gamma(a + b);
};

// Gamma function approximation (Stirling's approximation)
const gamma = (z: number): number => {
  if (z < 0.5) {
    return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
  }
  z -= 1;
  const g = 7;
  const C = [
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7
  ];

  let x = C[0];
  for (let i = 1; i < g + 2; i++) {
    x += C[i] / (z + i);
  }

  const t = z + g + 0.5;
  return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
};

// Beta distribution PDF
const betaPDF = (x: number, alpha: number, beta: number): number => {
  if (x <= 0 || x >= 1) return 0;
  return (Math.pow(x, alpha - 1) * Math.pow(1 - x, beta - 1)) / betaFunction(alpha, beta);
};

// Calculate statistical significance (Z-test for proportions)
const calculateSignificance = (v1: Variant, v2: Variant): { pValue: number; significant: boolean } => {
  const p1 = v1.clicks / (v1.impressions || 1);
  const p2 = v2.clicks / (v2.impressions || 1);
  const n1 = v1.impressions;
  const n2 = v2.impressions;

  if (n1 === 0 || n2 === 0) return { pValue: 1, significant: false };

  const pPool = (v1.clicks + v2.clicks) / (n1 + n2);
  const se = Math.sqrt(pPool * (1 - pPool) * (1/n1 + 1/n2));

  if (se === 0) return { pValue: 1, significant: false };

  const z = (p1 - p2) / se;
  const pValue = 2 * (1 - normalCDF(Math.abs(z)));

  return { pValue, significant: pValue < 0.05 };
};

// Normal CDF approximation
const normalCDF = (x: number): number => {
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989423 * Math.exp(-x * x / 2);
  const prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  return x > 0 ? 1 - prob : prob;
};

// Calculate lift percentage
const calculateLift = (control: Variant, variant: Variant): number => {
  const controlCTR = control.clicks / (control.impressions || 1);
  const variantCTR = variant.clicks / (variant.impressions || 1);
  return ((variantCTR - controlCTR) / controlCTR) * 100;
};

// Thompson Sampling - sample from beta distribution
const sampleBeta = (alpha: number, beta: number): number => {
  // Using rejection sampling method
  let x, y;
  do {
    x = Math.random();
    y = Math.random() * Math.max(betaPDF(0.5, alpha, beta), 0.1);
  } while (y > betaPDF(x, alpha, beta));
  return x;
};

// Calculate winner probability using Thompson Sampling
const calculateWinnerProbability = (variants: Variant[], samples: number = 10000): number[] => {
  const wins = new Array(variants.length).fill(0);

  for (let i = 0; i < samples; i++) {
    const samples = variants.map(v => sampleBeta(v.alpha, v.beta));
    const maxIndex = samples.indexOf(Math.max(...samples));
    wins[maxIndex]++;
  }

  return wins.map(w => (w / samples) * 100);
};

// Export to CSV
const exportToCSV = (experiment: Experiment) => {
  const headers = ['Variant', 'Impressions', 'Clicks', 'CTR', 'Conversions', 'Spend', 'Revenue', 'ROAS'];
  const rows = experiment.variants.map(v => [
    v.name,
    v.impressions,
    v.clicks,
    ((v.clicks / (v.impressions || 1)) * 100).toFixed(2) + '%',
    v.conversions,
    '$' + v.spend.toFixed(2),
    '$' + v.revenue.toFixed(2),
    (v.revenue / (v.spend || 1)).toFixed(2)
  ]);

  const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${experiment.name.replace(/\s+/g, '_')}_${Date.now()}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
};

// ============================================================================
// MOCK DATA
// ============================================================================

const generateMockExperiments = (): Experiment[] => {
  return [
    {
      id: 'exp-1',
      name: 'Thumbnail A/B Test - Gaming Video',
      status: 'running',
      startDate: new Date(Date.now() - 86400000 * 3), // 3 days ago
      totalBudget: 5000,
      explorationRate: 20,
      variants: [
        {
          id: 'var-1a',
          name: 'Control (Original)',
          impressions: 12450,
          clicks: 1245,
          conversions: 124,
          spend: 1250,
          revenue: 1870,
          alpha: 1246, // clicks + 1
          beta: 11206, // (impressions - clicks) + 1
        },
        {
          id: 'var-1b',
          name: 'Variant A (Action Shot)',
          impressions: 11830,
          clicks: 1420,
          conversions: 156,
          spend: 1180,
          revenue: 2340,
          alpha: 1421,
          beta: 10411,
        },
        {
          id: 'var-1c',
          name: 'Variant B (Close-up)',
          impressions: 10920,
          clicks: 1310,
          conversions: 142,
          spend: 1090,
          revenue: 2130,
          alpha: 1311,
          beta: 9611,
        },
      ],
    },
    {
      id: 'exp-2',
      name: 'CTA Button Text Test',
      status: 'running',
      startDate: new Date(Date.now() - 86400000 * 7), // 7 days ago
      totalBudget: 3000,
      explorationRate: 15,
      variants: [
        {
          id: 'var-2a',
          name: 'Control (Watch Now)',
          impressions: 8450,
          clicks: 845,
          conversions: 84,
          spend: 845,
          revenue: 1268,
          alpha: 846,
          beta: 7606,
        },
        {
          id: 'var-2b',
          name: 'Variant (Learn More)',
          impressions: 9120,
          clicks: 1095,
          conversions: 109,
          spend: 912,
          revenue: 1638,
          alpha: 1096,
          beta: 8026,
        },
      ],
    },
    {
      id: 'exp-3',
      name: 'Video Length Test - Tutorial',
      status: 'paused',
      startDate: new Date(Date.now() - 86400000 * 5),
      totalBudget: 2000,
      explorationRate: 25,
      variants: [
        {
          id: 'var-3a',
          name: '5 min version',
          impressions: 4500,
          clicks: 405,
          conversions: 40,
          spend: 450,
          revenue: 600,
          alpha: 406,
          beta: 4096,
        },
        {
          id: 'var-3b',
          name: '10 min version',
          impressions: 4200,
          clicks: 462,
          conversions: 46,
          spend: 420,
          revenue: 690,
          alpha: 463,
          beta: 3739,
        },
      ],
    },
    {
      id: 'exp-4',
      name: 'Opening Hook Test',
      status: 'completed',
      startDate: new Date(Date.now() - 86400000 * 14),
      endDate: new Date(Date.now() - 86400000 * 1),
      totalBudget: 4000,
      explorationRate: 10,
      variants: [
        {
          id: 'var-4a',
          name: 'Control (Standard)',
          impressions: 15600,
          clicks: 1560,
          conversions: 156,
          spend: 1560,
          revenue: 2340,
          alpha: 1561,
          beta: 14041,
        },
        {
          id: 'var-4b',
          name: 'Variant (Question)',
          impressions: 16200,
          clicks: 1782,
          conversions: 178,
          spend: 1620,
          revenue: 2670,
          alpha: 1783,
          beta: 14419,
        },
      ],
    },
  ];
};

// ============================================================================
// CHART COMPONENTS
// ============================================================================

interface BetaDistributionChartProps {
  variants: Variant[];
  width?: number;
  height?: number;
}

const BetaDistributionChart: React.FC<BetaDistributionChartProps> = ({
  variants,
  width = 600,
  height = 300
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Chart padding
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Draw axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Conversion Rate', width / 2, height - 5);
    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Probability Density', 0, 0);
    ctx.restore();

    // X-axis labels
    ctx.textAlign = 'center';
    for (let i = 0; i <= 10; i++) {
      const x = padding.left + (i / 10) * chartWidth;
      const label = (i / 10).toFixed(1);
      ctx.fillText(label, x, height - padding.bottom + 20);

      // Grid lines
      ctx.strokeStyle = '#e0e0e0';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, padding.top);
      ctx.lineTo(x, height - padding.bottom);
      ctx.stroke();
    }

    // Calculate max density for scaling
    let maxDensity = 0;
    variants.forEach(variant => {
      for (let x = 0.01; x < 1; x += 0.01) {
        const density = betaPDF(x, variant.alpha, variant.beta);
        maxDensity = Math.max(maxDensity, density);
      }
    });

    // Draw beta distributions
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];

    variants.forEach((variant, index) => {
      ctx.strokeStyle = colors[index % colors.length];
      ctx.lineWidth = 2;
      ctx.beginPath();

      let firstPoint = true;
      for (let x = 0.01; x < 1; x += 0.005) {
        const density = betaPDF(x, variant.alpha, variant.beta);
        const canvasX = padding.left + x * chartWidth;
        const canvasY = height - padding.bottom - (density / maxDensity) * chartHeight;

        if (firstPoint) {
          ctx.moveTo(canvasX, canvasY);
          firstPoint = false;
        } else {
          ctx.lineTo(canvasX, canvasY);
        }
      }

      ctx.stroke();

      // Legend
      const legendY = padding.top + index * 20;
      ctx.fillStyle = colors[index % colors.length];
      ctx.fillRect(width - 150, legendY, 15, 15);
      ctx.fillStyle = '#333';
      ctx.textAlign = 'left';
      ctx.fillText(variant.name, width - 130, legendY + 12);
    });

  }, [variants, width, height]);

  return <canvas ref={canvasRef} width={width} height={height} />;
};

interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  width?: number;
  height?: number;
  valueFormatter?: (value: number) => string;
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  width = 400,
  height = 250,
  valueFormatter = (v) => v.toFixed(1) + '%'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 20, bottom: 60, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const maxValue = Math.max(...data.map(d => d.value), 1);
    const barWidth = chartWidth / data.length - 10;

    // Draw axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Draw bars
    data.forEach((item, index) => {
      const barHeight = (item.value / maxValue) * chartHeight;
      const x = padding.left + index * (chartWidth / data.length) + 10;
      const y = height - padding.bottom - barHeight;

      ctx.fillStyle = item.color || '#36A2EB';
      ctx.fillRect(x, y, barWidth, barHeight);

      // Value label
      ctx.fillStyle = '#333';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(valueFormatter(item.value), x + barWidth / 2, y - 5);

      // X-axis label
      ctx.save();
      ctx.translate(x + barWidth / 2, height - padding.bottom + 15);
      ctx.rotate(-Math.PI / 4);
      ctx.textAlign = 'right';
      ctx.fillText(item.label, 0, 0);
      ctx.restore();
    });

  }, [data, width, height, valueFormatter]);

  return <canvas ref={canvasRef} width={width} height={height} />;
};

interface LineChartProps {
  data: { x: number; y: number }[][];
  labels: string[];
  width?: number;
  height?: number;
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  labels,
  width = 600,
  height = 250
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Find max values
    const allPoints = data.flat();
    const maxX = Math.max(...allPoints.map(p => p.x), 1);
    const maxY = Math.max(...allPoints.map(p => p.y), 1);

    // Draw axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();

    // Draw lines
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'];

    data.forEach((series, seriesIndex) => {
      if (series.length === 0) return;

      ctx.strokeStyle = colors[seriesIndex % colors.length];
      ctx.lineWidth = 2;
      ctx.beginPath();

      series.forEach((point, index) => {
        const x = padding.left + (point.x / maxX) * chartWidth;
        const y = height - padding.bottom - (point.y / maxY) * chartHeight;

        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();

      // Legend
      const legendY = padding.top + seriesIndex * 20;
      ctx.fillStyle = colors[seriesIndex % colors.length];
      ctx.fillRect(width - 150, legendY, 15, 15);
      ctx.fillStyle = '#333';
      ctx.font = '12px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(labels[seriesIndex], width - 130, legendY + 12);
    });

  }, [data, labels, width, height]);

  return <canvas ref={canvasRef} width={width} height={height} />;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const ABTestingDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'running' | 'paused' | 'completed'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [explorationRate, setExplorationRate] = useState(20);
  const [autoShift, setAutoShift] = useState(true);

  // Initialize with mock data
  useEffect(() => {
    const mockData = generateMockExperiments();
    setExperiments(mockData);
    setSelectedExperiment(mockData[0]);
  }, []);

  // Simulate real-time updates (polling every 5 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      setExperiments(prev => prev.map(exp => {
        if (exp.status !== 'running') return exp;

        return {
          ...exp,
          variants: exp.variants.map(variant => {
            // Simulate new data
            const newImpressions = Math.floor(Math.random() * 10) + 1;
            const newClicks = Math.floor(Math.random() * 3);
            const newConversions = Math.random() > 0.7 ? 1 : 0;

            return {
              ...variant,
              impressions: variant.impressions + newImpressions,
              clicks: variant.clicks + newClicks,
              conversions: variant.conversions + newConversions,
              alpha: variant.alpha + newClicks,
              beta: variant.beta + (newImpressions - newClicks),
              spend: variant.spend + newImpressions * 0.1,
              revenue: variant.revenue + newConversions * 15,
            };
          }),
        };
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Filter experiments
  const filteredExperiments = experiments.filter(exp =>
    statusFilter === 'all' || exp.status === statusFilter
  );

  // Calculate winner probabilities for selected experiment
  const winnerProbabilities = selectedExperiment
    ? calculateWinnerProbability(selectedExperiment.variants)
    : [];

  const currentWinnerIndex = winnerProbabilities.indexOf(Math.max(...winnerProbabilities));

  // Budget allocation based on Thompson Sampling
  const calculateBudgetAllocation = (experiment: Experiment) => {
    const probs = calculateWinnerProbability(experiment.variants);
    const explorationBonus = experiment.explorationRate / 100;

    return experiment.variants.map((variant, index) => {
      const baseAllocation = probs[index] / 100;
      const exploration = explorationBonus / experiment.variants.length;
      const allocation = baseAllocation * (1 - explorationBonus) + exploration;
      return allocation * 100;
    });
  };

  const budgetAllocations = selectedExperiment
    ? calculateBudgetAllocation(selectedExperiment)
    : [];

  // Handlers
  const handleCreateExperiment = () => {
    setShowCreateModal(true);
  };

  const handlePauseResume = (experimentId: string) => {
    setExperiments(prev => prev.map(exp => {
      if (exp.id === experimentId) {
        return {
          ...exp,
          status: exp.status === 'running' ? 'paused' : 'running'
        };
      }
      return exp;
    }));
  };

  const handleDelete = (experimentId: string) => {
    if (window.confirm('Are you sure you want to delete this experiment?')) {
      setExperiments(prev => prev.filter(exp => exp.id !== experimentId));
      if (selectedExperiment?.id === experimentId) {
        setSelectedExperiment(experiments[0] || null);
      }
    }
  };

  const handleExportCSV = () => {
    if (selectedExperiment) {
      exportToCSV(selectedExperiment);
    }
  };

  const handleApplyBudgetChanges = () => {
    if (selectedExperiment) {
      setExperiments(prev => prev.map(exp => {
        if (exp.id === selectedExperiment.id) {
          return {
            ...exp,
            explorationRate: explorationRate
          };
        }
        return exp;
      }));
      alert('Budget allocation updated successfully!');
    }
  };

  return (
    <div className="ab-testing-dashboard">
      <header className="dashboard-header">
        <h1>A/B Testing & Thompson Sampling Dashboard</h1>
        <div className="header-actions">
          <button className="btn-primary" onClick={handleCreateExperiment}>
            + Create New Experiment
          </button>
          <button className="btn-secondary" onClick={handleExportCSV}>
            Export to CSV
          </button>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* LEFT COLUMN: Experiments List */}
        <section className="experiments-list">
          <div className="section-header">
            <h2>Experiments</h2>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="status-filter"
            >
              <option value="all">All Status</option>
              <option value="running">Running</option>
              <option value="paused">Paused</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div className="experiments-table-wrapper">
            <table className="experiments-table">
              <thead>
                <tr>
                  <th>Experiment Name</th>
                  <th>Status</th>
                  <th>Variants</th>
                  <th>Start Date</th>
                  <th>Impressions</th>
                  <th>Winner</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredExperiments.map(exp => {
                  const totalImpressions = exp.variants.reduce((sum, v) => sum + v.impressions, 0);
                  const winnerProbs = calculateWinnerProbability(exp.variants);
                  const winnerIndex = winnerProbs.indexOf(Math.max(...winnerProbs));

                  return (
                    <tr
                      key={exp.id}
                      className={selectedExperiment?.id === exp.id ? 'selected' : ''}
                      onClick={() => setSelectedExperiment(exp)}
                    >
                      <td className="exp-name">{exp.name}</td>
                      <td>
                        <span className={`status-badge status-${exp.status}`}>
                          {exp.status}
                        </span>
                      </td>
                      <td>{exp.variants.length}</td>
                      <td>{exp.startDate.toLocaleDateString()}</td>
                      <td>{totalImpressions.toLocaleString()}</td>
                      <td className="winner-cell">
                        {exp.variants[winnerIndex]?.name}
                        <span className="winner-prob">
                          ({winnerProbs[winnerIndex].toFixed(1)}%)
                        </span>
                      </td>
                      <td className="actions-cell">
                        <button
                          className="btn-icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePauseResume(exp.id);
                          }}
                          title={exp.status === 'running' ? 'Pause' : 'Resume'}
                        >
                          {exp.status === 'running' ? '⏸' : '▶'}
                        </button>
                        <button
                          className="btn-icon btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(exp.id);
                          }}
                          title="Delete"
                        >
                          🗑
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* RIGHT COLUMN: Details */}
        {selectedExperiment && (
          <div className="experiment-details">
            {/* Thompson Sampling Visualizer */}
            <section className="thompson-sampling">
              <h2>Thompson Sampling Visualizer</h2>

              <div className="ts-grid">
                <div className="beta-chart">
                  <h3>Beta Distribution - Conversion Rate Posterior</h3>
                  <BetaDistributionChart variants={selectedExperiment.variants} />
                  <p className="chart-description">
                    Shows the probability distribution of conversion rates for each variant.
                    Taller peaks indicate more confidence in the estimate.
                  </p>
                </div>

                <div className="arm-probabilities">
                  <h3>Arm Selection Probabilities</h3>
                  <BarChart
                    data={selectedExperiment.variants.map((v, i) => ({
                      label: v.name,
                      value: winnerProbabilities[i],
                      color: i === currentWinnerIndex ? '#4CAF50' : '#36A2EB'
                    }))}
                  />
                  <p className="chart-description">
                    Probability of each variant being the best based on 10,000 samples.
                  </p>
                </div>
              </div>

              <div className="recommendation-panel">
                <h3>Recommendation</h3>
                <div className="recommendation-content">
                  <div className="recommendation-winner">
                    <span className="label">Current Best Performer:</span>
                    <span className="value winner">
                      {selectedExperiment.variants[currentWinnerIndex]?.name}
                    </span>
                    <span className="confidence">
                      {winnerProbabilities[currentWinnerIndex]?.toFixed(1)}% confidence
                    </span>
                  </div>

                  {winnerProbabilities[currentWinnerIndex] > 95 ? (
                    <div className="recommendation-action high-confidence">
                      <strong>High Confidence:</strong> Consider ending the experiment and
                      rolling out the winner to 100% of traffic.
                    </div>
                  ) : winnerProbabilities[currentWinnerIndex] > 80 ? (
                    <div className="recommendation-action medium-confidence">
                      <strong>Moderate Confidence:</strong> Continue testing but start
                      allocating more budget to the leading variant.
                    </div>
                  ) : (
                    <div className="recommendation-action low-confidence">
                      <strong>Low Confidence:</strong> Continue exploring all variants.
                      No clear winner yet.
                    </div>
                  )}

                  <div className="exploration-balance">
                    <span className="label">Exploration Rate:</span>
                    <span className="value">{selectedExperiment.explorationRate}%</span>
                    <div className="balance-bar">
                      <div
                        className="exploit"
                        style={{ width: `${100 - selectedExperiment.explorationRate}%` }}
                      >
                        Exploit {100 - selectedExperiment.explorationRate}%
                      </div>
                      <div
                        className="explore"
                        style={{ width: `${selectedExperiment.explorationRate}%` }}
                      >
                        Explore {selectedExperiment.explorationRate}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Variant Comparison */}
            <section className="variant-comparison">
              <h2>Variant Comparison</h2>

              <div className="comparison-table-wrapper">
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Variant</th>
                      <th>Impressions</th>
                      <th>Clicks</th>
                      <th>CTR</th>
                      <th>Conversions</th>
                      <th>CVR</th>
                      <th>Spend</th>
                      <th>Revenue</th>
                      <th>ROAS</th>
                      <th>Winner Prob</th>
                      <th>Lift</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedExperiment.variants.map((variant, index) => {
                      const ctr = (variant.clicks / (variant.impressions || 1)) * 100;
                      const cvr = (variant.conversions / (variant.clicks || 1)) * 100;
                      const roas = variant.revenue / (variant.spend || 1);
                      const lift = index === 0 ? 0 : calculateLift(selectedExperiment.variants[0], variant);
                      const isWinner = index === currentWinnerIndex;

                      return (
                        <tr key={variant.id} className={isWinner ? 'winner-row' : ''}>
                          <td className="variant-name">
                            {variant.name}
                            {isWinner && <span className="winner-badge">👑 Winner</span>}
                          </td>
                          <td>{variant.impressions.toLocaleString()}</td>
                          <td>{variant.clicks.toLocaleString()}</td>
                          <td>{ctr.toFixed(2)}%</td>
                          <td>{variant.conversions}</td>
                          <td>{cvr.toFixed(2)}%</td>
                          <td>${variant.spend.toFixed(2)}</td>
                          <td>${variant.revenue.toFixed(2)}</td>
                          <td className={roas > 2 ? 'positive' : roas > 1 ? 'neutral' : 'negative'}>
                            {roas.toFixed(2)}x
                          </td>
                          <td className="winner-prob-cell">
                            <div className="prob-bar-container">
                              <div
                                className="prob-bar"
                                style={{
                                  width: `${winnerProbabilities[index]}%`,
                                  backgroundColor: isWinner ? '#4CAF50' : '#36A2EB'
                                }}
                              />
                              <span className="prob-text">
                                {winnerProbabilities[index]?.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className={lift > 0 ? 'positive' : lift < 0 ? 'negative' : ''}>
                            {index === 0 ? 'Control' : `${lift > 0 ? '+' : ''}${lift.toFixed(1)}%`}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {selectedExperiment.variants.length === 2 && (
                <div className="statistical-significance">
                  {(() => {
                    const { pValue, significant } = calculateSignificance(
                      selectedExperiment.variants[0],
                      selectedExperiment.variants[1]
                    );
                    return (
                      <div className={`significance-indicator ${significant ? 'significant' : 'not-significant'}`}>
                        <span className="label">Statistical Significance:</span>
                        <span className="value">
                          {significant ? '✓ Significant' : '✗ Not Significant'}
                        </span>
                        <span className="p-value">
                          (p-value: {pValue.toFixed(4)})
                        </span>
                      </div>
                    );
                  })()}
                </div>
              )}
            </section>

            {/* Budget Optimizer */}
            <section className="budget-optimizer">
              <h2>Budget Optimizer</h2>

              <div className="budget-grid">
                <div className="current-allocation">
                  <h3>Current Allocation</h3>
                  <div className="allocation-bars">
                    {selectedExperiment.variants.map((variant, index) => {
                      const currentAlloc = variant.spend /
                        selectedExperiment.variants.reduce((sum, v) => sum + v.spend, 0) * 100;

                      return (
                        <div key={variant.id} className="allocation-item">
                          <span className="variant-label">{variant.name}</span>
                          <div className="allocation-bar-container">
                            <div
                              className="allocation-bar current"
                              style={{ width: `${currentAlloc}%` }}
                            />
                            <span className="allocation-value">{currentAlloc.toFixed(1)}%</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="recommended-allocation">
                  <h3>Recommended Allocation</h3>
                  <div className="allocation-bars">
                    {selectedExperiment.variants.map((variant, index) => {
                      return (
                        <div key={variant.id} className="allocation-item">
                          <span className="variant-label">{variant.name}</span>
                          <div className="allocation-bar-container">
                            <div
                              className="allocation-bar recommended"
                              style={{ width: `${budgetAllocations[index]}%` }}
                            />
                            <span className="allocation-value">
                              {budgetAllocations[index]?.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="budget-controls">
                <div className="control-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={autoShift}
                      onChange={(e) => setAutoShift(e.target.checked)}
                    />
                    Enable Auto-Shift Budget
                  </label>
                  <span className="help-text">
                    Automatically adjust budget allocation based on Thompson Sampling
                  </span>
                </div>

                <div className="control-group">
                  <label>
                    Exploration Rate: {explorationRate}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={explorationRate}
                    onChange={(e) => setExplorationRate(parseInt(e.target.value))}
                    className="exploration-slider"
                  />
                  <div className="slider-labels">
                    <span>Exploit (0%)</span>
                    <span>Balanced (50%)</span>
                    <span>Explore (100%)</span>
                  </div>
                  <span className="help-text">
                    Higher values allocate more budget to exploration (testing all variants).
                    Lower values exploit the current winner more aggressively.
                  </span>
                </div>

                <button
                  className="btn-primary btn-apply"
                  onClick={handleApplyBudgetChanges}
                >
                  Apply Budget Changes
                </button>
              </div>
            </section>
          </div>
        )}
      </div>

      {/* Create Experiment Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Experiment</h2>
            <form onSubmit={(e) => {
              e.preventDefault();
              // Implementation would be here
              setShowCreateModal(false);
            }}>
              <div className="form-group">
                <label>Experiment Name</label>
                <input type="text" placeholder="e.g., Thumbnail Test - Product Video" />
              </div>

              <div className="form-group">
                <label>Total Budget</label>
                <input type="number" placeholder="5000" />
              </div>

              <div className="form-group">
                <label>Exploration Rate (%)</label>
                <input type="number" min="0" max="100" placeholder="20" />
              </div>

              <div className="form-group">
                <label>Number of Variants</label>
                <input type="number" min="2" max="10" placeholder="2" />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Experiment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ABTestingDashboard;
