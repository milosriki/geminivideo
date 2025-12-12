"""Base agent class with LangChain integration and error handling."""

from __future__ import annotations

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    RETRYING = "retrying"


class AgentError(Exception):
    """Custom agent error with context."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        error_type: str = "unknown",
        retryable: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.agent_name = agent_name
        self.error_type = error_type
        self.retryable = retryable
        self.context = context or {}


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    retry_count: int = 0


@dataclass
class AgentMemory:
    """Agent memory for learning and context."""

    agent_id: str
    experiences: List[Dict[str, Any]] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """Base agent with LangChain integration, error handling, and learning."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: Optional[BaseChatModel] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_learning: bool = True,
    ):
        self.name = name
        self.description = description
        self.llm = llm or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_learning = enable_learning
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory(agent_id=name)
        self._execution_history: List[Dict[str, Any]] = []

        # Initialize prompt template
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=f"You are {name}, a specialized AI agent. {description}"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="{input}"),
            ]
        )

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Execute agent with error handling and retries."""
        start_time = datetime.now()
        retry_count = 0
        last_error: Optional[Exception] = None

        self.status = AgentStatus.RUNNING

        while retry_count <= self.max_retries:
            try:
                logger.info(f"[{self.name}] Starting execution (attempt {retry_count + 1})")

                # Load context from memory
                memory_context = self._get_memory_context()
                full_context = {**(context or {}), **memory_context}

                # Execute agent logic
                result_data = await self._execute_impl(input_data, full_context)

                # Record success
                execution_time = (datetime.now() - start_time).total_seconds()
                self.status = AgentStatus.SUCCESS

                result = AgentResult(
                    success=True,
                    data=result_data,
                    execution_time=execution_time,
                    retry_count=retry_count,
                )

                # Learn from success
                if self.enable_learning:
                    await self._learn_from_success(input_data, result_data, execution_time)

                logger.info(
                    f"[{self.name}] Execution successful in {execution_time:.2f}s"
                )
                return result

            except AgentError as e:
                last_error = e
                if not e.retryable or retry_count >= self.max_retries:
                    break

                retry_count += 1
                self.status = AgentStatus.RETRYING
                logger.warning(
                    f"[{self.name}] Retryable error (attempt {retry_count}): {e}"
                )

                # Learn from error
                if self.enable_learning:
                    await self._learn_from_error(e, input_data)

                await asyncio.sleep(self.retry_delay * retry_count)

            except Exception as e:
                last_error = e
                logger.error(
                    f"[{self.name}] Unexpected error: {e}\n{traceback.format_exc()}"
                )
                break

        # Execution failed
        execution_time = (datetime.now() - start_time).total_seconds()
        self.status = AgentStatus.ERROR

        error_message = str(last_error) if last_error else "Unknown error"
        result = AgentResult(
            success=False,
            error=error_message,
            execution_time=execution_time,
            retry_count=retry_count,
        )

        # Learn from failure
        if self.enable_learning:
            await self._learn_from_failure(input_data, error_message)

        logger.error(f"[{self.name}] Execution failed after {retry_count} retries")
        return result

    @abstractmethod
    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Implement agent-specific logic."""
        pass

    async def _call_llm(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
    ) -> str:
        """Call LLM with error handling."""
        try:
            # If temperature is specified, create a new LLM instance with that temperature
            llm = self.llm
            if temperature is not None and hasattr(llm, "temperature"):
                # Create a copy with different temperature if needed
                from langchain_openai import ChatOpenAI
                if isinstance(llm, ChatOpenAI):
                    llm = ChatOpenAI(
                        model=llm.model_name if hasattr(llm, "model_name") else "gpt-4-turbo-preview",
                        temperature=temperature,
                    )
            
            response = await llm.ainvoke(messages)
            if isinstance(response, AIMessage):
                return response.content
            return str(response)
        except Exception as e:
            logger.error(f"[{self.name}] LLM call failed: {e}")
            raise AgentError(
                f"LLM call failed: {e}",
                agent_name=self.name,
                error_type="llm_error",
                retryable=True,
            )

    def _get_memory_context(self) -> Dict[str, Any]:
        """Get relevant context from memory."""
        if not self.memory.experiences:
            return {}

        # Get recent successful experiences
        recent_successes = [
            exp
            for exp in self.memory.experiences[-10:]
            if exp.get("success", False)
        ]

        return {
            "recent_experiences": recent_successes,
            "learned_patterns": self.memory.learned_patterns,
            "performance_metrics": self.memory.performance_metrics,
        }

    async def _learn_from_success(
        self, input_data: Dict[str, Any], result_data: Any, execution_time: float
    ):
        """Learn from successful execution."""
        experience = {
            "timestamp": datetime.now().isoformat(),
            "input": input_data,
            "output": result_data,
            "execution_time": execution_time,
            "success": True,
        }

        self.memory.experiences.append(experience)
        self.memory.performance_metrics["avg_execution_time"] = (
            self.memory.performance_metrics.get("avg_execution_time", 0) * 0.9
            + execution_time * 0.1
        )
        self.memory.performance_metrics["success_rate"] = (
            self.memory.performance_metrics.get("success_rate", 0) * 0.9 + 1.0 * 0.1
        )
        self.memory.last_updated = datetime.now()

        # Keep only last 100 experiences
        if len(self.memory.experiences) > 100:
            self.memory.experiences = self.memory.experiences[-100:]

    async def _learn_from_error(
        self, error: AgentError, input_data: Dict[str, Any]
    ):
        """Learn from error."""
        experience = {
            "timestamp": datetime.now().isoformat(),
            "input": input_data,
            "error": str(error),
            "error_type": error.error_type,
            "success": False,
        }

        self.memory.experiences.append(experience)
        self.memory.performance_metrics["success_rate"] = (
            self.memory.performance_metrics.get("success_rate", 0) * 0.9 + 0.0 * 0.1
        )

        # Update learned patterns to avoid similar errors
        if error.error_type not in self.memory.learned_patterns:
            self.memory.learned_patterns[error.error_type] = {
                "count": 0,
                "avoid_patterns": [],
            }
        self.memory.learned_patterns[error.error_type]["count"] += 1

    async def _learn_from_failure(
        self, input_data: Dict[str, Any], error_message: str
    ):
        """Learn from final failure."""
        experience = {
            "timestamp": datetime.now().isoformat(),
            "input": input_data,
            "error": error_message,
            "success": False,
        }

        self.memory.experiences.append(experience)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics."""
        return {
            "name": self.name,
            "status": self.status.value,
            "memory_size": len(self.memory.experiences),
            "performance_metrics": self.memory.performance_metrics,
            "last_updated": self.memory.last_updated.isoformat(),
        }

