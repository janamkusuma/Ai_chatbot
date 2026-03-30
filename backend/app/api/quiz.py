# backend/app/api/quiz.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import random

from app.auth import get_current_user
from app.database import get_db
from app.models import QuizScore

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

# ------------------------------
# ✅ Full Quiz Data (All Categories)
# ------------------------------
quiz_data = {
    "Infectious Diseases": [
        {"question":"Dengue spreads by?","options":["Housefly","Mosquito","Water","Food"],"answer":1},
        {"question":"COVID affects mainly?","options":["Heart","Lungs","Kidney","Liver"],"answer":1},
        {"question":"Malaria caused by?","options":["Virus","Bacteria","Parasite","Fungus"],"answer":2},
        {"question":"Flu spreads via?","options":["Water","Air droplets","Food","Soil"],"answer":1},
        {"question":"Common symptom of infection?","options":["Fever","Hair fall","Blindness","Fracture"],"answer":0},
        {"question":"TB affects?","options":["Lungs","Heart","Brain","Skin"],"answer":0},
        {"question":"Prevention of infections?","options":["Handwash","Sleep less","Skip food","None"],"answer":0},
        {"question":"Hepatitis affects?","options":["Liver","Kidney","Heart","Brain"],"answer":0},
        {"question":"Virus spreads by?","options":["Contact","Magic","Nothing","Stone"],"answer":0},
        {"question":"Immunity helps?","options":["Fight disease","Increase weight","Reduce height","None"],"answer":0}
    ],

    "Respiratory Diseases": [
        {"question":"Pneumonia affects?","options":["Lungs","Heart","Brain","Kidney"],"answer":0},
        {"question":"Asthma symptom?","options":["Breathing issue","Hair loss","Blindness","None"],"answer":0},
        {"question":"Oxygen used by?","options":["Lungs","Kidney","Liver","Skin"],"answer":0},
        {"question":"Bronchitis is?","options":["Lung issue","Bone issue","Skin issue","Eye issue"],"answer":0},
        {"question":"Cough indicates?","options":["Resp issue","Bone issue","Eye issue","None"],"answer":0},
        {"question":"Smoking affects?","options":["Lungs","Hair","Nails","None"],"answer":0},
        {"question":"Air pollution causes?","options":["Resp problems","Good health","Nothing","Sleep"],"answer":0},
        {"question":"Breathing organ?","options":["Lungs","Heart","Brain","Liver"],"answer":0},
        {"question":"Oxygen exchange?","options":["Lungs","Kidney","Skin","Hair"],"answer":0},
        {"question":"Respiratory disease example?","options":["Asthma","Diabetes","Cancer","Ulcer"],"answer":0}
    ],

    "Digestive Diseases": [
        {"question":"Food digestion organ?","options":["Stomach","Heart","Brain","Lungs"],"answer":0},
        {"question":"ORS used for?","options":["Hydration","Pain","Sleep","None"],"answer":0},
        {"question":"Food poisoning cause?","options":["Bad food","Air","Water","Sleep"],"answer":0},
        {"question":"Acidity affects?","options":["Stomach","Brain","Heart","Skin"],"answer":0},
        {"question":"Digestion helps?","options":["Break food","Sleep","Run","Jump"],"answer":0},
        {"question":"Vomiting sign of?","options":["Digestive issue","Bone issue","Hair issue","None"],"answer":0},
        {"question":"Healthy digestion needs?","options":["Fiber","Stone","Plastic","None"],"answer":0},
        {"question":"Water helps?","options":["Digestion","Hair fall","Sleep","None"],"answer":0},
        {"question":"Stomach pain means?","options":["Digestive issue","Eye issue","Ear issue","None"],"answer":0},
        {"question":"Liver role?","options":["Digestion","Thinking","Walking","None"],"answer":0}
    ],

    "Chronic Diseases": [
        {"question":"High BP called?","options":["Hypertension","Hypotension","Diabetes","Asthma"],"answer":0},
        {"question":"Diabetes affects?","options":["Sugar","Bones","Hair","Skin"],"answer":0},
        {"question":"Chronic means?","options":["Long term","Short term","No issue","None"],"answer":0},
        {"question":"BP check helps?","options":["Health","Weight","Height","None"],"answer":0},
        {"question":"Sugar control needs?","options":["Diet","Sleep","Run","None"],"answer":0},
        {"question":"Exercise helps?","options":["Health","Hair loss","Weakness","None"],"answer":0},
        {"question":"Chronic disease example?","options":["Diabetes","Cold","Fever","None"],"answer":0},
        {"question":"BP affects?","options":["Heart","Hair","Nails","None"],"answer":0},
        {"question":"Healthy lifestyle means?","options":["Good habits","Bad habits","None","Sleep"],"answer":0},
        {"question":"Obesity causes?","options":["Chronic disease","Good health","Sleep","None"],"answer":0}
    ],

    "Heart Diseases": [
        {"question":"Heart pumps?","options":["Blood","Water","Air","Food"],"answer":0},
        {"question":"Chest pain means?","options":["Heart issue","Hair issue","Eye issue","None"],"answer":0},
        {"question":"Heart disease risk?","options":["Smoking","Exercise","Water","None"],"answer":0},
        {"question":"Heart rate measures?","options":["Pulse","Height","Weight","None"],"answer":0},
        {"question":"BP relates to?","options":["Heart","Skin","Hair","None"],"answer":0},
        {"question":"Exercise helps?","options":["Heart","Hair","Nails","None"],"answer":0},
        {"question":"Cholesterol affects?","options":["Heart","Hair","Skin","None"],"answer":0},
        {"question":"Healthy heart needs?","options":["Diet","Junk food","None","Sleep"],"answer":0},
        {"question":"Heart attack means?","options":["Blockage","Growth","Sleep","None"],"answer":0},
        {"question":"Heart organ?","options":["Blood pump","Thinking","Digestion","None"],"answer":0}
    ],

    "Neurological Disorders": [
        {"question":"Brain controls?","options":["Body","Hair","Nails","None"],"answer":0},
        {"question":"Migraine is?","options":["Headache","Bone pain","Skin issue","None"],"answer":0},
        {"question":"Seizure occurs in?","options":["Brain","Heart","Kidney","None"],"answer":0},
        {"question":"Memory stored in?","options":["Brain","Heart","Lungs","None"],"answer":0},
        {"question":"Dizziness means?","options":["Brain issue","Hair issue","Skin issue","None"],"answer":0},
        {"question":"Sleep helps?","options":["Brain","Hair","Skin","None"],"answer":0},
        {"question":"Stress affects?","options":["Brain","Nails","Hair","None"],"answer":0},
        {"question":"Nerves connect?","options":["Brain-body","Hair","Skin","None"],"answer":0},
        {"question":"Thinking organ?","options":["Brain","Heart","Liver","None"],"answer":0},
        {"question":"Neuro disease example?","options":["Epilepsy","Flu","Cold","None"],"answer":0}
    ],

    "Skin Diseases": [
        {"question":"Skin protects?","options":["Body","Hair","Nails","None"],"answer":0},
        {"question":"Eczema causes?","options":["Itching","Hair fall","Sleep","None"],"answer":0},
        {"question":"Skin infection means?","options":["Skin issue","Brain issue","Heart issue","None"],"answer":0},
        {"question":"Clean skin needs?","options":["Hygiene","Dirt","None","Sleep"],"answer":0},
        {"question":"Sun affects?","options":["Skin","Hair","Nails","None"],"answer":0},
        {"question":"Rash indicates?","options":["Skin issue","Eye issue","None","Sleep"],"answer":0},
        {"question":"Skin color due to?","options":["Melanin","Blood","Hair","None"],"answer":0},
        {"question":"Healthy skin needs?","options":["Water","Dust","None","Sleep"],"answer":0},
        {"question":"Skin disease example?","options":["Psoriasis","Diabetes","Asthma","None"],"answer":0},
        {"question":"Itching cause?","options":["Skin issue","Brain issue","None","Sleep"],"answer":0}
    ],

    "Kidney Diseases": [
        {"question":"Kidney filters?","options":["Blood","Air","Food","None"],"answer":0},
        {"question":"Kidney stone causes?","options":["Pain","Sleep","Hair fall","None"],"answer":0},
        {"question":"Urine formed in?","options":["Kidney","Heart","Liver","None"],"answer":0},
        {"question":"Water helps?","options":["Kidney","Hair","Nails","None"],"answer":0},
        {"question":"Kidney failure means?","options":["Stop working","Grow","Sleep","None"],"answer":0},
        {"question":"Dialysis used for?","options":["Kidney","Heart","Brain","None"],"answer":0},
        {"question":"Kidney disease sign?","options":["Swelling","Hair fall","None","Sleep"],"answer":0},
        {"question":"Healthy kidney needs?","options":["Water","Dust","None","Sleep"],"answer":0},
        {"question":"Kidney role?","options":["Filter blood","Think","Digest","None"],"answer":0},
        {"question":"Urine color change?","options":["Health issue","Hair issue","None","Sleep"],"answer":0}
    ],

    "Liver Diseases": [
        {"question":"Liver helps?","options":["Digestion","Thinking","Walking","None"],"answer":0},
        {"question":"Hepatitis affects?","options":["Liver","Brain","Heart","None"],"answer":0},
        {"question":"Alcohol affects?","options":["Liver","Hair","Nails","None"],"answer":0},
        {"question":"Liver stores?","options":["Energy","Hair","Nails","None"],"answer":0},
        {"question":"Fatty liver cause?","options":["Fat","Sleep","None","Hair"],"answer":0},
        {"question":"Liver disease sign?","options":["Fatigue","Hair fall","None","Sleep"],"answer":0},
        {"question":"Healthy liver needs?","options":["Diet","Junk","None","Sleep"],"answer":0},
        {"question":"Liver organ?","options":["Digestive","Thinking","Walking","None"],"answer":0},
        {"question":"Detox done by?","options":["Liver","Brain","Heart","None"],"answer":0},
        {"question":"Liver damage cause?","options":["Alcohol","Water","Sleep","None"],"answer":0}
    ],

    "Mental Health": [
        {"question":"Depression affects?","options":["Mind","Hair","Skin","None"],"answer":0},
        {"question":"Stress affects?","options":["Mind","Nails","Hair","None"],"answer":0},
        {"question":"Sleep helps?","options":["Mental health","Hair","Skin","None"],"answer":0},
        {"question":"Anxiety means?","options":["Fear","Happy","Sleep","None"],"answer":0},
        {"question":"Meditation helps?","options":["Mind","Hair","Nails","None"],"answer":0},
        {"question":"Mental health needs?","options":["Peace","Noise","None","Sleep"],"answer":0},
        {"question":"Counselling helps?","options":["Mind","Hair","Skin","None"],"answer":0},
        {"question":"Overthinking causes?","options":["Stress","Health","None","Sleep"],"answer":0},
        {"question":"Happy mind needs?","options":["Balance","Stress","None","Sleep"],"answer":0},
        {"question":"Mental disease example?","options":["Depression","Flu","Cold","None"],"answer":0}
    ]
}

