from ai_care_agent import PawPalAIAgent
from pawpal_system import Owner, Pet


def run_demo() -> None:
    owner = Owner(name="Salmaa", email="salmaa@example.com")
    bella = Pet(name="Bella", species="Dog", age=9)  # Senior dog
    milo = Pet(name="Milo", species="Cat", age=2)
    owner.add_pet(bella)
    owner.add_pet(milo)

    agent = PawPalAIAgent(owner)

    scenarios = [
        ("Bella", "Daily morning walk", "08:00"),
        ("Milo", "Daily thyroid medication pill", "08:15"),
        ("Bella", "Give chocolate treat snack", "15:00"),
    ]

    print("=== PawPal+ Applied AI Care Agent — Reproducible Demo ===\n")
    decisions = []
    for idx, (pet_name, req, time_str) in enumerate(scenarios, start=1):
        decision = agent.plan_and_schedule(pet_name=pet_name, request_text=req, time_str=time_str)
        decisions.append(decision)
        print(f"--- Interaction {idx}: {pet_name} | '{req}' @ {time_str} ---")
        print(f"Approved: {decision.approved}")
        print(f"Confidence Score: {decision.confidence_score:.2f} | Human Review Needed: {decision.needs_human_review}")
        print(f"Retrieved RAG Guidelines: {decision.retrieved_guidelines}")
        print(f"Guardrail Flags: {decision.guardrail_flags}")
        print(f"Explanation: {decision.explanation}")
        if decision.critique_notes:
            print(f"Self-Critique Notes: {decision.critique_notes}")
        print()

    avg_conf = sum(d.confidence_score for d in decisions) / len(decisions)
    print(f"Summary: {len(decisions)} scenarios executed | Average Confidence: {avg_conf:.2f}")


if __name__ == "__main__":
    run_demo()
