# 🏥 Healthcare Claims Analytics Dashboard

A full-stack analytics dashboard for exploring synthetic healthcare claims data — tracking **readmission rates**, **treatment utilization**, **regional cost variation**, and **quality metrics**.

Built with Python, SQL and Tableau. All data is synthetically generated (no real patient data).

---

## 📸 Dashboard Sections

| Tab | What it shows |
|-----|---------------|
| **Overview** | Executive KPIs, monthly trend, payer mix, regional cost bar |
| **Utilization** | Top diagnoses by volume, facility distribution, readmission cards |
| **Cost Analysis** | Payer payment ratios, regional variation, preventable admission rate |
| **Quality Metrics** | Radar quality score, preventable vs. readmission chart, data validation flags |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev

# 3. Open http://localhost:3000
```

---

## 🗂 Project Structure

```
healthcare-claims-dashboard/
├── index.html                  # HTML shell
├── vite.config.js              # Vite build config
├── package.json
│
├── src/
│   ├── main.jsx                # React entry point
│   ├── App.jsx                 # Main dashboard (all tabs + charts)
│   └── data/
│       └── generateData.js     # Synthetic data generator + aggregation helpers
│
└── sql/
    └── claims_analytics.sql    # Full SQL library (schema, KPIs, validation, views)
```

---

## 📊 Key Metrics Tracked

### Utilization
- Claim volume by diagnosis (ICD-10 codes)
- Facility type distribution (Hospital, Outpatient, Urgent Care, etc.)
- Readmission rates per diagnosis — flagged by severity

### Patient Costs
- Total billed vs. paid by payer
- Average cost per claim by region
- Payment ratio (paid / billed) by insurance type
- Cost by age group and gender

### Quality
- Composite quality score by clinical category
- 30-day readmission rate (benchmark: <10%)
- Preventable admission rate by region
- Data validation: duplicate IDs, outlier costs, missing fields

---

## 🧮 SQL Queries Included

The `sql/claims_analytics.sql` file contains:

1. **Schema definition** with indexes
2. **KPI summary** — executive-level metrics
3. **Readmission analysis** — by region, diagnosis, month; high-risk cohort
4. **Treatment utilization** — procedure and diagnosis breakdowns
5. **Regional cost variation** — with P50/P90 spread, cross-tab by payer
6. **Patient cost analysis** — top spenders, cost by age/gender
7. **Quality metrics** — score distribution, preventable admissions
8. **Data validation** — 8 quality check queries
9. **Reporting views** — `v_monthly_dashboard`, `v_quality_scorecard`

---

## 🔧 Tech Stack

| Layer | Tool |
|-------|------|
| Framework | React 18 |
| Charts | Recharts 2 |
| Build | Vite 5 |
| Data | Synthetic JS generator (seeded random, 2 000 records) |
| SQL | PostgreSQL-compatible DDL + DML |

---

## 📋 Data Dictionary

| Field | Type | Description |
|-------|------|-------------|
| `claimId` | string | Unique claim identifier (`CLM000001`) |
| `patientId` | string | De-identified patient ID |
| `serviceDate` | date | Date of service |
| `region` | string | Geographic region (Northeast / Southeast / Midwest / Southwest / West) |
| `facilityType` | string | Care setting |
| `diagnosis` | object | ICD-10 code, name, clinical category |
| `procedure` | object | CPT code, name, base cost |
| `payer` | string | Insurance type |
| `billedAmount` | number | Charged amount |
| `allowedAmount` | number | Contracted allowed amount |
| `paidAmount` | number | Actual paid amount |
| `patientResponsibility` | number | Patient's portion |
| `lengthOfStay` | integer | Days (0 = outpatient) |
| `readmitted` | boolean | 30-day readmission flag |
| `qualityScore` | number | Composite quality score (0–1) |
| `preventable` | boolean | Preventable admission flag |

---

## ⚠️ Disclaimer

All data in this project is **entirely synthetic** and generated programmatically. It does not represent real patients, providers, or healthcare organizations. This project is for analytical and portfolio demonstration purposes only.

---

## 📄 License

MIT
