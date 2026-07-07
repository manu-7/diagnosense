"""
Seeds one reference snippet per parameter in ai_service.NORMAL_RANGES.
This is the grounding material RAG retrieval draws from - written here in
plain language, sourced conceptually from general clinical reference
material (e.g. MedlinePlus-style descriptions), not from an LLM.

Usage (container already running):
    docker compose exec api python -m app.seed_rag

Safe to re-run - skips any parameter that already has a snippet.
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.reference_snippet import ReferenceSnippet
from app.services.embedding_service import embed_text

SNIPPETS = [
    {
        "parameter": "hemoglobin",
        "title": "Hemoglobin reference sheet",
        "content": (
            "Hemoglobin is the protein in red blood cells that carries oxygen around the body. "
            "Low hemoglobin (anemia) can cause fatigue, pale skin, dizziness, and shortness of breath, "
            "and is commonly linked to iron deficiency, vitamin B12 or folate deficiency, chronic disease, "
            "or blood loss. High hemoglobin can be linked to dehydration, smoking, lung disease, or living "
            "at high altitude. Mild deviations are often manageable with diet or lifestyle changes; larger "
            "deviations warrant further testing to find the underlying cause."
        ),
    },
    {
        "parameter": "wbc",
        "title": "White blood cell count (WBC) reference sheet",
        "content": (
            "White blood cells (WBCs) are part of the immune system and help fight infection. A high WBC "
            "count often indicates the body is fighting an infection or inflammation, and can also occur "
            "with stress, certain medications, or in rarer cases blood disorders. A low WBC count can mean "
            "increased vulnerability to infection, and may be linked to viral infections, autoimmune "
            "conditions, or bone marrow issues. A single abnormal reading is often temporary and worth "
            "re-checking rather than immediately concerning."
        ),
    },
    {
        "parameter": "platelets",
        "title": "Platelet count reference sheet",
        "content": (
            "Platelets help blood clot to stop bleeding. A low platelet count (thrombocytopenia) can "
            "increase bruising or bleeding risk, and can be linked to viral infections, certain medications, "
            "autoimmune conditions, or bone marrow issues. A high platelet count (thrombocytosis) can occur "
            "after inflammation, infection, iron deficiency, or in some cases bone marrow disorders. "
            "Isolated mild abnormalities are frequently transient."
        ),
    },
    {
        "parameter": "glucose_fasting",
        "title": "Fasting blood glucose reference sheet",
        "content": (
            "Fasting blood glucose measures blood sugar after not eating for at least 8 hours. Elevated "
            "fasting glucose can indicate prediabetes or diabetes, and is often linked to diet, body weight, "
            "physical activity levels, or family history. Low fasting glucose (hypoglycemia) can cause "
            "shakiness, sweating, or confusion, and can be linked to medication, prolonged fasting, or other "
            "metabolic conditions. Repeated testing is typically used to confirm a diagnosis rather than a "
            "single reading."
        ),
    },
    {
        "parameter": "total_cholesterol",
        "title": "Total cholesterol reference sheet",
        "content": (
            "Total cholesterol measures the combined amount of LDL, HDL, and other lipids in the blood. "
            "High total cholesterol increases long-term risk of heart disease and stroke, and is influenced "
            "by diet, physical activity, body weight, genetics, and other health conditions. It is usually "
            "interpreted alongside LDL and HDL levels rather than on its own, since the balance between "
            "'good' and 'bad' cholesterol matters more than the total figure alone."
        ),
    },
    {
        "parameter": "ldl",
        "title": "LDL cholesterol reference sheet",
        "content": (
            "LDL (low-density lipoprotein) is often called 'bad' cholesterol because high levels contribute "
            "to plaque buildup in arteries, raising the risk of heart disease and stroke over time. Elevated "
            "LDL is commonly linked to diet high in saturated fat, lack of physical activity, smoking, "
            "obesity, or genetic factors. Lifestyle changes (diet, exercise) are typically the first-line "
            "approach to lowering LDL, with medication considered for higher or persistent elevations."
        ),
    },
    {
        "parameter": "hdl",
        "title": "HDL cholesterol reference sheet",
        "content": (
            "HDL (high-density lipoprotein) is often called 'good' cholesterol because it helps remove other "
            "forms of cholesterol from the bloodstream, and higher levels are generally protective against "
            "heart disease. Low HDL can be linked to smoking, physical inactivity, obesity, or type 2 "
            "diabetes. Regular physical activity, quitting smoking, and a healthy diet can help raise HDL "
            "levels over time."
        ),
    },
    {
        "parameter": "tsh",
        "title": "Thyroid-stimulating hormone (TSH) reference sheet",
        "content": (
            "TSH is produced by the pituitary gland and regulates thyroid hormone production. A high TSH "
            "usually indicates an underactive thyroid (hypothyroidism), which can cause fatigue, weight gain, "
            "cold intolerance, or hair thinning. A low TSH usually indicates an overactive thyroid "
            "(hyperthyroidism), which can cause weight loss, rapid heartbeat, or anxiety-like symptoms. "
            "TSH is typically interpreted alongside T3/T4 levels for a fuller picture of thyroid function."
        ),
    },
    {
        "parameter": "creatinine",
        "title": "Creatinine reference sheet",
        "content": (
            "Creatinine is a waste product filtered out of the blood by the kidneys, and is used as a marker "
            "of kidney function. Elevated creatinine can indicate reduced kidney function, dehydration, high "
            "protein intake, or certain medications. Low creatinine is less commonly significant and can be "
            "linked to lower muscle mass. Persistently elevated creatinine typically warrants follow-up "
            "kidney function testing."
        ),
    },
    {
        "parameter": "alt",
        "title": "ALT (liver enzyme) reference sheet",
        "content": (
            "ALT (alanine aminotransferase) is an enzyme found mainly in the liver, and elevated levels "
            "usually indicate liver cell stress or damage. Common causes include fatty liver, alcohol use, "
            "certain medications, viral hepatitis, or obesity. A single mild elevation is often followed up "
            "with repeat testing and lifestyle review (alcohol intake, medications, diet) rather than "
            "immediate concern."
        ),
    },
    {
        "parameter": "ast",
        "title": "AST (liver enzyme) reference sheet",
        "content": (
            "AST (aspartate aminotransferase) is an enzyme found in the liver as well as muscle and heart "
            "tissue, so it is usually interpreted alongside ALT to narrow down the likely source of "
            "elevation. Elevated AST with elevated ALT points more specifically toward liver-related causes "
            "like fatty liver, alcohol use, or hepatitis; AST elevated alone can sometimes reflect muscle "
            "strain or cardiac causes instead."
        ),
    },
    {
        "parameter": "vitamin_d",
        "title": "Vitamin D reference sheet",
        "content": (
            "Vitamin D helps the body absorb calcium and supports bone and immune health. Low vitamin D is "
            "common and can cause fatigue, bone pain, muscle weakness, or low mood, and is often linked to "
            "limited sun exposure, diet, or absorption issues. High vitamin D is rare and usually related to "
            "over-supplementation. Mild-to-moderate deficiency is typically corrected with supplements and "
            "diet changes, with follow-up testing to confirm improvement."
        ),
    },
    {
        "parameter": "b12",
        "title": "Vitamin B12 reference sheet",
        "content": (
            "Vitamin B12 is essential for nerve function and red blood cell production. Low B12 can cause "
            "fatigue, weakness, tingling in hands or feet, or memory issues, and is often linked to diet "
            "(especially in vegetarians/vegans), absorption problems, or certain medications. High B12 is "
            "less commonly significant and is usually related to supplementation. Deficiency is generally "
            "treated with supplements or dietary changes."
        ),
    },
    {
        "parameter": "hba1c",
        "title": "HbA1c (3-month average blood sugar) reference sheet",
        "content": (
            "HbA1c reflects average blood sugar levels over roughly the past three months, making it more "
            "stable than a single fasting glucose reading. Elevated HbA1c can indicate prediabetes or "
            "diabetes and is influenced by diet, body weight, physical activity, and family history. Low "
            "HbA1c is uncommon and usually not a concern on its own. Because it reflects a longer trend, a "
            "single elevated reading is usually followed up with repeat testing and lifestyle review rather "
            "than treated as a definitive diagnosis."
        ),
    },
    {
        "parameter": "sodium",
        "title": "Sodium (blood electrolyte) reference sheet",
        "content": (
            "Sodium helps regulate fluid balance and nerve/muscle function. Low sodium can cause confusion, "
            "weakness, or headaches, and can be linked to excessive fluid intake, certain medications, or "
            "kidney/hormonal conditions. High sodium is often linked to dehydration or excess salt intake. "
            "Mild deviations are frequently corrected with fluid or diet adjustments; larger deviations "
            "warrant closer medical follow-up."
        ),
    },
    {
        "parameter": "potassium",
        "title": "Potassium (blood electrolyte) reference sheet",
        "content": (
            "Potassium is important for heart rhythm and muscle function. Low potassium can cause muscle "
            "cramps, weakness, or irregular heartbeat, and can be linked to certain medications, vomiting, "
            "or diarrhea. High potassium can also affect heart rhythm and is often linked to kidney function "
            "or certain medications. Because potassium affects the heart directly, notable deviations are "
            "usually followed up promptly."
        ),
    },
    {
        "parameter": "calcium",
        "title": "Calcium reference sheet",
        "content": (
            "Calcium supports bone strength, muscle function, and nerve signaling. Low calcium can cause "
            "muscle cramps, tingling, or fatigue, and can be linked to vitamin D deficiency, diet, or "
            "parathyroid conditions. High calcium can cause fatigue, nausea, or bone pain, and can be linked "
            "to certain medications or parathyroid conditions. Follow-up testing often looks at vitamin D "
            "and parathyroid hormone together for a fuller picture."
        ),
    },
    {
        "parameter": "iron",
        "title": "Iron reference sheet",
        "content": (
            "Iron is needed to make hemoglobin for oxygen transport in the blood. Low iron can cause "
            "fatigue, pale skin, brittle nails, or hair loss, and is often linked to diet, blood loss, or "
            "absorption issues. High iron is less common and can be linked to certain genetic conditions or "
            "over-supplementation. Iron levels are usually interpreted alongside ferritin for a clearer "
            "picture of the body's iron stores."
        ),
    },
    {
        "parameter": "ferritin",
        "title": "Ferritin (iron storage) reference sheet",
        "content": (
            "Ferritin reflects how much iron is stored in the body, making it a more stable marker than "
            "iron alone. Low ferritin usually confirms iron deficiency, often linked to diet, blood loss, or "
            "increased demand (e.g. pregnancy). High ferritin can be linked to inflammation, liver "
            "conditions, or iron overload disorders. Because ferritin can rise with inflammation, it is "
            "often interpreted alongside other iron markers rather than alone."
        ),
    },
]


async def seed_rag():
    async with AsyncSessionLocal() as db:
        for entry in SNIPPETS:
            existing = await db.execute(select(ReferenceSnippet).where(ReferenceSnippet.parameter == entry["parameter"]))
            if existing.scalar_one_or_none():
                print(f"Snippet already exists, skipping: {entry['parameter']}")
                continue

            embedding = embed_text(entry["content"])
            if embedding is None:
                print(f"Embedding failed for {entry['parameter']} - skipped (check internet access / model download)")
                continue

            db.add(
                ReferenceSnippet(
                    parameter=entry["parameter"],
                    title=entry["title"],
                    content=entry["content"],
                    embedding=embedding,
                )
            )
            print(f"Embedded and added snippet: {entry['parameter']}")

        await db.commit()

    print("\nDone. Reference snippets are ready for RAG retrieval.")


if __name__ == "__main__":
    asyncio.run(seed_rag())