# 🐾 Model Card: PawPal+ AI Care Agent

## 1. System Overview & Intended Use
**PawPal+ AI Care Agent** is an educational decision-support assistant built on top of the PawPal+ pet care scheduler. It helps pet owners convert natural-language care goals into validated daily tasks grounded in veterinary guidelines, while flagging medical actions and schedule conflicts for human review. It is **not** a substitute for licensed veterinary diagnosis or emergency care.

## 2. Limitations & Potential Biases
* **Small Curated Knowledge Base:** `knowledge_base/veterinary_guidelines.md` covers common dog and cat routines (feeding, exercise, medication, checkups) but lacks specialized guidance for exotic pets (birds, reptiles, rabbits), breed-specific conditions, or regional toxins.
* **Keyword-Overlap Retrieval:** Because `KnowledgeRetriever` uses token-overlap matching rather than semantic embeddings, unusually phrased requests may miss a relevant guideline and fall back to default durations (`confidence` reduced by `-0.25`).
* **English-Only Guardrail Lexicon:** The toxic-substance blocklist checks English terms (`chocolate`, `grapes`, `xylitol`, `ibuprofen`) and could miss misspelled or non-English names.

## 3. Potential Misuse & Mitigation Strategies
* **Misuse Risk (Over-Reliance on Medical Advice):** A user might treat the agent's task confirmation as veterinary approval for administering medications or treating acute illness.
* **Mitigations Implemented:**
  * Hard safety guardrails immediately block known toxic substances (`BLOCKED_UNSAFE_SUBSTANCE`).
  * Any medication or dosage keyword automatically triggers `HUMAN_REVIEW_REQUIRED` and sets `needs_human_review=True`.
  * Every action is recorded in `ai_agent.log` with timestamps, confidence scores, and self-critique notes for full auditability.

## 4. Reliability Testing Surprises
While testing overlapping scenarios, I was surprised to see how dramatically a single time collision combined with a medication flag lowered the self-critique confidence score (from `1.00` down to `0.65`). Even though the agent correctly identified the guideline and scheduled the task, combining both penalties cleanly surfaced why an owner needs to step in and resolve the timing conflict before giving medication.

## 5. AI Collaboration Reflection
* **Suggestion Accepted:** I accepted the AI assistant's recommendation to separate `KnowledgeRetriever` and `PawPalAIAgent` into a dedicated `ai_care_agent.py` module that wraps `pawpal_system.py` rather than modifying the original `Owner`, `Pet`, `Task`, and `Scheduler` classes. This preserved backward compatibility so all 6 original unit tests continued passing untouched while 5 new AI reliability tests were added cleanly.
* **Suggestion Rejected / Revised:** An earlier AI draft suggested calling an external hosted LLM API with a large prompt chain to classify tasks and critique outputs. I rejected that approach and revised it into a deterministic local RAG retriever paired with explicit rule-based guardrails and self-critique scoring—eliminating external API key failures, reducing latency to milliseconds, and making every test 100% reproducible for reviewers.
