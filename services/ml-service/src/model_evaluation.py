"""
Champion-Challenger Model Evaluation

Compares models on simulated ROAS and promotes challenger
only if >5% better than champion.

Created: 2025-12-07
"""

import numpy as np
from typing import Dict, Tuple, Optional
import logging
import joblib
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Database connection (would use actual connection in production)
DATABASE_URL = os.environ.get("DATABASE_URL", "")


def evaluate_champion_vs_challenger(
    champion_path: str,
    challenger_path: str,
    test_data: Dict,
) -> Dict:
    """
    Compare models on simulated ROAS.
    Promote challenger only if >5% better.

    Args:
        champion_path: Path to champion model file
        challenger_path: Path to challenger model file
        test_data: Dictionary with 'features', 'revenue', 'spend' arrays

    Returns:
        Dict with evaluation results and promotion decision
    """
    try:
        # Load models
        logger.info(f"Loading champion model from {champion_path}")
        champion = joblib.load(champion_path)

        logger.info(f"Loading challenger model from {challenger_path}")
        challenger = joblib.load(challenger_path)

        # Simulate ROAS for both models
        logger.info("Simulating ROAS for champion model")
        champion_roas = simulate_roas(champion, test_data)

        logger.info("Simulating ROAS for challenger model")
        challenger_roas = simulate_roas(challenger, test_data)

        # Calculate improvement
        improvement = (challenger_roas - champion_roas) / champion_roas * 100

        # Promotion threshold: 5% improvement
        should_promote = improvement > 5.0

        result = {
            "champion_roas": round(champion_roas, 4),
            "challenger_roas": round(challenger_roas, 4),
            "improvement_pct": round(improvement, 2),
            "promoted": should_promote,
            "evaluation_date": datetime.utcnow().isoformat(),
            "test_samples": len(test_data["features"]),
        }

        if should_promote:
            logger.info(
                f"Challenger outperforms champion by {improvement:.2f}% - PROMOTING"
            )
            promote_to_champion(challenger_path)
            result["promotion_timestamp"] = datetime.utcnow().isoformat()
        else:
            logger.info(
                f"Challenger improvement {improvement:.2f}% below 5% threshold - keeping champion"
            )

        return result

    except Exception as e:
        logger.error(f"Error evaluating models: {e}", exc_info=True)
        raise


def simulate_roas(model, test_data: Dict) -> float:
    """
    Simulate ROAS based on model predictions.

    Args:
        model: Trained model with predict() method
        test_data: Dict with 'features', 'revenue', 'spend' arrays

    Returns:
        Simulated ROAS value
    """
    features = np.array(test_data["features"])
    revenue = np.array(test_data["revenue"])
    spend = np.array(test_data["spend"])

    # Get model predictions (e.g., click probability)
    predictions = model.predict(features)

    # Allocate budget to predicted winners (above threshold)
    threshold = 0.5
    allocated_revenue = revenue * (predictions > threshold)
    total_revenue = allocated_revenue.sum()

    # Calculate ROAS
    total_spend = spend.sum()
    if total_spend == 0:
        return 0.0

    roas = total_revenue / total_spend
    return float(roas)


def promote_to_champion(model_path: str) -> bool:
    """
    Update model registry to promote challenger to champion.

    Args:
        model_path: Path to the model to promote

    Returns:
        True if promotion successful, False otherwise
    """
    try:
        if not DATABASE_URL:
            logger.warning("DATABASE_URL not set - skipping database update")
            return False

        # Import database connection
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(DATABASE_URL)

            with engine.connect() as conn:
                # Archive current champion
                conn.execute(
                    text("""
                    UPDATE model_registry 
                    SET stage = 'archived',
                        archived_at = NOW()
                    WHERE stage = 'champion' 
                      AND model_name = 'battle_hardened_sampler'
                """)
                )
                conn.commit()

                # Promote challenger to champion
                conn.execute(
                    text("""
                    UPDATE model_registry 
                    SET stage = 'champion',
                        promoted_at = NOW()
                    WHERE artifact_path = :model_path
                """),
                    {"model_path": model_path},
                )
                conn.commit()

                logger.info(f"Successfully promoted {model_path} to champion")
                return True

        except ImportError:
            logger.warning("SQLAlchemy not available - cannot update database")
            return False

    except Exception as e:
        logger.error(f"Error promoting model: {e}", exc_info=True)
        return False


def load_test_data(test_data_path: str) -> Dict:
    """
    Load test data from file.

    Args:
        test_data_path: Path to test data file (numpy, pickle, etc.)

    Returns:
        Dict with features, revenue, spend arrays
    """
    try:
        # Load from numpy file
        if test_data_path.endswith(".npz"):
            data = np.load(test_data_path)
            return {
                "features": data["features"],
                "revenue": data["revenue"],
                "spend": data["spend"],
            }
        # Load from pickle
        elif test_data_path.endswith(".pkl"):
            import pickle

            with open(test_data_path, "rb") as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported test data format: {test_data_path}")

    except Exception as e:
        logger.error(f"Error loading test data: {e}", exc_info=True)
        raise


# CLI interface for running evaluations
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate champion vs challenger models")
    parser.add_argument("--champion", required=True, help="Path to champion model")
    parser.add_argument("--challenger", required=True, help="Path to challenger model")
    parser.add_argument("--test-data", required=True, help="Path to test data file")

    args = parser.parse_args()

    # Load test data
    test_data = load_test_data(args.test_data)

    # Run evaluation
    result = evaluate_champion_vs_challenger(
        champion_path=args.champion,
        challenger_path=args.challenger,
        test_data=test_data,
    )

    # Print results
    print("\n" + "=" * 60)
    print("CHAMPION-CHALLENGER EVALUATION RESULTS")
    print("=" * 60)
    print(f"Champion ROAS:    {result['champion_roas']:.4f}")
    print(f"Challenger ROAS:  {result['challenger_roas']:.4f}")
    print(f"Improvement:      {result['improvement_pct']:.2f}%")
    print(f"Decision:         {'PROMOTE' if result['promoted'] else 'KEEP CHAMPION'}")
    print(f"Test Samples:     {result['test_samples']}")
    print(f"Evaluation Date:  {result['evaluation_date']}")
    if result['promoted']:
        print(f"Promoted At:      {result['promotion_timestamp']}")
    print("=" * 60 + "\n")
