from database import engine, SessionLocal, Base
from models import HCP, Interaction, Followup
from datetime import date

def seed():
    Base.metadata.create_all(bind=engine)   # creates tables if they dont exist
    db = SessionLocal()

    # Idempotent check: if HCP count > 0, skip seeding
    if db.query(HCP).count() > 0:
        print("Database already seeded. Skipping...")
        db.close()
        return

    # 3 Pharma HCPs
    hcps = [
        HCP(name="Dr. Meera Sharma",  specialty="Cardiologist",         hospital="Apollo Hospital",  city="New Delhi"),
        HCP(name="Dr. Rajesh Patel",  specialty="General Practitioner", hospital="City Clinic",      city="Mumbai"),
        HCP(name="Dr. Anita Verma",   specialty="Endocrinologist",      hospital="Max Hospital",     city="Bangalore"),
    ]
    db.add_all(hcps)
    db.commit()

    # 5 Realistic Pharma Interactions
    interactions = [
        Interaction(hcp_id=1, interaction_date=date(2026,4,15), mode="visit",
            product_discussed="Atorvastatin 10mg", sentiment="Positive",
            materials_shared="Brochures", key_topics="Cholesterol management, post-MI patients",
            outcome="interested",
            raw_notes="Met Dr. Sharma at Apollo. Discussed Atorvastatin 10mg for post-MI.",
            ai_summary="Dr. Sharma showed strong interest in Atorvastatin 10mg."),
        Interaction(hcp_id=1, interaction_date=date(2026,4,10), mode="call",
            product_discussed="Rosuvastatin 20mg", sentiment="Neutral",
            materials_shared="None", key_topics="Dosage comparison, side effects",
            outcome="follow_up_needed",
            raw_notes="Phone call about Rosuvastatin 20mg vs competitors.",
            ai_summary="Dr. Sharma requested comparative data before switching."),
        Interaction(hcp_id=2, interaction_date=date(2026,4,17), mode="visit",
            product_discussed="Metformin 500mg", sentiment="Positive",
            materials_shared="Samples", key_topics="Type 2 diabetes management",
            outcome="samples_requested",
            raw_notes="Dr. Patel enthusiastic about Metformin. Requested 20 samples.",
            ai_summary="Strong prescription potential. 20 samples given."),
        Interaction(hcp_id=2, interaction_date=date(2026,4,12), mode="email",
            product_discussed="Glipizide 5mg", sentiment="Neutral",
            materials_shared="Brochures", key_topics="HbA1c reduction, combination therapy",
            outcome="detailed_product",
            raw_notes="Email follow-up on Glipizide combination therapy.",
            ai_summary="Dr. Patel requested detailed clinical data for Glipizide."),
        Interaction(hcp_id=3, interaction_date=date(2026,4,18), mode="visit",
            product_discussed="Insulin Glargine", sentiment="Positive",
            materials_shared="Brochures, Samples", key_topics="Basal insulin initiation",
            outcome="interested",
            raw_notes="Dr. Verma very interested in Insulin Glargine for T1D patients.",
            ai_summary="Priority account. Excellent engagement. Schedule follow-up within 10 days."),
    ]
    db.add_all(interactions)
    db.commit()

    # 2 Pending Follow-ups
    followups = [
        Followup(interaction_id=2, hcp_id=1, due_date=date(2026,4,28),
                 notes="Share Rosuvastatin vs Atorvastatin comparative study"),
        Followup(interaction_id=4, hcp_id=2, due_date=date(2026,4,25),
                 notes="Send Glipizide 5mg combination therapy clinical trial PDF"),
    ]
    db.add_all(followups)
    db.commit()
    db.close()
    print("Database seeded: 3 HCPs, 5 interactions, 2 follow-ups")

if __name__ == "__main__":
    seed()