# ------------------------------
# ✅ Pydantic model
# ------------------------------
class QuizSaveIn(BaseModel):
    score: int
    total: int

# ------------------------------
# ✅ Helper: convert datetime to UTC ISO string
# ------------------------------
def to_utc_z(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

# ------------------------------
# Save quiz score
# ------------------------------
@router.post("/save")
def save_quiz_score(
    body: QuizSaveIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if body.total <= 0:
        raise HTTPException(status_code=400, detail="Total must be > 0")
    if body.score < 0 or body.score > body.total:
        raise HTTPException(status_code=400, detail="Invalid score")

    email = getattr(user, "email", None) or getattr(user, "username", "unknown")

    row = QuizScore(
        user_email=email,
        score=int(body.score),
        total=int(body.total),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"message": "saved", "created_at": to_utc_z(row.created_at)}

# ------------------------------
# Get my scores
# ------------------------------
@router.get("/my-scores")
def my_scores(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    email = getattr(user, "email", None) or getattr(user, "username", "unknown")
    role = getattr(user, "role", "USER")

    q = db.query(QuizScore)
    if role != "ADMIN":
        q = q.filter(QuizScore.user_email == email)

    rows = q.order_by(QuizScore.id.desc()).limit(500).all()

    if role == "ADMIN":
        return [
            {
                "user_email": r.user_email,
                "score": r.score,
                "total": r.total,
                "created_at": to_utc_z(r.created_at),
            }
            for r in rows
        ]

    return [
        {
            "score": r.score,
            "total": r.total,
            "created_at": to_utc_z(r.created_at),
        }
        for r in rows
    ]

# ------------------------------
# Quiz categories & questions
# ------------------------------
@router.get("/categories")
def get_categories():
    return {"categories": list(quiz_data.keys())}

@router.get("/questions")
def get_questions(category: str):
    questions = quiz_data.get(category, [])
    if not questions:
        return {"questions": [], "message": "No questions found"}
    selected = random.sample(questions, min(10, len(questions)))
    return {"questions": selected}