"""
Memory Manager - The "Elephant Brain" for Titan Agent
Handles storage and retrieval of episodic and semantic memory.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages persistent memory for the agent.
    - Episodic: What happened in specific past runs (success/failure).
    - Semantic: General rules and facts learned over time.
    """
    
    def __init__(self):
        self.memory_path = Path(__file__).parent / "knowledge" / "memory.json"
        self._load_memory()
        
    def _load_memory(self):
        """Load memory from JSON file"""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.data = {"episodic_memory": [], "semantic_memory": {"rules": [], "niche_preferences": {}}}
        else:
            self.data = {"episodic_memory": [], "semantic_memory": {"rules": [], "niche_preferences": {}}}
            self._save_memory()

    def _save_memory(self):
        """Save memory to JSON file"""
        try:
            self.data["last_updated"] = datetime.utcnow().isoformat()
            # Ensure directory exists
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.memory_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def recall_relevant_lessons(self, niche: str) -> str:
        """
        Retrieve relevant rules and preferences for the current context.
        Returns a formatted string for the system prompt.
        """
        rules = self.data["semantic_memory"].get("rules", [])
        niche_prefs = self.data["semantic_memory"].get("niche_preferences", {}).get(niche, [])
        
        # Get recent failures from episodic memory to avoid repeating them
        recent_failures = [
            m["lesson"] for m in self.data["episodic_memory"][-5:] 
            if m.get("outcome") == "failure" and m.get("niche") == niche
        ]
        
        memory_context = "## 🧠 AGENT MEMORY (Do not ignore):\n"
        
        if rules:
            memory_context += "GENERAL RULES:\n" + "\n".join([f"- {r}" for r in rules]) + "\n"
            
        if niche_prefs:
            memory_context += f"\nPREFERENCES FOR '{niche.upper()}':\n" + "\n".join([f"- {p}" for p in niche_prefs]) + "\n"
            
        if recent_failures:
            memory_context += "\n⛔ AVOID PAST MISTAKES:\n" + "\n".join([f"- {f}" for f in recent_failures]) + "\n"
            
        return memory_context

    def memorize_episode(self, niche: str, goal: str, outcome: str, lesson: str):
        """
        Store a new experience (episode) and update rules if needed.
        """
        episode = {
            "timestamp": datetime.utcnow().isoformat(),
            "niche": niche,
            "goal": goal,
            "outcome": outcome,
            "lesson": lesson
        }
        
        self.data["episodic_memory"].append(episode)
        
        # If successful and lesson is a general rule, add to semantic memory
        if outcome == "success" and len(lesson) < 100 and "always" in lesson.lower():
            if lesson not in self.data["semantic_memory"]["rules"]:
                self.data["semantic_memory"]["rules"].append(lesson)
                
        self._save_memory()
        logger.info(f"🧠 Memorized episode: {outcome} - {lesson}")

# Global instance
memory_manager = MemoryManager()
