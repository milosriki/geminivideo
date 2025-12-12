"""Agent orchestrator for coordinating multiple agents."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from agent.core.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class OrchestrationStrategy(str, Enum):
    """Orchestration strategies."""

    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"  # All at once
    PIPELINE = "pipeline"  # Based on dependencies
    ADAPTIVE = "adaptive"  # Dynamic based on results


@dataclass
class AgentTask:
    """Task for an agent."""

    agent: BaseAgent
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    timeout: Optional[float] = None


@dataclass
class OrchestrationResult:
    """Result from orchestration."""

    success: bool
    results: Dict[str, AgentResult] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    total_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class AgentOrchestrator:
    """Orchestrates multiple agents with dependency management."""

    def __init__(
        self,
        strategy: OrchestrationStrategy = OrchestrationStrategy.ADAPTIVE,
        max_concurrent: int = 10,
    ):
        self.strategy = strategy
        self.max_concurrent = max_concurrent
        self.agents: Dict[str, BaseAgent] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def register_agent(self, agent: BaseAgent, dependencies: Optional[List[str]] = None):
        """Register an agent with optional dependencies."""
        self.agents[agent.name] = agent
        self.dependency_graph[agent.name] = set(dependencies or [])

    async def orchestrate(
        self,
        tasks: List[AgentTask],
        strategy: Optional[OrchestrationStrategy] = None,
    ) -> OrchestrationResult:
        """Orchestrate multiple agent tasks."""
        start_time = datetime.now()
        strategy = strategy or self.strategy

        logger.info(
            f"Orchestrating {len(tasks)} tasks with strategy: {strategy.value}"
        )

        if strategy == OrchestrationStrategy.SEQUENTIAL:
            return await self._orchestrate_sequential(tasks, start_time)
        elif strategy == OrchestrationStrategy.PARALLEL:
            return await self._orchestrate_parallel(tasks, start_time)
        elif strategy == OrchestrationStrategy.PIPELINE:
            return await self._orchestrate_pipeline(tasks, start_time)
        else:  # ADAPTIVE
            return await self._orchestrate_adaptive(tasks, start_time)

    async def _orchestrate_sequential(
        self, tasks: List[AgentTask], start_time: datetime
    ) -> OrchestrationResult:
        """Execute tasks sequentially."""
        results: Dict[str, AgentResult] = {}
        execution_order: List[str] = []
        errors: List[str] = []

        for task in sorted(tasks, key=lambda t: t.priority, reverse=True):
            agent_name = task.agent.name
            execution_order.append(agent_name)

            try:
                # Wait for dependencies
                for dep in task.dependencies:
                    if dep in results and not results[dep].success:
                        raise Exception(f"Dependency {dep} failed")

                # Execute agent
                result = await task.agent.execute(
                    task.input_data,
                    context={dep: results[dep].data for dep in task.dependencies if dep in results},
                )
                results[agent_name] = result

                if not result.success:
                    errors.append(f"{agent_name}: {result.error}")

            except Exception as e:
                logger.error(f"Task {agent_name} failed: {e}")
                results[agent_name] = AgentResult(
                    success=False, error=str(e)
                )
                errors.append(f"{agent_name}: {str(e)}")

        total_time = (datetime.now() - start_time).total_seconds()
        return OrchestrationResult(
            success=len(errors) == 0,
            results=results,
            execution_order=execution_order,
            total_time=total_time,
            errors=errors,
        )

    async def _orchestrate_parallel(
        self, tasks: List[AgentTask], start_time: datetime
    ) -> OrchestrationResult:
        """Execute tasks in parallel."""
        # Create tasks with dependency resolution
        ready_tasks = [t for t in tasks if not t.dependencies]
        pending_tasks = [t for t in tasks if t.dependencies]

        results: Dict[str, AgentResult] = {}
        execution_order: List[str] = []
        errors: List[str] = []

        # Execute ready tasks in parallel
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_task(task: AgentTask):
            async with semaphore:
                agent_name = task.agent.name
                execution_order.append(agent_name)

                try:
                    # Check dependencies
                    for dep in task.dependencies:
                        if dep not in results or not results[dep].success:
                            raise Exception(f"Dependency {dep} not ready")

                    result = await task.agent.execute(
                        task.input_data,
                        context={dep: results[dep].data for dep in task.dependencies if dep in results},
                    )
                    results[agent_name] = result

                    if not result.success:
                        errors.append(f"{agent_name}: {result.error}")

                except Exception as e:
                    logger.error(f"Task {agent_name} failed: {e}")
                    results[agent_name] = AgentResult(
                        success=False, error=str(e)
                    )
                    errors.append(f"{agent_name}: {str(e)}")

        # Execute all ready tasks
        await asyncio.gather(*[execute_task(t) for t in ready_tasks])

        # Execute pending tasks as dependencies become available
        while pending_tasks:
            ready_now = [
                t
                for t in pending_tasks
                if all(dep in results and results[dep].success for dep in t.dependencies)
            ]

            if not ready_now:
                # Deadlock or missing dependencies
                for task in pending_tasks:
                    errors.append(f"{task.agent.name}: Missing dependencies")
                break

            await asyncio.gather(*[execute_task(t) for t in ready_now])
            pending_tasks = [t for t in pending_tasks if t not in ready_now]

        total_time = (datetime.now() - start_time).total_seconds()
        return OrchestrationResult(
            success=len(errors) == 0,
            results=results,
            execution_order=execution_order,
            total_time=total_time,
            errors=errors,
        )

    async def _orchestrate_pipeline(
        self, tasks: List[AgentTask], start_time: datetime
    ) -> OrchestrationResult:
        """Execute tasks in pipeline order based on dependencies."""
        # Topological sort
        execution_order = self._topological_sort(tasks)
        results: Dict[str, AgentResult] = {}
        errors: List[str] = []

        for agent_name in execution_order:
            task = next(t for t in tasks if t.agent.name == agent_name)

            try:
                # Check dependencies
                for dep in task.dependencies:
                    if dep not in results or not results[dep].success:
                        raise Exception(f"Dependency {dep} failed")

                result = await task.agent.execute(
                    task.input_data,
                    context={dep: results[dep].data for dep in task.dependencies if dep in results},
                )
                results[agent_name] = result

                if not result.success:
                    errors.append(f"{agent_name}: {result.error}")

            except Exception as e:
                logger.error(f"Task {agent_name} failed: {e}")
                results[agent_name] = AgentResult(
                    success=False, error=str(e)
                )
                errors.append(f"{agent_name}: {str(e)}")

        total_time = (datetime.now() - start_time).total_seconds()
        return OrchestrationResult(
            success=len(errors) == 0,
            results=results,
            execution_order=execution_order,
            total_time=total_time,
            errors=errors,
        )

    async def _orchestrate_adaptive(
        self, tasks: List[AgentTask], start_time: datetime
    ) -> OrchestrationResult:
        """Adaptive orchestration - dynamically adjust based on results."""
        # Start with parallel execution, adapt based on results
        return await self._orchestrate_parallel(tasks, start_time)

    def _topological_sort(self, tasks: List[AgentTask]) -> List[str]:
        """Topological sort of tasks based on dependencies."""
        # Build graph
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}

        for task in tasks:
            agent_name = task.agent.name
            graph[agent_name] = set(task.dependencies)
            in_degree[agent_name] = len(task.dependencies)

        # Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Update in-degrees
            for other_node, deps in graph.items():
                if node in deps:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)

        return result

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents."""
        return {
            agent_name: agent.get_status()
            for agent_name, agent in self.agents.items()
        }

