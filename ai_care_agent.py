import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pawpal_system import Owner, Pet, Scheduler, Task

# Configure structured execution logging
logging.basicConfig(
    filename="ai_agent.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

TOXIC_OR_UNSAFE_KEYWORDS = {
    "chocolate",
    "grapes",
    "raisins",
    "xylitol",
    "ibuprofen",
    "acetaminophen",
    "tylenol",
    "advil",
    "onion",
    "garlic",
    "lily",
    "lilies",
}


@dataclass
class AgentDecision:
    """Structured output returned by the PawPal+ AI Care Agent."""
    pet_name: str
    request: str
    approved: bool
    scheduled_task: Optional[Task]
    retrieved_guidelines: List[str]
    guardrail_flags: List[str]
    confidence_score: float
    needs_human_review: bool
    explanation: str
    critique_notes: List[str] = field(default_factory=list)


class KnowledgeRetriever:
    """Lightweight RAG retriever that searches veterinary_guidelines.md for relevant care rules."""

    def __init__(self, kb_path: str = "knowledge_base/veterinary_guidelines.md"):
        self.kb_path = Path(kb_path)
        self.chunks: List[str] = self._load_chunks()

    def _load_chunks(self) -> List[str]:
        if not self.kb_path.exists():
            logging.warning(f"Knowledge base file missing at {self.kb_path}")
            return []
        lines = self.kb_path.read_text(encoding="utf-8").splitlines()
        return [line.lstrip("- ").strip() for line in lines if line.strip().startswith("- ")]

    def retrieve(self, query: str, species: str = "", top_k: int = 2) -> List[str]:
        """Rank and return top_k guideline bullets matching query and pet species."""
        if not self.chunks:
            return []
        keywords = set(f"{query} {species}".lower().replace(",", " ").split())
        stop_words = {"a", "an", "the", "for", "to", "at", "and", "or", "of", "in", "on"}
        keywords = {w for w in keywords if w not in stop_words and len(w) > 2}

        scored: List[Tuple[int, str]] = []
        for chunk in self.chunks:
            chunk_words = set(chunk.lower().replace(",", " ").replace(".", " ").split())
            overlap = len(keywords & chunk_words)
            if overlap > 0:
                scored.append((overlap, chunk))

        scored.sort(key=lambda item: item, reverse=True)
        results = [chunk for _, chunk in scored[:top_k]]
        logging.info(f"RAG retrieve | query='{query}' | species='{species}' | hits={len(results)}")
        return results


class PawPalAIAgent:
    """
    Agentic workflow that combines RAG retrieval, safety guardrails, PawPal+ scheduling,
    and self-critique reliability scoring with human-in-the-loop escalation.
    """

    def __init__(self, owner: Owner, kb_path: str = "knowledge_base/veterinary_guidelines.md"):
        self.owner = owner
        self.scheduler = Scheduler(owner)
        self.retriever = KnowledgeRetriever(kb_path)

    def _check_safety_guardrails(self, request_text: str, category: str) -> List[str]:
        """Validate user input against toxic substance and medical dosage guardrails."""
        flags: List[str] = []
        lower_req = request_text.lower()
        for bad_word in TOXIC_OR_UNSAFE_KEYWORDS:
            if bad_word in lower_req:
                flags.append(f"BLOCKED_UNSAFE_SUBSTANCE: '{bad_word}' is hazardous for pets.")
        if category.lower() == "medication" or any(w in lower_req for w in ("dose", "dosage", "pill", "mg")):
            flags.append("HUMAN_REVIEW_REQUIRED: Medication or dosage routine requires owner/vet verification.")
        return flags

    def _infer_task_details(self, request_text: str, pet: Pet, retrieved_docs: List[str]) -> Tuple[str, int, str, str]:
        """Infer category, safe duration, priority, and frequency using request + RAG context."""
        lower = request_text.lower()
        if any(w in lower for w in ("walk", "run", "exercise", "play")):
            category = "Walk"
            # Adjust duration based on retrieved senior-dog guidance
            duration = 20 if (pet.species.lower() == "dog" and pet.age >= 8) else 30
            priority = "Medium"
        elif any(w in lower for w in ("med", "pill", "thyroid", "vitamin", "dose")):
            category = "Medication"
            duration = 15
            priority = "High"
        elif any(w in lower for w in ("vet", "checkup", "vaccine", "appointment")):
            category = "Appointment"
            duration = 60
            priority = "High"
        else:
            category = "Feeding"
            duration = 15
            priority = "Medium"

        frequency = "Daily" if any(w in lower for w in ("daily", "every day", "morning", "evening")) else "Once"
        return category, duration, priority, frequency

    def _self_critique(
        self,
        pet: Optional[Pet],
        retrieved_docs: List[str],
        guardrail_flags: List[str],
        conflicts: List[Tuple[Task, Task]],
    ) -> Tuple[float, bool, List[str]]:
        """Evaluate plan reliability, compute confidence score (0.0-1.0), and flag human-in-the-loop review."""
        score = 1.0
        notes: List[str] = []

        if pet is None:
            return 0.0, True, ["Pet not found in owner household."]

        if any(f.startswith("BLOCKED") for f in guardrail_flags):
            return 0.15, True, ["Request blocked by toxic-substance safety guardrail."]

        if not retrieved_docs:
            score -= 0.25
            notes.append("No matching veterinary guidelines retrieved; using default scheduling heuristics.")

        if any(f.startswith("HUMAN_REVIEW") for f in guardrail_flags):
            score -= 0.20
            notes.append("Medication routine flagged for human-in-the-loop confirmation.")

        if conflicts:
            score -= 0.15
            notes.append(f"Schedule conflict detected ({len(conflicts)} overlapping task pair(s)).")

        score = round(max(0.0, min(1.0, score)), 2)
        needs_human = score < 0.80 or len(guardrail_flags) > 0
        return score, needs_human, notes

    def plan_and_schedule(self, pet_name: str, request_text: str, time_str: str = "09:00") -> AgentDecision:
        """Execute full 4-step agentic pipeline: Retrieve -> Guardrail -> Act -> Self-Critique."""
        logging.info(f"Agent start | pet='{pet_name}' | request='{request_text}' | time='{time_str}'")
        pet = self.owner.get_pet(pet_name)
        if not pet:
            logging.error(f"Pet '{pet_name}' not found.")
            return AgentDecision(
                pet_name=pet_name,
                request=request_text,
                approved=False,
                scheduled_task=None,
                retrieved_guidelines=[],
                guardrail_flags=["ERROR: Pet not registered under owner."],
                confidence_score=0.0,
                needs_human_review=True,
                explanation=f"Could not schedule because '{pet_name}' is not registered.",
                critique_notes=["Missing pet entity."],
            )

        # 1. Retrieve relevant guidelines (RAG)
        retrieved = self.retriever.retrieve(request_text, species=pet.species, top_k=2)

        # 2. Infer task structure and run safety guardrails
        category, duration, priority, frequency = self._infer_task_details(request_text, pet, retrieved)
        flags = self._check_safety_guardrails(request_text, category)

        if any(f.startswith("BLOCKED") for f in flags):
            confidence, needs_human, critique = self._self_critique(pet, retrieved, flags, [])
            logging.warning(f"Guardrail blocked request for {pet_name}: {flags}")
            return AgentDecision(
                pet_name=pet.name,
                request=request_text,
                approved=False,
                scheduled_task=None,
                retrieved_guidelines=retrieved,
                guardrail_flags=flags,
                confidence_score=confidence,
                needs_human_review=needs_human,
                explanation="Request rejected by safety guardrail to protect pet health.",
                critique_notes=critique,
            )

        # 3. Act: Create Task and add to PawPal+ system
        new_task = Task(
            title=request_text.strip(),
            category=category,
            time=time_str,
            duration_minutes=duration,
            priority=priority,
            frequency=frequency,
            pet_name=pet.name,
        )
        pet.add_task(new_task)
        conflicts = self.scheduler.detect_conflicts()

        # 4. Self-Critique & Reliability Scoring
        confidence, needs_human, critique = self._self_critique(pet, retrieved, flags, conflicts)
        guideline_summary = retrieved if retrieved else "Standard household care defaults."
        explanation = (
            f"Scheduled '{new_task.title}' ({category}, {duration}m, {priority} priority) at {time_str}. "
            f"Grounded in guideline: {guideline_summary}"
        )
        logging.info(
            f"Agent completed | pet='{pet.name}' | task='{new_task.title}' | "
            f"confidence={confidence} | human_review={needs_human}"
        )

        return AgentDecision(
            pet_name=pet.name,
            request=request_text,
            approved=True,
            scheduled_task=new_task,
            retrieved_guidelines=retrieved,
            guardrail_flags=flags,
            confidence_score=confidence,
            needs_human_review=needs_human,
            explanation=explanation,
            critique_notes=critique,
        )
