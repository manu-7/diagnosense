"""
One-shot seed script: creates 2 approved diagnostic centers with realistic
packages, plus a demo patient account, so the app isn't empty on first run.

Usage (from the backend folder, container already running):
    docker compose exec api python -m app.seed

Safe to re-run - it skips anything that already exists by email/center name.
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.center import DiagnosticCenter
from app.models.package import Package
from app.models.user import User, UserRole
from app.security import hash_password

DEMO_PASSWORD = "testpass123"

CENTERS = [
    {
        "user": {"name": "City Diagnostics", "email": "city.diagnostics@test.com", "phone": "9800000001"},
        "profile": {
            "center_name": "City Diagnostics",
            "address": "12 Park Street",
            "city": "Kolkata",
            "license_number": "WB-DL-1001",
        },
        "packages": [
            {
                "name": "Complete Blood Count (CBC)",
                "description": "Measures red cells, white cells, and platelets.",
                "symptom_tags": "fatigue,fever,weakness,pale skin,dizziness",
                "test_type": "blood",
                "price": 499.0,
            },
            {
                "name": "Thyroid Profile (T3, T4, TSH)",
                "description": "Checks thyroid hormone levels.",
                "symptom_tags": "fatigue,weight gain,weight loss,hair fall,cold intolerance",
                "test_type": "blood",
                "price": 799.0,
            },
            {
                "name": "Lipid Profile",
                "description": "Cholesterol and triglyceride levels.",
                "symptom_tags": "chest pain,high cholesterol,family history heart disease",
                "test_type": "blood",
                "price": 649.0,
            },
            {
                "name": "Vitamin D & B12 Panel",
                "description": "Checks for common nutritional deficiencies.",
                "symptom_tags": "fatigue,bone pain,muscle weakness,low mood,hair fall",
                "test_type": "blood",
                "price": 999.0,
            },
            {
                "name": "Kidney Function Test (KFT)",
                "description": "Creatinine and electrolyte levels.",
                "symptom_tags": "swelling,reduced urination,fatigue,high blood pressure",
                "test_type": "blood",
                "price": 749.0,
            },
        ],
    },
    {
        "user": {"name": "Wellness Path Labs", "email": "wellnesspath@test.com", "phone": "9800000002"},
        "profile": {
            "center_name": "Wellness Path Labs",
            "address": "45 Salt Lake Sector 5",
            "city": "Kolkata",
            "license_number": "WB-DL-1002",
        },
        "packages": [
            {
                "name": "Fasting Blood Glucose",
                "description": "Screens for diabetes / prediabetes.",
                "symptom_tags": "excessive thirst,frequent urination,fatigue,blurred vision",
                "test_type": "blood",
                "price": 199.0,
            },
            {
                "name": "Liver Function Test (LFT)",
                "description": "ALT, AST, and related liver enzyme markers.",
                "symptom_tags": "jaundice,abdominal pain,nausea,dark urine",
                "test_type": "blood",
                "price": 899.0,
            },
            {
                "name": "Chest X-Ray",
                "description": "Screens lungs and chest cavity.",
                "symptom_tags": "cough,breathlessness,chest pain,persistent cold",
                "test_type": "imaging",
                "price": 349.0,
            },
            {
                "name": "HbA1c (3-Month Sugar Average)",
                "description": "Long-term blood sugar control marker.",
                "symptom_tags": "excessive thirst,frequent urination,fatigue,slow healing wounds",
                "test_type": "blood",
                "price": 599.0,
            },
            {
                "name": "ECG (Electrocardiogram)",
                "description": "Records the heart's electrical activity.",
                "symptom_tags": "chest pain,palpitations,breathlessness,dizziness",
                "test_type": "cardiac",
                "price": 299.0,
            },
        ],
    },
    {
        "user": {"name": "MedCore Diagnostics", "email": "medcore@test.com", "phone": "9800000003"},
        "profile": {
            "center_name": "MedCore Diagnostics",
            "address": "8 Howrah Bridge Road",
            "city": "Howrah",
            "license_number": "WB-DL-1003",
        },
        "packages": [
            {
                "name": "Allergy Panel (IgE)",
                "description": "Screens for common allergy triggers.",
                "symptom_tags": "eye irritation,itching,skin rash,sneezing,watery eyes",
                "test_type": "blood",
                "price": 1299.0,
            },
            {
                "name": "Urine Routine & Culture",
                "description": "Checks for urinary tract infection markers.",
                "symptom_tags": "burning urination,frequent urination,cloudy urine,lower abdominal pain",
                "test_type": "urine",
                "price": 349.0,
            },
            {
                "name": "Dengue/Malaria Antigen Panel",
                "description": "Screens for common mosquito-borne infections.",
                "symptom_tags": "high fever,chills,body ache,headache,joint pain",
                "test_type": "blood",
                "price": 799.0,
            },
            {
                "name": "Iron Studies",
                "description": "Iron and ferritin levels, for anemia workup.",
                "symptom_tags": "fatigue,pale skin,brittle nails,hair loss,restless legs",
                "test_type": "blood",
                "price": 899.0,
            },
        ],
    },
    {
        "user": {"name": "Apollo North Clinic", "email": "apollonorth@test.com", "phone": "9800000004"},
        "profile": {
            "center_name": "Apollo North Clinic",
            "address": "22 Ballygunge Circular Road",
            "city": "Kolkata",
            "license_number": "WB-DL-1004",
        },
        "packages": [
            {
                "name": "Complete Health Checkup",
                "description": "Full-body screening covering blood, sugar, and lipids.",
                "symptom_tags": "general checkup,fatigue,weight changes,preventive screening",
                "test_type": "full-body",
                "price": 1999.0,
            },
            {
                "name": "Prenatal Panel",
                "description": "Core blood work for early pregnancy checkups.",
                "symptom_tags": "pregnancy,fatigue,nausea,dizziness",
                "test_type": "blood",
                "price": 1499.0,
            },
            {
                "name": "Bone Health Panel",
                "description": "Vitamin D and calcium levels for bone strength.",
                "symptom_tags": "bone pain,joint pain,muscle cramps,fatigue",
                "test_type": "blood",
                "price": 1099.0,
            },
            {
                "name": "Electrolyte Panel",
                "description": "Sodium and potassium balance check.",
                "symptom_tags": "muscle cramps,irregular heartbeat,weakness,confusion",
                "test_type": "blood",
                "price": 599.0,
            },
            {
                "name": "STI Screening Panel",
                "description": "Screens for common sexually transmitted infections.",
                "symptom_tags": "genital discomfort,unusual discharge,pelvic pain",
                "test_type": "blood",
                "price": 1599.0,
            },
        ],
    },
]

DEMO_PATIENT = {"name": "Demo Patient", "email": "patient1@test.com", "phone": "9800000099"}


async def seed():
    async with AsyncSessionLocal() as db:
        for entry in CENTERS:
            existing = await db.execute(select(User).where(User.email == entry["user"]["email"]))
            user = existing.scalar_one_or_none()
            if not user:
                user = User(
                    **entry["user"],
                    hashed_password=hash_password(DEMO_PASSWORD),
                    role=UserRole.CENTER,
                )
                db.add(user)
                await db.flush()
                print(f"Created center user: {entry['user']['email']}")
            else:
                print(f"User already exists, skipping: {entry['user']['email']}")

            center_result = await db.execute(select(DiagnosticCenter).where(DiagnosticCenter.user_id == user.id))
            center = center_result.scalar_one_or_none()
            if not center:
                center = DiagnosticCenter(user_id=user.id, is_approved=True, **entry["profile"])
                db.add(center)
                await db.flush()
                print(f"  Created + approved center: {entry['profile']['center_name']}")
            else:
                center.is_approved = True
                print(f"  Center already exists, ensured approved: {entry['profile']['center_name']}")

            existing_pkgs = await db.execute(select(Package).where(Package.center_id == center.id))
            if existing_pkgs.scalars().first():
                print("  Packages already exist, skipping package creation")
            else:
                for pkg in entry["packages"]:
                    db.add(Package(center_id=center.id, **pkg))
                print(f"  Added {len(entry['packages'])} packages")

        patient_existing = await db.execute(select(User).where(User.email == DEMO_PATIENT["email"]))
        if not patient_existing.scalar_one_or_none():
            db.add(
                User(
                    **DEMO_PATIENT,
                    hashed_password=hash_password(DEMO_PASSWORD),
                    role=UserRole.PATIENT,
                )
            )
            print(f"Created patient user: {DEMO_PATIENT['email']}")
        else:
            print(f"Patient already exists, skipping: {DEMO_PATIENT['email']}")

        await db.commit()

    print("\nDone. Log in with password 'testpass123' for any of the accounts above.")


if __name__ == "__main__":
    asyncio.run(seed())