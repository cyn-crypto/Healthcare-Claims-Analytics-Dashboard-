# Healthcare Claims Analytics Dashboard

A complete end-to-end analytics project demonstrating healthcare claims data analysis using **Python**, **SQL**, **Tableau**, and **Power BI**.

---

## 📁 Project Structure

```
healthcare-claims-analytics/
├── data/
│   ├── patients.csv              # 2,000 synthetic patients
│   ├── claims.csv                # 15,000 synthetic claims (2022–2024)
│   ├── quality_metrics.csv       # Pre-aggregated regional quality KPIs
│   └── claims.db                 # SQLite database (auto-generated)
│
├── sql/
│   └── analytics_queries.sql     # Schema DDL + 20+ analytical SQL queries
│
├── python/
│   ├── generate_data.py          # Synthetic data generator (numpy/pandas)
│   ├── analytics.py              # Full analytics pipeline → 8 chart outputs
│   └── data_validation.py        # 10 QC checks on patient-level data
│
├── dashboard/
│   ├── 01_kpi_summary.png           # Executive KPI summary + sparklines
│   ├── 02_regional_cost.png         # Regional cost variation
│   ├── 03_readmission_analysis.png  # 30-day readmission analysis
│   ├── 04_payer_analysis.png        # Payer mix & coverage
│   ├── 05_utilization_heatmap.png   # Facility × Region heatmap
│   ├── 06_cost_trend.png            # Monthly & YoY cost trends
│   ├── 07_quality_metrics.png       # Denial rate & quality KPIs
│   ├── 08_demographics.png          # Patient demographics & stratification
│   ├── healthcare_claims_analytics.xlsx   # Tableau/Power BI ready workbook
│   ├── data_validation_report.csv         # QC results
│   ├── tableau_setup_guide.xml            # Tableau connection + calc fields
│   └── powerbi_setup.m                    # Power Query M + DAX measures
│
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install pandas numpy matplotlib seaborn openpyxl
```

### 2. Generate synthetic data
```bash
python python/generate_data.py
```

### 3. Run data validation
```bash
python python/data_validation.py
```

### 4. Generate all charts and Excel export
```bash
python python/analytics.py
```

---

## 📊 Dashboard Outputs

| Chart | Description |
|-------|-------------|
| 01 KPI Summary | Total spend, claims, avg cost, readmit %, denial rate + sparkline |
| 02 Regional Cost | Bar + bubble chart of avg cost and total spend by region |
| 03 Readmission | By region, by diagnosis, trend by year |
| 04 Payer Analysis | Volume pie, billed vs paid bar, coverage rate |
| 05 Utilization Heatmap | Claim count matrix: facility type × region |
| 06 Cost Trend | Monthly spend over 3 years + regional YoY lines |
| 07 Quality Metrics | Denial rate, avg LOS, ER visit rate |
| 08 Demographics | Cost by age group, chronic conditions, gender split |

---

## 🗄️ Key SQL Analyses

- **Utilization**: Monthly volume trend, facility mix, top diagnoses
- **Cost**: Regional variation, payer coverage, high-cost cohort (top 5%)
- **Readmissions**: By region, diagnosis, year, chronic condition count
- **Claims Management**: Denial rate by payer, claim status distribution
- **YoY Comparison**: Window functions for year-over-year cost change %

---

## 📋 Data Validation (10 QC Rules)

| Check | Description |
|-------|-------------|
| QC-01 | Null patient IDs |
| QC-02 | Null service dates |
| QC-03 | Non-positive costs |
| QC-04 | Paid > billed (overpayments) |
| QC-05 | Orphaned claims (missing patient) |
| QC-06 | LOS > 30 days |
| QC-07 | Duplicate claims |
| QC-08 | Future-dated claims |
| QC-09 | Invalid readmission flags |
| QC-10 | Unknown region codes |

---

## 🔗 Tableau / Power BI

1. Open `dashboard/healthcare_claims_analytics.xlsx`
2. Import all 6 sheets as separate tables
3. Follow `tableau_setup_guide.xml` or `powerbi_setup.m` for calculated fields, DAX measures, and recommended dashboard layouts
4. Use the provided color palette: Teal `#00B4D8`, Coral `#FF6B6B`, Amber `#FFB347`, Mint `#52C8A4`

---

## 🔧 Tech Stack

| Tool | Purpose |
|------|---------|
| Python / pandas / numpy | Data generation, analytics pipeline |
| Matplotlib | Chart generation (8 dashboard panels) |
| SQLite / SQL | Data storage, analytical queries |
| OpenPyXL | Excel workbook export |
| Tableau / Power BI | Interactive BI dashboards (via xlsx import) |

---

## 📌 Key Findings (Synthetic Data)

- **Northeast** and **West** show ~25% higher avg claim costs vs Southwest
- **30-day readmission rates** increase significantly with each additional chronic condition
- **Self-Pay** payers have the lowest coverage rate (~45%), creating highest OOP burden
- **Hospital** facility claims represent the highest avg cost and longest LOS
- **Denial rates** vary by payer; rates >5% flagged as operational risk
