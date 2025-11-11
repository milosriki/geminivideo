#!/usr/bin/env python3
"""
Nightly Learning Script
Calibrates scoring weights based on actual performance data
Reads prediction logs and updates shared/config/weights.yaml
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import statistics


def load_prediction_logs(logs_path: Path) -> List[Dict[str, Any]]:
    """Load all prediction log entries"""
    entries = []
    
    if not logs_path.exists():
        print(f"No prediction log found at {logs_path}")
        return entries
    
    with open(logs_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    # Only include entries with actual CTR data
                    if 'actual_ctr' in entry and entry['actual_ctr'] is not None:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
    
    print(f"Loaded {len(entries)} prediction entries with actual performance data")
    return entries


def calculate_performance_metrics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate performance metrics"""
    if not entries:
        return {}
    
    predicted_ctrs = [e['predicted_ctr'] for e in entries]
    actual_ctrs = [e['actual_ctr'] for e in entries]
    
    # Calculate prediction accuracy
    errors = [abs(pred - actual) for pred, actual in zip(predicted_ctrs, actual_ctrs)]
    mae = statistics.mean(errors)  # Mean Absolute Error
    
    # Calculate bias (tendency to over/under-predict)
    bias = statistics.mean([pred - actual for pred, actual in zip(predicted_ctrs, actual_ctrs)])
    
    # Group by predicted band
    band_performance = {}
    for entry in entries:
        band = entry['predicted_band']
        if band not in band_performance:
            band_performance[band] = {'predicted': [], 'actual': []}
        band_performance[band]['predicted'].append(entry['predicted_ctr'])
        band_performance[band]['actual'].append(entry['actual_ctr'])
    
    return {
        'mae': mae,
        'bias': bias,
        'sample_count': len(entries),
        'band_performance': band_performance
    }


def adjust_weights(
    current_weights: Dict[str, Any],
    metrics: Dict[str, Any],
    learning_rate: float = 0.05
) -> Dict[str, Any]:
    """
    Adjust scoring weights based on performance metrics
    Uses gradient descent-like approach to minimize prediction error
    """
    if not metrics or metrics.get('sample_count', 0) < 100:
        print("Insufficient data for weight adjustment (min 100 samples required)")
        return current_weights
    
    adjusted = current_weights.copy()
    mae = metrics['mae']
    bias = metrics['bias']
    
    print(f"\nCurrent Performance:")
    print(f"  MAE: {mae:.4f}")
    print(f"  Bias: {bias:.4f}")
    print(f"  Samples: {metrics['sample_count']}")
    
    # Adjust performance bands based on actual results
    band_performance = metrics.get('band_performance', {})
    
    if 'performance_bands' in adjusted:
        for band, data in band_performance.items():
            if band in adjusted['performance_bands']:
                actual_mean = statistics.mean(data['actual'])
                current_ctr = adjusted['performance_bands'][band]['expected_ctr']
                
                # Adjust expected CTR towards actual performance
                new_ctr = current_ctr + learning_rate * (actual_mean - current_ctr)
                adjusted['performance_bands'][band]['expected_ctr'] = round(new_ctr, 4)
                
                print(f"\nBand '{band}':")
                print(f"  Previous expected CTR: {current_ctr:.4f}")
                print(f"  Actual mean CTR: {actual_mean:.4f}")
                print(f"  New expected CTR: {new_ctr:.4f}")
    
    # If we're consistently over-predicting, reduce weights slightly
    if abs(bias) > 0.01:
        adjustment_factor = 1 - (learning_rate * bias)
        
        for category in ['psychology', 'hooks', 'features']:
            if category in adjusted:
                for key, value in adjusted[category].items():
                    if isinstance(value, (int, float)):
                        adjusted[category][key] = round(value * adjustment_factor, 4)
        
        print(f"\nApplied bias correction factor: {adjustment_factor:.4f}")
    
    return adjusted


def save_weights(weights: Dict[str, Any], weights_path: Path, backup: bool = True):
    """Save updated weights to YAML file with backup"""
    if backup and weights_path.exists():
        backup_path = weights_path.with_suffix('.yaml.bak')
        import shutil
        shutil.copy2(weights_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Add metadata
    weights['last_calibration'] = datetime.utcnow().isoformat()
    weights['version'] = weights.get('version', '1.0.0')
    
    with open(weights_path, 'w') as f:
        f.write("# AI Ad Intelligence Scoring Weights Configuration\n")
        f.write(f"# Last updated: {weights['last_calibration']}\n")
        f.write("# Auto-adjusted by nightly_learning.py based on actual performance\n\n")
        yaml.dump(weights, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nWeights saved to: {weights_path}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Nightly Learning - Weight Calibration")
    print("=" * 60)
    
    # Paths
    base_path = Path(__file__).parent.parent
    logs_path = base_path / 'logs' / 'predictions.jsonl'
    weights_path = base_path / 'shared' / 'config' / 'weights.yaml'
    
    # Load current weights
    print(f"\nLoading weights from: {weights_path}")
    with open(weights_path, 'r') as f:
        current_weights = yaml.safe_load(f)
    
    # Load prediction logs
    entries = load_prediction_logs(logs_path)
    
    if not entries:
        print("\nNo performance data available. Skipping calibration.")
        return
    
    # Calculate metrics
    metrics = calculate_performance_metrics(entries)
    
    # Adjust weights
    learning_rate = current_weights.get('calibration', {}).get('learning_rate', 0.05)
    adjusted_weights = adjust_weights(current_weights, metrics, learning_rate)
    
    # Save updated weights
    save_weights(adjusted_weights, weights_path)
    
    print("\n" + "=" * 60)
    print("Calibration complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
