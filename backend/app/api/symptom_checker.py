from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from app.auth import get_current_user
from app.api.disease_data import DISEASES

router = APIRouter(prefix="/symptom", tags=["Symptom Checker"])

print("✅ USING FIXED REASON VERSION")  # remove later

class SymptomIn(BaseModel):
    symptoms: List[str]

def _risk_from_score(score: int) -> str:
    if score >= 8:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"

def _fixed_reason(name: str) -> str:
    name = (name or "").strip()

    mapping = {
        "Influenza (Flu)": "Fever and cough are common symptoms of influenza, especially if accompanied by body aches or fatigue.",
        "COVID-19": "Fever and cough can be symptoms of COVID-19, especially if there are additional symptoms like loss of taste or smell.",
        "Common Cold": "Fever and cough are common symptoms of a cold, often with mild fatigue or headache.",
        "Pneumonia": "Cough and fever can indicate pneumonia, particularly if there is chest pain or breathing difficulty.",
        "Bronchitis": "Persistent cough with fever or fatigue may suggest bronchitis, especially if mucus production occurs.",
        "Food Poisoning": "Nausea, vomiting, and fever often indicate food poisoning, especially after contaminated food.",
        "Hypertension": "Hypertension usually has no symptoms, but dizziness or headaches can sometimes occur.",
        "Diabetes": "Fatigue or dizziness may occur in diabetes, though proper diagnosis requires medical tests.",
        "Dengue": "High fever with severe headache and body pain can be seen in dengue, especially if there is rash or nausea."
    }

    return mapping.get(
        name,
        "Some of the selected symptoms are associated with this condition. Consult a doctor for confirmation."
    )

@router.post("/analyze")
def analyze(body: SymptomIn, user=Depends(get_current_user)) -> Dict[str, Any]:
    # ✅ NEW: normalize / alias (frontend lo different words unte match correct avvali)
    alias = {
        "high fever": "fever",
        "severe headache": "headache",
        "dry cough": "cough",
        "productive cough": "cough",
        "shortness of breath": "breathing difficulty",
        "chest tightness": "chest pain",   # optional
        "skin rash": "rash",
        "body aches": "body pain",
        "muscle pain": "body pain",
        "joint pain": "body pain",
        "sleepiness": "fatigue",
        "nasal congestion": "cold",
        "runny nose": "cold",
        "loss of smell": "loss of taste",  # optional (if you don’t have smell in data)
    }

    selected = [
        alias.get(s.strip().lower(), s.strip().lower())
        for s in (body.symptoms or [])
        if s and s.strip()
    ]
    selected_set = set(selected)

    results = []

    for d in DISEASES:
        all_sym = set([alias.get(str(x).strip().lower(), str(x).strip().lower()) for x in d.get("symptoms", []) if x])
        key_sym = set([alias.get(str(x).strip().lower(), str(x).strip().lower()) for x in d.get("key_symptoms", []) if x])

        matched_all = sorted(list(selected_set.intersection(all_sym)))
        if not matched_all:
            continue

        matched_key = sorted(list(selected_set.intersection(key_sym)))

        matched_show = matched_key if matched_key else matched_all
        matched_show = matched_show[:3]

        score = (len(matched_key) * 2) + (len(matched_all) * 1)

        results.append({
            "name": d.get("name", "Unknown"),
            "risk": _risk_from_score(score),
            "score": score,
            "reason": _fixed_reason(d.get("name", "")),
            "matched_symptoms": matched_show
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:6]

    return {
        "results": results,
        "home_remedies": [
            "Drink plenty of fluids (water/ORS).",
            "Take adequate rest and sleep.",
            "Eat light foods (khichdi/soup/curd rice).",
            "Avoid oily/spicy food if nausea."
        ],
        "when_to_visit_doctor": [
            "Breathing difficulty / chest pain.",
            "Very high fever lasting >2 days.",
            "Severe vomiting or cannot drink fluids.",
            "Drowsiness, confusion, or fainting.",
            "Any bleeding or severe weakness (urgent)."
        ],
    }