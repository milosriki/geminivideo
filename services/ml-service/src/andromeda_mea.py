"""
ANDROMEDA MEA (Meta-Evolutionary Algorithm)
Advanced multi-objective evolutionary optimization for ad performance prediction

MATHEMATICAL FOUNDATIONS:
=======================

1. Multi-Objective Optimization:
   - Minimize: -CTR, -ROAS, -Engagement (convert to minimization problem)
   - Pareto Frontier: Set of non-dominated solutions
   - Dominated: Solution A dominates B if A is better in all objectives

2. Evolutionary Algorithm:
   - Population-based search with genetic operators
   - Selection: Tournament + Pareto ranking
   - Crossover: Simulated Binary Crossover (SBX)
   - Mutation: Polynomial mutation
   - Elitism: Preserve best solutions

3. Meta-Learning:
   - Transfer knowledge from historical campaigns
   - Adaptive hyperparameter tuning
   - Campaign similarity matching

4. Fitness Functions:
   F1(θ) = -predicted_CTR(θ)
   F2(θ) = -predicted_ROAS(θ)
   F3(θ) = -predicted_Engagement(θ)

   Where θ = model parameters to optimize

5. Pareto Dominance:
   A ≻ B iff ∀i: fi(A) ≤ fi(B) and ∃j: fj(A) < fj(B)

6. Crowding Distance (diversity metric):
   CD(i) = Σ(j=1 to M) [f_j(i+1) - f_j(i-1)] / [f_j^max - f_j^min]
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Callable, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime
import copy

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """
    Individual solution in the evolutionary population

    Attributes:
        genes: Parameter vector (weights, hyperparameters, etc.)
        objectives: Multi-objective fitness values [CTR, ROAS, Engagement]
        rank: Pareto rank (0 = best non-dominated front)
        crowding_distance: Diversity metric for selection
        metadata: Additional information
    """
    genes: np.ndarray
    objectives: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.0]))
    rank: int = -1
    crowding_distance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def dominates(self, other: 'Individual') -> bool:
        """
        Check if this individual dominates another

        Args:
            other: Another individual to compare

        Returns:
            True if self dominates other
        """
        # For minimization: self dominates other if all objectives are ≤ and at least one is <
        better_or_equal = np.all(self.objectives <= other.objectives)
        strictly_better = np.any(self.objectives < other.objectives)
        return better_or_equal and strictly_better

    def __lt__(self, other: 'Individual') -> bool:
        """Comparison for sorting (by rank then crowding distance)"""
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.crowding_distance > other.crowding_distance  # Higher crowding distance is better


@dataclass
class MEAConfig:
    """Configuration for Andromeda MEA"""
    population_size: int = 100
    num_generations: int = 50
    num_objectives: int = 3  # CTR, ROAS, Engagement
    crossover_prob: float = 0.9
    mutation_prob: float = 0.1
    mutation_eta: float = 20.0  # Polynomial mutation parameter
    crossover_eta: float = 20.0  # SBX parameter
    tournament_size: int = 2
    elite_size: int = 10
    gene_bounds: Tuple[float, float] = (-5.0, 5.0)
    gene_dimension: int = 50  # Number of parameters to optimize
    random_seed: int = 42


class AndromedaMEA:
    """
    Andromeda Meta-Evolutionary Algorithm (MEA)

    Multi-objective evolutionary optimization for ad performance prediction.
    Optimizes CTR, ROAS, and Engagement simultaneously using Pareto frontier.

    Key Features:
    - NSGA-II inspired algorithm with Pareto ranking
    - Multi-objective optimization (CTR + ROAS + Engagement)
    - Meta-learning from historical campaigns
    - Population-based training with elitism
    - Adaptive hyperparameter tuning
    """

    def __init__(self, config: Optional[MEAConfig] = None):
        """
        Initialize Andromeda MEA

        Args:
            config: MEA configuration parameters
        """
        self.config = config or MEAConfig()
        self.population: List[Individual] = []
        self.pareto_front: List[Individual] = []
        self.generation = 0
        self.history: List[Dict[str, Any]] = []

        # Set random seed for reproducibility
        np.random.seed(self.config.random_seed)

        # Fitness evaluation functions (set by user)
        self.fitness_functions: List[Callable] = []

        # Meta-learning cache
        self.historical_campaigns: List[Dict[str, Any]] = []
        self.campaign_embeddings: Optional[np.ndarray] = None

        logger.info(f"Andromeda MEA initialized with population={self.config.population_size}, generations={self.config.num_generations}")

    def set_fitness_functions(self, functions: List[Callable[[np.ndarray], float]]):
        """
        Set fitness evaluation functions

        Args:
            functions: List of 3 functions for [CTR, ROAS, Engagement] prediction
                      Each function takes genes (np.ndarray) and returns a score
        """
        if len(functions) != self.config.num_objectives:
            raise ValueError(f"Expected {self.config.num_objectives} fitness functions, got {len(functions)}")
        self.fitness_functions = functions
        logger.info("Fitness functions configured")

    def initialize_population(self, prior_knowledge: Optional[List[np.ndarray]] = None):
        """
        Initialize population with random individuals

        Args:
            prior_knowledge: Optional list of gene vectors from previous runs or meta-learning
        """
        self.population = []

        # Add individuals from prior knowledge
        if prior_knowledge:
            for genes in prior_knowledge[:self.config.elite_size]:
                individual = Individual(genes=genes.copy())
                self.population.append(individual)
                logger.debug(f"Added prior knowledge individual")

        # Fill rest with random individuals
        remaining = self.config.population_size - len(self.population)
        for _ in range(remaining):
            genes = np.random.uniform(
                self.config.gene_bounds[0],
                self.config.gene_bounds[1],
                size=self.config.gene_dimension
            )
            individual = Individual(genes=genes)
            self.population.append(individual)

        logger.info(f"Population initialized with {len(self.population)} individuals")

    def evaluate_population(self):
        """Evaluate fitness for all individuals in population"""
        if not self.fitness_functions:
            raise ValueError("Fitness functions not set. Call set_fitness_functions() first.")

        for individual in self.population:
            objectives = []
            for fitness_fn in self.fitness_functions:
                try:
                    # Fitness functions return positive scores (higher is better)
                    # Convert to minimization problem
                    score = fitness_fn(individual.genes)
                    objectives.append(-score)  # Negate for minimization
                except Exception as e:
                    logger.error(f"Error evaluating fitness: {e}")
                    objectives.append(1e6)  # Penalty for invalid solutions

            individual.objectives = np.array(objectives)

        logger.debug(f"Evaluated {len(self.population)} individuals")

    def fast_non_dominated_sort(self) -> List[List[Individual]]:
        """
        Fast non-dominated sorting (NSGA-II)

        Returns:
            List of fronts, where front[0] is the Pareto front
        """
        fronts = [[]]

        # For each individual, calculate domination
        domination_count = {}  # Number of solutions that dominate this one
        dominated_solutions = {}  # Solutions this one dominates

        for p in self.population:
            domination_count[id(p)] = 0
            dominated_solutions[id(p)] = []

            for q in self.population:
                if p is q:
                    continue

                if p.dominates(q):
                    dominated_solutions[id(p)].append(q)
                elif q.dominates(p):
                    domination_count[id(p)] += 1

            # If no one dominates this solution, it's in the first front
            if domination_count[id(p)] == 0:
                p.rank = 0
                fronts[0].append(p)

        # Generate subsequent fronts
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in dominated_solutions[id(p)]:
                    domination_count[id(q)] -= 1
                    if domination_count[id(q)] == 0:
                        q.rank = i + 1
                        next_front.append(q)
            i += 1
            if next_front:
                fronts.append(next_front)

        # Remove empty last front
        if fronts and not fronts[-1]:
            fronts.pop()

        logger.debug(f"Non-dominated sorting complete: {len(fronts)} fronts")
        return fronts

    def calculate_crowding_distance(self, front: List[Individual]):
        """
        Calculate crowding distance for individuals in a front

        Args:
            front: List of individuals in the same front
        """
        if len(front) == 0:
            return

        # Initialize crowding distance
        for individual in front:
            individual.crowding_distance = 0.0

        # For each objective
        for m in range(self.config.num_objectives):
            # Sort by objective m
            front.sort(key=lambda x: x.objectives[m])

            # Boundary points get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')

            # Calculate range
            obj_range = front[-1].objectives[m] - front[0].objectives[m]
            if obj_range == 0:
                continue

            # Calculate crowding distance for interior points
            for i in range(1, len(front) - 1):
                distance = (front[i+1].objectives[m] - front[i-1].objectives[m]) / obj_range
                front[i].crowding_distance += distance

    def tournament_selection(self) -> Individual:
        """
        Tournament selection based on rank and crowding distance

        Returns:
            Selected individual
        """
        # Select random individuals for tournament
        candidates = np.random.choice(
            self.population,
            size=self.config.tournament_size,
            replace=False
        )

        # Return best based on rank and crowding distance
        return min(candidates)

    def simulated_binary_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """
        Simulated Binary Crossover (SBX)

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Two offspring
        """
        if np.random.rand() > self.config.crossover_prob:
            # No crossover, return copies of parents
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        genes1 = parent1.genes.copy()
        genes2 = parent2.genes.copy()

        offspring1_genes = np.zeros_like(genes1)
        offspring2_genes = np.zeros_like(genes2)

        for i in range(len(genes1)):
            if np.random.rand() <= 0.5:
                # Perform SBX
                if abs(genes1[i] - genes2[i]) > 1e-6:
                    # Calculate beta
                    u = np.random.rand()
                    if u <= 0.5:
                        beta = (2 * u) ** (1.0 / (self.config.crossover_eta + 1))
                    else:
                        beta = (1.0 / (2 * (1 - u))) ** (1.0 / (self.config.crossover_eta + 1))

                    # Create offspring
                    offspring1_genes[i] = 0.5 * ((genes1[i] + genes2[i]) - beta * abs(genes1[i] - genes2[i]))
                    offspring2_genes[i] = 0.5 * ((genes1[i] + genes2[i]) + beta * abs(genes1[i] - genes2[i]))
                else:
                    offspring1_genes[i] = genes1[i]
                    offspring2_genes[i] = genes2[i]
            else:
                offspring1_genes[i] = genes1[i]
                offspring2_genes[i] = genes2[i]

        # Apply bounds
        offspring1_genes = np.clip(offspring1_genes, self.config.gene_bounds[0], self.config.gene_bounds[1])
        offspring2_genes = np.clip(offspring2_genes, self.config.gene_bounds[0], self.config.gene_bounds[1])

        return Individual(genes=offspring1_genes), Individual(genes=offspring2_genes)

    def polynomial_mutation(self, individual: Individual) -> Individual:
        """
        Polynomial mutation

        Args:
            individual: Individual to mutate

        Returns:
            Mutated individual
        """
        mutated_genes = individual.genes.copy()

        for i in range(len(mutated_genes)):
            if np.random.rand() <= self.config.mutation_prob:
                # Perform polynomial mutation
                gene_value = mutated_genes[i]
                delta_l = (gene_value - self.config.gene_bounds[0]) / (self.config.gene_bounds[1] - self.config.gene_bounds[0])
                delta_r = (self.config.gene_bounds[1] - gene_value) / (self.config.gene_bounds[1] - self.config.gene_bounds[0])

                u = np.random.rand()
                if u < 0.5:
                    delta = (2 * u) ** (1.0 / (self.config.mutation_eta + 1)) - 1
                    mutated_genes[i] = gene_value + delta * delta_l * (self.config.gene_bounds[1] - self.config.gene_bounds[0])
                else:
                    delta = 1 - (2 * (1 - u)) ** (1.0 / (self.config.mutation_eta + 1))
                    mutated_genes[i] = gene_value + delta * delta_r * (self.config.gene_bounds[1] - self.config.gene_bounds[0])

                # Apply bounds
                mutated_genes[i] = np.clip(mutated_genes[i], self.config.gene_bounds[0], self.config.gene_bounds[1])

        return Individual(genes=mutated_genes)

    def evolve_generation(self):
        """Evolve population for one generation"""
        # Create offspring population
        offspring = []

        while len(offspring) < self.config.population_size:
            # Selection
            parent1 = self.tournament_selection()
            parent2 = self.tournament_selection()

            # Crossover
            child1, child2 = self.simulated_binary_crossover(parent1, parent2)

            # Mutation
            child1 = self.polynomial_mutation(child1)
            child2 = self.polynomial_mutation(child2)

            offspring.extend([child1, child2])

        # Trim to exact population size
        offspring = offspring[:self.config.population_size]

        # Evaluate offspring
        old_population = self.population
        self.population = offspring
        self.evaluate_population()

        # Combine parent and offspring populations
        self.population = old_population + offspring

        # Non-dominated sorting
        fronts = self.fast_non_dominated_sort()

        # Calculate crowding distance for each front
        for front in fronts:
            self.calculate_crowding_distance(front)

        # Select next generation
        next_population = []
        for front in fronts:
            if len(next_population) + len(front) <= self.config.population_size:
                next_population.extend(front)
            else:
                # Sort by crowding distance and fill remaining slots
                front.sort(key=lambda x: x.crowding_distance, reverse=True)
                remaining = self.config.population_size - len(next_population)
                next_population.extend(front[:remaining])
                break

        self.population = next_population

        # Update Pareto front
        self.pareto_front = fronts[0] if fronts else []

        self.generation += 1
        logger.debug(f"Generation {self.generation} complete, Pareto front size: {len(self.pareto_front)}")

    def optimize(self,
                 num_generations: Optional[int] = None,
                 callback: Optional[Callable[[int, List[Individual]], None]] = None) -> List[Individual]:
        """
        Run evolutionary optimization

        Args:
            num_generations: Number of generations to run (uses config if None)
            callback: Optional callback function called after each generation

        Returns:
            Final Pareto front
        """
        num_gen = num_generations or self.config.num_generations

        logger.info(f"Starting optimization for {num_gen} generations")
        start_time = datetime.utcnow()

        # Initialize if not already done
        if not self.population:
            self.initialize_population()
            self.evaluate_population()
            fronts = self.fast_non_dominated_sort()
            for front in fronts:
                self.calculate_crowding_distance(front)
            self.pareto_front = fronts[0] if fronts else []

        # Evolution loop
        for gen in range(num_gen):
            self.evolve_generation()

            # Track history
            self.history.append({
                'generation': self.generation,
                'pareto_front_size': len(self.pareto_front),
                'best_ctr': -min([ind.objectives[0] for ind in self.pareto_front]) if self.pareto_front else 0,
                'best_roas': -min([ind.objectives[1] for ind in self.pareto_front]) if self.pareto_front else 0,
                'best_engagement': -min([ind.objectives[2] for ind in self.pareto_front]) if self.pareto_front else 0,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Callback
            if callback:
                callback(self.generation, self.pareto_front)

            # Log progress every 10 generations
            if (gen + 1) % 10 == 0:
                logger.info(f"Generation {self.generation}/{num_gen}: Pareto front = {len(self.pareto_front)} solutions")

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Optimization complete in {elapsed:.2f}s, Final Pareto front: {len(self.pareto_front)} solutions")

        return self.pareto_front

    def get_best_solution(self, weights: Optional[np.ndarray] = None) -> Individual:
        """
        Get best solution from Pareto front using weighted sum

        Args:
            weights: Weights for each objective [w_ctr, w_roas, w_engagement]
                    Default: [0.33, 0.33, 0.34] (equal weight)

        Returns:
            Best individual according to weighted sum
        """
        if not self.pareto_front:
            raise ValueError("No Pareto front available. Run optimize() first.")

        if weights is None:
            weights = np.array([0.33, 0.33, 0.34])

        weights = weights / np.sum(weights)  # Normalize

        # Calculate weighted sum for each solution (remember: objectives are negated)
        best_individual = None
        best_score = float('inf')

        for individual in self.pareto_front:
            # Convert back to positive scores and calculate weighted sum
            positive_objectives = -individual.objectives
            weighted_score = np.dot(weights, positive_objectives)

            if weighted_score > best_score or best_individual is None:
                best_score = weighted_score
                best_individual = individual

        return best_individual

    def add_historical_campaign(self, campaign_data: Dict[str, Any]):
        """
        Add historical campaign data for meta-learning

        Args:
            campaign_data: Dictionary with campaign features and performance
        """
        self.historical_campaigns.append(campaign_data)
        logger.debug(f"Added historical campaign, total: {len(self.historical_campaigns)}")

    def extract_meta_features(self) -> np.ndarray:
        """
        Extract meta-features from historical campaigns for warm-starting

        Returns:
            Array of meta-features to use as prior knowledge
        """
        if not self.historical_campaigns:
            return np.array([])

        # Extract top-performing campaign parameters
        meta_features = []

        for campaign in sorted(self.historical_campaigns,
                              key=lambda x: x.get('roas', 0),
                              reverse=True)[:self.config.elite_size]:

            # Extract relevant features as genes
            features = campaign.get('features', {})
            genes = np.zeros(self.config.gene_dimension)

            # Map campaign features to gene space
            # This is a simplified mapping - in production, use learned embeddings
            for i, (key, value) in enumerate(list(features.items())[:self.config.gene_dimension]):
                if isinstance(value, (int, float)):
                    genes[i] = float(value)

            meta_features.append(genes)

        logger.info(f"Extracted meta-features from {len(meta_features)} campaigns")
        return np.array(meta_features)

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization results

        Returns:
            Dictionary with optimization statistics
        """
        if not self.pareto_front:
            return {'error': 'No optimization results available'}

        # Extract objectives from Pareto front (convert back to positive)
        objectives = np.array([[-obj for obj in ind.objectives] for ind in self.pareto_front])

        return {
            'num_generations': self.generation,
            'pareto_front_size': len(self.pareto_front),
            'best_ctr': float(np.max(objectives[:, 0])),
            'best_roas': float(np.max(objectives[:, 1])),
            'best_engagement': float(np.max(objectives[:, 2])),
            'avg_ctr': float(np.mean(objectives[:, 0])),
            'avg_roas': float(np.mean(objectives[:, 1])),
            'avg_engagement': float(np.mean(objectives[:, 2])),
            'hypervolume': self._calculate_hypervolume(objectives),
            'convergence_history': self.history
        }

    def _calculate_hypervolume(self, objectives: np.ndarray) -> float:
        """
        Calculate hypervolume indicator (quality metric for Pareto front)

        Args:
            objectives: Array of objective values (positive scores)

        Returns:
            Hypervolume value
        """
        if len(objectives) == 0:
            return 0.0

        # Simplified hypervolume calculation (2D projection)
        # In production, use pygmo or similar for accurate hypervolume
        reference_point = np.zeros(self.config.num_objectives)

        # Calculate dominated hypervolume (simplified)
        volume = 0.0
        for obj in objectives:
            # Product of distances from reference point
            distances = np.maximum(obj - reference_point, 0)
            volume += np.prod(distances)

        return float(volume)
