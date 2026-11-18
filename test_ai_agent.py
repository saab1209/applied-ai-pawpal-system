from ai_care_agent import PawPalAIAgent
from pawpal_system import Owner, Pet


def setup_agent() -> PawPalAIAgent:
    owner = Owner(name="Salmaa")
    owner.add_pet(Pet(name="Bella", species="Dog", age=9))
    owner.add_pet(Pet(name="Milo", species="Cat", age=2))
    return PawPalAIAgent(owner)


def test_rag_adjusts_senior_dog_walk_duration():
    agent = setup_agent()
    decision = agent.plan_and_schedule("Bella", "Daily morning walk", "08:00")
    assert decision.approved is True
    assert decision.scheduled_task is not None
    assert decision.scheduled_task.duration_minutes == 20
    assert len(decision.retrieved_guidelines) >= 1
    assert decision.confidence_score >= 0.80


def test_guardrail_blocks_toxic_substance():
    agent = setup_agent()
    decision = agent.plan_and_schedule("Bella", "Feed chocolate and grapes", "14:00")
    assert decision.approved is False
    assert decision.scheduled_task is None
    assert decision.needs_human_review is True
    assert decision.confidence_score <= 0.20


def test_medication_triggers_human_in_the_loop_flag():
    agent = setup_agent()
    decision = agent.plan_and_schedule("Milo", "Daily thyroid pill dosage", "09:00")
    assert decision.approved is True
    assert decision.needs_human_review is True
    assert any("HUMAN_REVIEW_REQUIRED" in f for f in decision.guardrail_flags)


def test_conflict_lowers_confidence_score():
    agent = setup_agent()
    agent.plan_and_schedule("Bella", "Morning walk", "08:00")
    second = agent.plan_and_schedule("Milo", "Morning play session", "08:10")
    assert second.approved is True
    assert second.confidence_score < 1.0
    assert any("conflict" in note.lower() for note in second.critique_notes)


def test_unknown_pet_handled_gracefully():
    agent = setup_agent()
    decision = agent.plan_and_schedule("GhostPet", "Daily walk", "10:00")
    assert decision.approved is False
    assert decision.confidence_score == 0.0
    assert decision.needs_human_review is True
