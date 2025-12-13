"""
Meta AX (Adaptive Experimentation) Integration

Provides Bayesian optimization and adaptive experimentation capabilities using Meta's Ax platform.
Enables intelligent A/B testing, hyperparameter tuning, and multi-objective optimization.
"""

from ax import (
    Experiment,
    SearchSpace,
    RangeParameter,
    ChoiceParameter,
    ParameterType,
    OptimizationConfig,
    Objective,
    OutcomeConstraint,
    ComparisonOp,
)
from ax.service.ax_client import AxClient
from ax.modelbridge.generation_strategy import GenerationStrategy
from ax.modelbridge.registry import Models
import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Meta AX configuration
META_AX_ENABLED = os.getenv("META_AX_ENABLED", "false").lower() == "true"
META_AX_STORAGE_PATH = os.getenv("META_AX_STORAGE_PATH", "/tmp/ax_experiments")

# Ensure storage directory exists
if META_AX_ENABLED:
    os.makedirs(META_AX_STORAGE_PATH, exist_ok=True)
    logger.info(f"Meta AX enabled. Storage path: {META_AX_STORAGE_PATH}")
else:
    logger.warning("Meta AX is disabled")


class AdaptiveExperiment:
    """
    Wrapper for Meta AX adaptive experimentation

    Provides a simplified interface for creating and running Bayesian optimization
    experiments with support for multiple objectives and constraints.
    """

    def __init__(
        self,
        name: str,
        parameters: Dict[str, Dict[str, Any]],
        objective_name: str = "primary_metric",
        minimize: bool = False,
        constraints: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize an adaptive experiment

        Args:
            name: Experiment name
            parameters: Dictionary defining parameter search space
                Format: {
                    "param_name": {
                        "type": "range" or "choice",
                        "min": float (for range),
                        "max": float (for range),
                        "values": list (for choice),
                        "value_type": "float" or "int" or "str"
                    }
                }
            objective_name: Name of the metric to optimize
            minimize: Whether to minimize (True) or maximize (False) the objective
            constraints: List of constraint dictionaries
        """
        self.name = name
        self.objective_name = objective_name
        self.minimize = minimize
        self.created_at = datetime.utcnow().isoformat()

        if not META_AX_ENABLED:
            logger.warning(f"Meta AX is disabled. Experiment '{name}' will not run.")
            self.enabled = False
            return

        self.enabled = True

        # Build search space
        self.search_space = self._build_search_space(parameters)

        # Create experiment
        self.experiment = Experiment(
            name=name,
            search_space=self.search_space,
        )

        # Create optimization config
        objective = Objective(
            metric_name=objective_name,
            minimize=minimize,
        )

        outcome_constraints = []
        if constraints:
            for constraint in constraints:
                outcome_constraints.append(
                    OutcomeConstraint(
                        metric_name=constraint["metric"],
                        op=ComparisonOp.LEQ if constraint.get("less_than") else ComparisonOp.GEQ,
                        bound=constraint["bound"],
                    )
                )

        self.optimization_config = OptimizationConfig(
            objective=objective,
            outcome_constraints=outcome_constraints,
        )

        self.experiment.optimization_config = self.optimization_config

        logger.info(f"Adaptive experiment '{name}' initialized successfully")

    def _build_search_space(self, parameters: Dict[str, Dict[str, Any]]) -> SearchSpace:
        """Build Ax SearchSpace from parameter definitions"""
        ax_parameters = []

        for param_name, param_config in parameters.items():
            param_type = param_config.get("type", "range")
            value_type = param_config.get("value_type", "float")

            # Map value type to Ax ParameterType
            if value_type == "int":
                ax_type = ParameterType.INT
            elif value_type == "float":
                ax_type = ParameterType.FLOAT
            elif value_type == "str":
                ax_type = ParameterType.STRING
            else:
                ax_type = ParameterType.FLOAT

            if param_type == "range":
                ax_parameters.append(
                    RangeParameter(
                        name=param_name,
                        lower=param_config["min"],
                        upper=param_config["max"],
                        parameter_type=ax_type,
                    )
                )
            elif param_type == "choice":
                ax_parameters.append(
                    ChoiceParameter(
                        name=param_name,
                        values=param_config["values"],
                        parameter_type=ax_type,
                    )
                )

        return SearchSpace(parameters=ax_parameters)

    def get_next_trial(self) -> Optional[Dict[str, Any]]:
        """
        Get the next trial parameters to evaluate

        Returns:
            Dictionary of parameter values for the next trial, or None if disabled
        """
        if not self.enabled:
            logger.warning("Experiment is disabled")
            return None

        try:
            trial = self.experiment.new_trial()
            parameters = trial.arm.parameters

            logger.info(f"Generated trial {trial.index} with parameters: {parameters}")
            return {
                "trial_index": trial.index,
                "parameters": parameters,
            }
        except Exception as e:
            logger.error(f"Error generating next trial: {e}")
            raise

    def complete_trial(
        self,
        trial_index: int,
        metrics: Dict[str, float],
    ) -> None:
        """
        Complete a trial with observed metrics

        Args:
            trial_index: Index of the trial to complete
            metrics: Dictionary of metric names to observed values
        """
        if not self.enabled:
            logger.warning("Experiment is disabled")
            return

        try:
            trial = self.experiment.trials[trial_index]

            # Ensure objective metric is present
            if self.objective_name not in metrics:
                raise ValueError(f"Objective metric '{self.objective_name}' not in metrics")

            # Complete the trial with data
            self.experiment.attach_data({
                "trial_index": trial_index,
                "arm_name": trial.arm.name,
                "metrics": metrics,
            })

            trial.mark_completed()

            logger.info(f"Completed trial {trial_index} with metrics: {metrics}")
        except Exception as e:
            logger.error(f"Error completing trial {trial_index}: {e}")
            raise

    def get_best_parameters(self) -> Optional[Dict[str, Any]]:
        """
        Get the best parameters found so far

        Returns:
            Dictionary with best parameters and metrics, or None if no trials completed
        """
        if not self.enabled:
            return None

        try:
            if len(self.experiment.trials) == 0:
                logger.warning("No trials completed yet")
                return None

            # Get best arm from experiment
            best_arm = self.experiment.optimization_config.objective.compute_best_arm(
                self.experiment
            )

            return {
                "parameters": best_arm[0].parameters,
                "metrics": best_arm[1],
            }
        except Exception as e:
            logger.error(f"Error getting best parameters: {e}")
            return None

    def save_experiment(self, filepath: Optional[str] = None) -> str:
        """
        Save experiment state to disk

        Args:
            filepath: Optional custom filepath, defaults to storage path

        Returns:
            Path to saved file
        """
        if not self.enabled:
            logger.warning("Experiment is disabled, nothing to save")
            return ""

        if filepath is None:
            filepath = os.path.join(
                META_AX_STORAGE_PATH,
                f"{self.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )

        try:
            # Save experiment to JSON
            from ax.storage.json_store.save import save_experiment
            save_experiment(self.experiment, filepath)

            logger.info(f"Experiment saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving experiment: {e}")
            raise


class ABTestExperiment:
    """
    Simplified A/B testing wrapper using Meta AX

    Provides an easy interface for running adaptive A/B tests with
    automatic winner selection based on Bayesian optimization.
    """

    def __init__(
        self,
        name: str,
        variants: List[str],
        metric_name: str = "conversion_rate",
        minimize: bool = False,
    ):
        """
        Initialize an A/B test experiment

        Args:
            name: Test name
            variants: List of variant names (e.g., ["control", "variant_a", "variant_b"])
            metric_name: Metric to optimize
            minimize: Whether to minimize the metric (default: maximize)
        """
        self.name = name
        self.variants = variants
        self.metric_name = metric_name

        if not META_AX_ENABLED:
            logger.warning(f"Meta AX is disabled. A/B test '{name}' will not run.")
            self.enabled = False
            return

        self.enabled = True

        # Use AxClient for simplified interface
        self.ax_client = AxClient()

        # Create experiment with variant as a choice parameter
        self.ax_client.create_experiment(
            name=name,
            parameters=[
                {
                    "name": "variant",
                    "type": "choice",
                    "values": variants,
                    "value_type": "str",
                }
            ],
            objectives={metric_name: "minimize" if minimize else "maximize"},
        )

        logger.info(f"A/B test '{name}' initialized with variants: {variants}")

    def get_next_variant(self) -> Optional[str]:
        """Get the next variant to show to a user"""
        if not self.enabled:
            return self.variants[0]  # Default to first variant if disabled

        try:
            parameters, trial_index = self.ax_client.get_next_trial()
            return parameters["variant"]
        except Exception as e:
            logger.error(f"Error getting next variant: {e}")
            return self.variants[0]

    def record_result(self, trial_index: int, metric_value: float) -> None:
        """Record the result for a trial"""
        if not self.enabled:
            return

        try:
            self.ax_client.complete_trial(
                trial_index=trial_index,
                raw_data={self.metric_name: metric_value},
            )
            logger.info(f"Recorded result for trial {trial_index}: {metric_value}")
        except Exception as e:
            logger.error(f"Error recording result: {e}")

    def get_winning_variant(self) -> Optional[Dict[str, Any]]:
        """Get the current winning variant"""
        if not self.enabled:
            return None

        try:
            best_parameters, best_values = self.ax_client.get_best_parameters()
            return {
                "variant": best_parameters["variant"],
                "metric_value": best_values[0][self.metric_name],
            }
        except Exception as e:
            logger.error(f"Error getting winning variant: {e}")
            return None


__all__ = [
    "AdaptiveExperiment",
    "ABTestExperiment",
    "META_AX_ENABLED",
]
