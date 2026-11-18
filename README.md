# 🐾 PawPal+ AI Care Agent — Applied AI Pet Care System

**Base Project:** Extended from **PawPal+ (Module 2)**, a modular object-oriented Python and Streamlit pet care scheduler (`Owner`, `Pet`, `Task`, `Scheduler`) that originally sorted daily routines, detected overlapping time windows, and automated `timedelta`-based recurring tasks.

**Project Summary:** **PawPal+ AI Care Agent** evolves the original rule-based scheduler into a trustworthy, retrieval-augmented, agentic planning system. When an owner enters a care request, the agent retrieves relevant veterinary guidelines via RAG, enforces toxic-substance and medication safety guardrails, schedules validated routines into `PawPal+`, and runs a self-critique reliability pass that scores confidence and escalates uncertain or medical actions for human-in-the-loop review.

## Architecture Overview

![System Architecture](diagrams/architecture.mmd)

1. **KnowledgeRetriever (RAG):** Searches `knowledge_base/veterinary_guidelines.md` to retrieve species- and category-specific rules (for example, adjusting walk durations for senior dogs aged 8+).
2. **Safety Guardrails:** Screens every request against toxic substances (`chocolate`, `grapes`, `xylitol`, `ibuprofen`, etc.) and flags medication or dosage requests for mandatory human confirmation.
3. **PawPal+ Core Engine (`pawpal_system.py`):** Converts approved plans into `Task` objects attached to `Pet` and `Owner`, then runs `Scheduler.detect_conflicts()` to check for overlapping routines.
4. **Self-Critique & Reliability Scorer:** Computes a `0.0–1.0` confidence score based on RAG grounding, guardrail flags, and schedule conflicts, logging every decision to `ai_agent.log`.

## Setup Instructions

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the reproducible AI agent demo
python main.py

# 4. Run the automated reliability test suite
python -m pytest
```

## Sample Interactions

```text
=== PawPal+ Applied AI Care Agent — Reproducible Demo ===

--- Interaction 1: Bella | 'Daily morning walk' @ 08:00 ---
Approved: True
Confidence Score: 1.00 | Human Review Needed: False
Retrieved RAG Guidelines: ['Senior dogs (age 8+) or brachycephalic breeds should take shorter 15 to 20 minute walks during cool morning or evening hours.', 'Adult dogs generally need 30 to 60 minutes of daily physical exercise depending on breed, age, and weather conditions.']
Guardrail Flags: []
Explanation: Scheduled 'Daily morning walk' (Walk, 20m, Medium priority) at 08:00. Grounded in guideline: Senior dogs (age 8+) or brachycephalic breeds should take shorter 15 to 20 minute walks during cool morning or evening hours.

--- Interaction 2: Milo | 'Daily thyroid medication pill' @ 08:15 ---
Approved: True
Confidence Score: 0.65 | Human Review Needed: True
Retrieved RAG Guidelines: ['Prescription pet medications such as thyroid pills or heartworm preventatives must be given at consistent 12-hour or 24-hour intervals.']
Guardrail Flags: ['HUMAN_REVIEW_REQUIRED: Medication or dosage routine requires owner/vet verification.']
Explanation: Scheduled 'Daily thyroid medication pill' (Medication, 15m, High priority) at 08:15. Grounded in guideline: Prescription pet medications such as thyroid pills or heartworm preventatives must be given at consistent 12-hour or 24-hour intervals.
Self-Critique Notes: ['Medication routine flagged for human-in-the-loop confirmation.', 'Schedule conflict detected (1 overlapping task pair(s)).']

--- Interaction 3: Bella | 'Give chocolate treat snack' @ 15:00 ---
Approved: False
Confidence Score: 0.15 | Human Review Needed: True
Retrieved RAG Guidelines: ['Dogs require two measured meals per day; avoid grapes, raisins, chocolate, xylitol, onions, and macadamia nuts as they are toxic.']
Guardrail Flags: ["BLOCKED_UNSAFE_SUBSTANCE: 'chocolate' is hazardous for pets."]
Explanation: Request rejected by safety guardrail to protect pet health.
Self-Critique Notes: ['Request blocked by toxic-substance safety guardrail.']

Summary: 3 scenarios executed | Average Confidence: 0.60
```

## Design Decisions

* **Deterministic Local RAG + Guardrails:** Using a structured local Markdown veterinary knowledge base (`knowledge_base/veterinary_guidelines.md`) with keyword-overlap ranking ensures 100% reproducible results without external API failures or hallucinated medical advice.
* **Human-in-the-Loop Escalation Over Silent Automation:** Any medication task or schedule collision automatically lowers the agent's confidence score below `0.80` and sets `needs_human_review=True`, trading full automation for owner safety.

## Testing Summary

**11 out of 11 automated tests passed** (`6` core scheduler tests in `tests/test_pawpal.py` + `5` AI agent reliability, RAG, and guardrail tests in `tests/test_ai_agent.py`). Confidence scores averaged `0.88` on valid non-medical routines, dropped to `0.65` when medication and time conflicts overlapped, and dropped to `0.15` when toxic foods were blocked.

| Test Case | Evaluation Criteria | Result |
| :--- | :--- | :--- |
| Senior dog walk request (`age=9`) | Retrieves senior guideline & caps walk to 20 mins (`confidence >= 0.80`) | Pass |
| Toxic food input (`chocolate` / `grapes`) | Blocked by guardrail (`approved=False`, `confidence <= 0.20`) | Pass |
| Cat medication request (`thyroid pill`) | Schedules task but flags `needs_human_review=True` | Pass |
| Overlapping time request (`08:00` & `08:10`) | Detects conflict and deducts confidence score | Pass |
| Unregistered pet name (`GhostPet`) | Handled gracefully without crashing (`confidence=0.0`) | Pass |

## Reflection

Extending PawPal+ from a basic scheduler into an agentic, RAG-grounded system showed me that trustworthy AI depends just as much on guardrails and self-critique as on generating answers. Adding deterministic safety checks, structured logging, and confidence thresholds turned a simple task manager into a transparent decision-support assistant. (See `model_card.md` for full responsible-AI and AI-collaboration reflections.)
