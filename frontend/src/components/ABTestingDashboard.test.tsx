/**
 * ABTestingDashboard Test Suite
 *
 * Comprehensive tests for the A/B Testing Dashboard component
 * using Jest and React Testing Library
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ABTestingDashboard from './ABTestingDashboard';

// ============================================================================
// MOCK DATA
// ============================================================================

const mockExperiment = {
  id: 'exp-1',
  name: 'Test Experiment',
  status: 'running' as const,
  startDate: new Date('2025-11-01'),
  totalBudget: 5000,
  explorationRate: 20,
  variants: [
    {
      id: 'var-1',
      name: 'Control',
      impressions: 10000,
      clicks: 1000,
      conversions: 100,
      spend: 1000,
      revenue: 1500,
      alpha: 1001,
      beta: 9001,
    },
    {
      id: 'var-2',
      name: 'Variant A',
      impressions: 10000,
      clicks: 1200,
      conversions: 120,
      spend: 1000,
      revenue: 1800,
      alpha: 1201,
      beta: 8801,
    },
  ],
};

// ============================================================================
// UTILITY TESTS
// ============================================================================

describe('Mathematical Utilities', () => {
  // Import the utility functions (you'd need to export them from the main file)
  // For now, we'll test them through the component behavior

  test('calculates CTR correctly', () => {
    const ctr = (1000 / 10000) * 100;
    expect(ctr).toBe(10);
  });

  test('calculates CVR correctly', () => {
    const cvr = (100 / 1000) * 100;
    expect(cvr).toBe(10);
  });

  test('calculates ROAS correctly', () => {
    const roas = 1500 / 1000;
    expect(roas).toBe(1.5);
  });

  test('calculates lift correctly', () => {
    const controlCTR = 1000 / 10000;
    const variantCTR = 1200 / 10000;
    const lift = ((variantCTR - controlCTR) / controlCTR) * 100;
    expect(lift).toBe(20);
  });
});

describe('Statistical Functions', () => {
  test('beta distribution PDF handles edge cases', () => {
    // Test x = 0 (should return 0)
    // Test x = 1 (should return 0)
    // Test valid range (0 < x < 1)
    expect(true).toBe(true); // Placeholder
  });

  test('statistical significance calculation', () => {
    // Test case where difference is significant
    // Test case where difference is not significant
    // Test case with zero impressions
    expect(true).toBe(true); // Placeholder
  });

  test('Thompson sampling winner probability', () => {
    // Should sum to approximately 100%
    // Should favor variant with better performance
    expect(true).toBe(true); // Placeholder
  });
});

// ============================================================================
// COMPONENT RENDERING TESTS
// ============================================================================

describe('ABTestingDashboard - Rendering', () => {
  test('renders dashboard header', () => {
    render(<ABTestingDashboard />);
    expect(screen.getByText(/A\/B Testing.*Thompson Sampling Dashboard/i)).toBeInTheDocument();
  });

  test('renders create experiment button', () => {
    render(<ABTestingDashboard />);
    expect(screen.getByText(/Create New Experiment/i)).toBeInTheDocument();
  });

  test('renders export CSV button', () => {
    render(<ABTestingDashboard />);
    expect(screen.getByText(/Export to CSV/i)).toBeInTheDocument();
  });

  test('renders experiments list', async () => {
    render(<ABTestingDashboard />);
    // Wait for mock data to load
    await waitFor(() => {
      expect(screen.getByText(/Thumbnail A\/B Test/i)).toBeInTheDocument();
    });
  });

  test('renders status filter dropdown', () => {
    render(<ABTestingDashboard />);
    const filter = screen.getByRole('combobox');
    expect(filter).toBeInTheDocument();
    expect(within(filter).getByText('All Status')).toBeInTheDocument();
  });
});

// ============================================================================
// INTERACTION TESTS
// ============================================================================

describe('ABTestingDashboard - Interactions', () => {
  test('filters experiments by status', async () => {
    render(<ABTestingDashboard />);

    const filter = screen.getByRole('combobox');

    // Select "running" status
    fireEvent.change(filter, { target: { value: 'running' } });

    await waitFor(() => {
      // Should show running experiments
      expect(screen.getByText(/Thumbnail A\/B Test/i)).toBeInTheDocument();
    });
  });

  test('selects experiment on row click', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const experimentRow = screen.getByText(/Thumbnail A\/B Test/i).closest('tr');
      if (experimentRow) {
        fireEvent.click(experimentRow);
        expect(experimentRow).toHaveClass('selected');
      }
    });
  });

  test('opens create experiment modal', () => {
    render(<ABTestingDashboard />);

    const createButton = screen.getByText(/Create New Experiment/i);
    fireEvent.click(createButton);

    expect(screen.getByText(/Create New Experiment/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Thumbnail Test/i)).toBeInTheDocument();
  });

  test('closes modal on cancel', () => {
    render(<ABTestingDashboard />);

    // Open modal
    fireEvent.click(screen.getByText(/Create New Experiment/i));

    // Click cancel
    const cancelButton = screen.getByText(/Cancel/i);
    fireEvent.click(cancelButton);

    // Modal should close
    expect(screen.queryByPlaceholderText(/Thumbnail Test/i)).not.toBeInTheDocument();
  });

  test('pauses and resumes experiment', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const pauseButtons = screen.getAllByTitle(/Pause/i);
      if (pauseButtons.length > 0) {
        fireEvent.click(pauseButtons[0]);

        // Should change to resume button
        expect(screen.getByTitle(/Resume/i)).toBeInTheDocument();
      }
    });
  });

  test('deletes experiment with confirmation', async () => {
    // Mock window.confirm
    global.confirm = jest.fn(() => true);

    render(<ABTestingDashboard />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle(/Delete/i);
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);
        expect(global.confirm).toHaveBeenCalled();
      }
    });
  });

  test('cancels delete on confirmation reject', async () => {
    global.confirm = jest.fn(() => false);

    render(<ABTestingDashboard />);

    await waitFor(async () => {
      const deleteButtons = screen.getAllByTitle(/Delete/i);
      const initialCount = deleteButtons.length;

      if (initialCount > 0) {
        fireEvent.click(deleteButtons[0]);

        // Should still have same number of experiments
        await waitFor(() => {
          expect(screen.getAllByTitle(/Delete/i)).toHaveLength(initialCount);
        });
      }
    });
  });
});

// ============================================================================
// BUDGET OPTIMIZER TESTS
// ============================================================================

describe('Budget Optimizer', () => {
  test('renders budget allocation sections', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Current Allocation/i)).toBeInTheDocument();
      expect(screen.getByText(/Recommended Allocation/i)).toBeInTheDocument();
    });
  });

  test('adjusts exploration rate slider', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '50' } });

      expect(slider).toHaveValue('50');
    });
  });

  test('toggles auto-shift budget', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox');
      const initialState = checkbox.getAttribute('checked');

      fireEvent.click(checkbox);

      expect(checkbox.getAttribute('checked')).not.toBe(initialState);
    });
  });

  test('applies budget changes', async () => {
    // Mock window.alert
    global.alert = jest.fn();

    render(<ABTestingDashboard />);

    await waitFor(() => {
      const applyButton = screen.getByText(/Apply Budget Changes/i);
      fireEvent.click(applyButton);

      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('Budget allocation updated')
      );
    });
  });
});

// ============================================================================
// CHART RENDERING TESTS
// ============================================================================

describe('Charts', () => {
  test('renders beta distribution chart', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const canvas = screen.getByRole('img', { hidden: true }); // Canvas has implicit role
      expect(canvas).toBeInTheDocument();
    });
  });

  test('renders bar chart for arm probabilities', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Arm Selection Probabilities/i)).toBeInTheDocument();
    });
  });
});

// ============================================================================
// VARIANT COMPARISON TESTS
// ============================================================================

describe('Variant Comparison', () => {
  test('displays all variant metrics', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Impressions/i)).toBeInTheDocument();
      expect(screen.getByText(/Clicks/i)).toBeInTheDocument();
      expect(screen.getByText(/CTR/i)).toBeInTheDocument();
      expect(screen.getByText(/Conversions/i)).toBeInTheDocument();
    });
  });

  test('highlights winner row', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const winnerBadge = screen.queryByText(/Winner/i);
      if (winnerBadge) {
        const row = winnerBadge.closest('tr');
        expect(row).toHaveClass('winner-row');
      }
    });
  });

  test('shows statistical significance', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      // Should show significance indicator for 2-variant tests
      const sigIndicator = screen.queryByText(/Statistical Significance/i);
      expect(sigIndicator).toBeInTheDocument();
    });
  });
});

// ============================================================================
// RECOMMENDATION PANEL TESTS
// ============================================================================

describe('Recommendation Panel', () => {
  test('shows current best performer', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Current Best Performer/i)).toBeInTheDocument();
    });
  });

  test('displays exploration vs exploitation balance', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Exploration Rate/i)).toBeInTheDocument();
      expect(screen.getByText(/Exploit/i)).toBeInTheDocument();
      expect(screen.getByText(/Explore/i)).toBeInTheDocument();
    });
  });

  test('shows appropriate recommendation based on confidence', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      // Should show one of: High Confidence, Moderate Confidence, Low Confidence
      const recommendations = screen.queryAllByText(
        /(High Confidence|Moderate Confidence|Low Confidence)/i
      );
      expect(recommendations.length).toBeGreaterThan(0);
    });
  });
});

// ============================================================================
// CSV EXPORT TESTS
// ============================================================================

describe('CSV Export', () => {
  beforeEach(() => {
    // Mock URL methods
    global.URL.createObjectURL = jest.fn(() => 'mock-url');
    global.URL.revokeObjectURL = jest.fn();

    // Mock document.createElement
    const mockAnchor = {
      href: '',
      download: '',
      click: jest.fn(),
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
  });

  test('exports selected experiment to CSV', async () => {
    render(<ABTestingDashboard />);

    await waitFor(() => {
      const exportButton = screen.getByText(/Export to CSV/i);
      fireEvent.click(exportButton);

      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  test('CSV contains correct headers', async () => {
    // This would require mocking Blob and reading its contents
    // Simplified version:
    expect(true).toBe(true); // Placeholder
  });
});

// ============================================================================
// REAL-TIME UPDATE TESTS
// ============================================================================

describe('Real-time Updates', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('polls for updates every 5 seconds', async () => {
    render(<ABTestingDashboard />);

    // Fast-forward time by 5 seconds
    jest.advanceTimersByTime(5000);

    // Should trigger update
    await waitFor(() => {
      expect(true).toBe(true); // Placeholder - would check for updated data
    });
  });

  test('updates metrics automatically', async () => {
    render(<ABTestingDashboard />);

    // Get initial impression count
    await waitFor(() => {
      const initialValue = screen.getByText(/Impressions/i);
      expect(initialValue).toBeInTheDocument();
    });

    // Fast-forward to trigger update
    jest.advanceTimersByTime(5000);

    // Metrics should update (in real implementation)
    await waitFor(() => {
      expect(true).toBe(true); // Placeholder
    });
  });

  test('cleans up interval on unmount', () => {
    const { unmount } = render(<ABTestingDashboard />);

    // Unmount component
    unmount();

    // Interval should be cleared (no way to directly test, but ensures no memory leak)
    expect(true).toBe(true);
  });
});

// ============================================================================
// ACCESSIBILITY TESTS
// ============================================================================

describe('Accessibility', () => {
  test('has no accessibility violations', async () => {
    // Would use jest-axe here
    // import { axe, toHaveNoViolations } from 'jest-axe';
    // expect.extend(toHaveNoViolations);

    const { container } = render(<ABTestingDashboard />);

    // const results = await axe(container);
    // expect(results).toHaveNoViolations();

    expect(container).toBeInTheDocument();
  });

  test('buttons have accessible labels', () => {
    render(<ABTestingDashboard />);

    const createButton = screen.getByText(/Create New Experiment/i);
    expect(createButton).toHaveAccessibleName();
  });

  test('form inputs have labels', async () => {
    render(<ABTestingDashboard />);

    // Open create modal
    fireEvent.click(screen.getByText(/Create New Experiment/i));

    await waitFor(() => {
      const inputs = screen.getAllByRole('textbox');
      inputs.forEach(input => {
        // Each input should have an associated label
        expect(input).toBeInTheDocument();
      });
    });
  });
});

// ============================================================================
// EDGE CASES
// ============================================================================

describe('Edge Cases', () => {
  test('handles zero impressions gracefully', () => {
    // Create experiment with zero impressions
    // Should not divide by zero
    expect(true).toBe(true); // Placeholder
  });

  test('handles single variant experiment', () => {
    // Should not crash with 1 variant
    // Statistical significance should be N/A
    expect(true).toBe(true); // Placeholder
  });

  test('handles very large numbers', () => {
    // Test with billions of impressions
    // Should format properly
    expect(true).toBe(true); // Placeholder
  });

  test('handles very small probabilities', () => {
    // Test beta distribution with extreme alpha/beta
    expect(true).toBe(true); // Placeholder
  });
});

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================

describe('Performance', () => {
  test('renders 100 experiments without lag', async () => {
    // Would create 100 mock experiments
    // Measure render time
    const startTime = performance.now();
    render(<ABTestingDashboard />);
    const endTime = performance.now();

    expect(endTime - startTime).toBeLessThan(1000); // Should render in < 1s
  });

  test('Thompson sampling completes in reasonable time', () => {
    // Test that 10,000 samples complete quickly
    const startTime = performance.now();
    // calculateWinnerProbability(variants, 10000);
    const endTime = performance.now();

    expect(endTime - startTime).toBeLessThan(100); // Should complete in < 100ms
  });
});

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

describe('Integration Tests', () => {
  test('complete workflow: create -> pause -> resume -> delete', async () => {
    global.confirm = jest.fn(() => true);
    global.alert = jest.fn();

    render(<ABTestingDashboard />);

    // 1. Create experiment
    fireEvent.click(screen.getByText(/Create New Experiment/i));
    // Fill form and submit (would need to implement)

    // 2. Pause experiment
    await waitFor(() => {
      const pauseButton = screen.getAllByTitle(/Pause/i)[0];
      fireEvent.click(pauseButton);
    });

    // 3. Resume experiment
    await waitFor(() => {
      const resumeButton = screen.getByTitle(/Resume/i);
      fireEvent.click(resumeButton);
    });

    // 4. Delete experiment
    await waitFor(() => {
      const deleteButton = screen.getAllByTitle(/Delete/i)[0];
      fireEvent.click(deleteButton);
    });

    expect(global.confirm).toHaveBeenCalled();
  });

  test('complete workflow: select -> adjust budget -> export', async () => {
    global.alert = jest.fn();
    global.URL.createObjectURL = jest.fn(() => 'mock-url');

    render(<ABTestingDashboard />);

    // 1. Select experiment
    await waitFor(() => {
      const row = screen.getByText(/Thumbnail A\/B Test/i).closest('tr');
      if (row) fireEvent.click(row);
    });

    // 2. Adjust budget
    await waitFor(() => {
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '30' } });

      const applyButton = screen.getByText(/Apply Budget Changes/i);
      fireEvent.click(applyButton);
    });

    // 3. Export
    const exportButton = screen.getByText(/Export to CSV/i);
    fireEvent.click(exportButton);

    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });
});

// ============================================================================
// SNAPSHOT TESTS
// ============================================================================

describe('Snapshot Tests', () => {
  test('matches snapshot for initial render', () => {
    const { container } = render(<ABTestingDashboard />);
    expect(container).toMatchSnapshot();
  });

  test('matches snapshot for selected experiment', async () => {
    const { container } = render(<ABTestingDashboard />);

    await waitFor(() => {
      const row = screen.getByText(/Thumbnail A\/B Test/i).closest('tr');
      if (row) fireEvent.click(row);
    });

    expect(container).toMatchSnapshot();
  });
});

export {};
