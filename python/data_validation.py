"""
Healthcare Claims – Data Validation & Quality Checks
Runs all QC rules and outputs a validation report.
"""

import sqlite3, os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, "..", "data", "claims.db")
OUT  = os.path.join(BASE, "..", "dashboard", "data_validation_report.csv")

CHECKS = [
    ("QC-01 Null patient_id",
     "SELECT COUNT(*) AS cnt FROM claims WHERE patient_id IS NULL"),
    ("QC-02 Null service_date",
     "SELECT COUNT(*) AS cnt FROM claims WHERE service_date IS NULL"),
    ("QC-03 Non-positive total_cost",
     "SELECT COUNT(*) AS cnt FROM claims WHERE total_cost <= 0"),
    ("QC-04 Paid > billed (overpayment)",
     "SELECT COUNT(*) AS cnt FROM claims WHERE paid_amount > total_cost"),
    ("QC-05 Orphaned claims",
     """SELECT COUNT(*) AS cnt FROM claims c
        LEFT JOIN patients p ON c.patient_id=p.patient_id
        WHERE p.patient_id IS NULL"""),
    ("QC-06 LOS > 30 days",
     "SELECT COUNT(*) AS cnt FROM claims WHERE length_of_stay > 30"),
    ("QC-07 Duplicate (patient+date+diag+proc)",
     """SELECT SUM(cnt-1) AS cnt FROM (
           SELECT COUNT(*) AS cnt
           FROM claims
           GROUP BY patient_id, service_date, diagnosis_code, procedure_code
           HAVING COUNT(*) > 1)"""),
    ("QC-08 Future-dated claims",
     "SELECT COUNT(*) AS cnt FROM claims WHERE service_date > DATE('now')"),
    ("QC-09 Invalid readmission flag",
     "SELECT COUNT(*) AS cnt FROM claims WHERE readmission_30d NOT IN (0,1)"),
    ("QC-10 Unknown region",
     """SELECT COUNT(*) AS cnt FROM claims
        WHERE region NOT IN ('Northeast','Southeast','Midwest','West','Southwest')"""),
]

def run():
    conn = sqlite3.connect(DB)
    results = []
    print(f"\n{'Check':<45} {'Count':>8}  {'Status'}")
    print("-" * 65)
    for name, sql in CHECKS:
        cnt = pd.read_sql_query(sql, conn)["cnt"].iloc[0] or 0
        status = "✅ PASS" if cnt == 0 else "⚠️  FLAG"
        print(f"{name:<45} {int(cnt):>8}  {status}")
        results.append({"check": name, "flagged_records": int(cnt), "status": status})
    conn.close()

    df = pd.DataFrame(results)
    df.to_csv(OUT, index=False)
    total_flags = df["flagged_records"].sum()
    print(f"\n{'─'*65}")
    print(f"Total flagged records: {int(total_flags):,}")
    print(f"Validation report saved → {OUT}\n")

if __name__ == "__main__":
    run()
