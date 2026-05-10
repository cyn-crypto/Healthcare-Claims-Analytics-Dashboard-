"""
Healthcare Claims Data Generator
Generates synthetic patient-level healthcare claims datasets
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

np.random.seed(42)
random.seed(42)

# ── Constants ──────────────────────────────────────────────────────────────────
N_PATIENTS    = 2_000
N_CLAIMS      = 15_000
REGIONS       = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]
DIAGNOSES     = {
    "E11":  "Type 2 Diabetes",
    "I10":  "Hypertension",
    "J45":  "Asthma",
    "M54":  "Back Pain",
    "F32":  "Depression",
    "I25":  "Coronary Artery Disease",
    "N18":  "Chronic Kidney Disease",
    "J44":  "COPD",
    "Z51":  "Chemotherapy",
    "S72":  "Hip Fracture",
}
PROCEDURES    = {
    "99213": "Office Visit",
    "93000": "EKG",
    "71046": "Chest X-Ray",
    "80053": "Comprehensive Metabolic Panel",
    "85025": "Complete Blood Count",
    "99232": "Subsequent Hospital Care",
    "27447": "Knee Replacement",
    "43239": "Upper GI Endoscopy",
    "99285": "Emergency Dept Visit",
    "36415": "Blood Draw",
}
PAYERS        = ["Medicare", "Medicaid", "BlueCross", "Aetna", "UnitedHealth", "Self-Pay"]
FACILITY_TYPES = ["Hospital", "Outpatient Clinic", "ER", "Specialist Office", "Primary Care"]
GENDERS       = ["M", "F", "Other"]

START_DATE = datetime(2022, 1, 1)
END_DATE   = datetime(2024, 12, 31)


def random_date(start=START_DATE, end=END_DATE):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


# ── 1. Patients ────────────────────────────────────────────────────────────────
def generate_patients():
    print("Generating patients …")
    patients = []
    for pid in range(1, N_PATIENTS + 1):
        age    = int(np.random.normal(55, 18))
        age    = max(18, min(95, age))
        region = random.choice(REGIONS)
        # region-based cost multiplier stored for later use
        patients.append({
            "patient_id":    pid,
            "age":           age,
            "gender":        random.choice(GENDERS),
            "region":        region,
            "payer":         random.choice(PAYERS),
            "zip_code":      f"{random.randint(10000, 99999)}",
            "chronic_conditions": random.randint(0, 5),
            "enrollment_date": random_date(START_DATE, START_DATE + timedelta(days=365)).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(patients)


# ── 2. Claims ──────────────────────────────────────────────────────────────────
def generate_claims(patients_df):
    print("Generating claims …")
    region_multiplier = {
        "Northeast": 1.25, "West": 1.20,
        "Midwest":   1.00, "Southeast": 0.92, "Southwest": 0.88,
    }
    claims = []
    diag_codes = list(DIAGNOSES.keys())
    proc_codes = list(PROCEDURES.keys())

    for cid in range(1, N_CLAIMS + 1):
        patient  = patients_df.sample(1).iloc[0]
        pid      = patient["patient_id"]
        region   = patient["region"]
        payer    = patient["payer"]
        age      = patient["age"]
        chronic  = patient["chronic_conditions"]

        diag  = random.choice(diag_codes)
        proc  = random.choice(proc_codes)
        ftype = random.choice(FACILITY_TYPES)

        # Base cost varies by facility and complexity
        base_cost = {
            "Hospital": np.random.lognormal(8.5, 0.8),
            "ER":       np.random.lognormal(7.8, 0.7),
            "Outpatient Clinic": np.random.lognormal(6.5, 0.6),
            "Specialist Office": np.random.lognormal(6.0, 0.5),
            "Primary Care":      np.random.lognormal(5.5, 0.4),
        }[ftype]

        # Adjust for age, chronic conditions, region
        cost = base_cost * (1 + age / 200) * (1 + chronic * 0.1) * region_multiplier[region]
        cost = round(cost, 2)

        # Payer adjustments
        paid_pct = {"Medicare": 0.80, "Medicaid": 0.65, "BlueCross": 0.78,
                    "Aetna": 0.75, "UnitedHealth": 0.77, "Self-Pay": 0.45}[payer]
        paid     = round(cost * paid_pct, 2)

        svc_date = random_date()
        los      = random.randint(0, 14) if ftype == "Hospital" else 0  # length of stay
        readmit  = 1 if (ftype == "Hospital" and random.random() < (0.08 + chronic * 0.02)) else 0

        claims.append({
            "claim_id":        cid,
            "patient_id":      pid,
            "service_date":    svc_date.strftime("%Y-%m-%d"),
            "service_year":    svc_date.year,
            "service_month":   svc_date.month,
            "service_quarter": f"Q{(svc_date.month - 1)//3 + 1}",
            "diagnosis_code":  diag,
            "diagnosis_desc":  DIAGNOSES[diag],
            "procedure_code":  proc,
            "procedure_desc":  PROCEDURES[proc],
            "facility_type":   ftype,
            "region":          region,
            "payer":           payer,
            "total_cost":      cost,
            "paid_amount":     paid,
            "patient_oop":     round(cost - paid, 2),
            "length_of_stay":  los,
            "readmission_30d": readmit,
            "claim_status":    random.choice(["Approved", "Approved", "Approved", "Denied", "Pending"]),
        })

    return pd.DataFrame(claims)


# ── 3. Quality Metrics ─────────────────────────────────────────────────────────
def generate_quality_metrics(claims_df):
    print("Generating quality metrics …")
    metrics = []
    for region in REGIONS:
        for year in [2022, 2023, 2024]:
            sub = claims_df[(claims_df["region"] == region) & (claims_df["service_year"] == year)]
            if sub.empty:
                continue
            hosp = sub[sub["facility_type"] == "Hospital"]
            metrics.append({
                "region":               region,
                "year":                 year,
                "total_claims":         len(sub),
                "avg_cost_per_claim":   round(sub["total_cost"].mean(), 2),
                "total_spend":          round(sub["total_cost"].sum(), 2),
                "readmission_rate_pct": round(hosp["readmission_30d"].mean() * 100, 2) if len(hosp) else 0,
                "denial_rate_pct":      round((sub["claim_status"] == "Denied").mean() * 100, 2),
                "avg_los_hospital":     round(hosp["length_of_stay"].mean(), 2) if len(hosp) else 0,
                "er_visit_rate_pct":    round((sub["facility_type"] == "ER").mean() * 100, 2),
            })
    return pd.DataFrame(metrics)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    out = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out, exist_ok=True)

    patients = generate_patients()
    claims   = generate_claims(patients)
    quality  = generate_quality_metrics(claims)

    patients.to_csv(f"{out}/patients.csv",        index=False)
    claims.to_csv(  f"{out}/claims.csv",           index=False)
    quality.to_csv( f"{out}/quality_metrics.csv",  index=False)

    print(f"\n✅  Datasets saved to {os.path.abspath(out)}/")
    print(f"   patients.csv        → {len(patients):,} rows")
    print(f"   claims.csv          → {len(claims):,}  rows")
    print(f"   quality_metrics.csv → {len(quality):,}    rows")
    return patients, claims, quality


if __name__ == "__main__":
    main()
