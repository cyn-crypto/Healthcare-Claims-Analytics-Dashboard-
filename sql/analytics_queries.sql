-- =============================================================================
-- Healthcare Claims Analytics – Schema & Analytical Queries
-- Compatible with: PostgreSQL 14+  |  SQLite 3.38+
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 1 – TABLE DEFINITIONS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS patients (
    patient_id          INTEGER PRIMARY KEY,
    age                 INTEGER        NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender              VARCHAR(10)    NOT NULL,
    region              VARCHAR(50)    NOT NULL,
    payer               VARCHAR(50)    NOT NULL,
    zip_code            VARCHAR(10),
    chronic_conditions  INTEGER        DEFAULT 0,
    enrollment_date     DATE
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id            INTEGER PRIMARY KEY,
    patient_id          INTEGER        NOT NULL REFERENCES patients(patient_id),
    service_date        DATE           NOT NULL,
    service_year        INTEGER,
    service_month       INTEGER,
    service_quarter     VARCHAR(2),
    diagnosis_code      VARCHAR(10)    NOT NULL,
    diagnosis_desc      VARCHAR(100),
    procedure_code      VARCHAR(10)    NOT NULL,
    procedure_desc      VARCHAR(100),
    facility_type       VARCHAR(50),
    region              VARCHAR(50),
    payer               VARCHAR(50),
    total_cost          NUMERIC(12,2),
    paid_amount         NUMERIC(12,2),
    patient_oop         NUMERIC(12,2),
    length_of_stay      INTEGER        DEFAULT 0,
    readmission_30d     INTEGER        DEFAULT 0 CHECK (readmission_30d IN (0,1)),
    claim_status        VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS quality_metrics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    region              VARCHAR(50),
    year                INTEGER,
    total_claims        INTEGER,
    avg_cost_per_claim  NUMERIC(12,2),
    total_spend         NUMERIC(14,2),
    readmission_rate_pct NUMERIC(6,2),
    denial_rate_pct     NUMERIC(6,2),
    avg_los_hospital    NUMERIC(6,2),
    er_visit_rate_pct   NUMERIC(6,2)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_claims_patient    ON claims(patient_id);
CREATE INDEX IF NOT EXISTS idx_claims_date       ON claims(service_date);
CREATE INDEX IF NOT EXISTS idx_claims_region     ON claims(region);
CREATE INDEX IF NOT EXISTS idx_claims_payer      ON claims(payer);
CREATE INDEX IF NOT EXISTS idx_claims_diagnosis  ON claims(diagnosis_code);
CREATE INDEX IF NOT EXISTS idx_claims_facility   ON claims(facility_type);
CREATE INDEX IF NOT EXISTS idx_claims_status     ON claims(claim_status);


-- =============================================================================
-- SECTION 2 – DATA VALIDATION & QUALITY CHECKS
-- =============================================================================

-- QC-01: Null / missing critical fields
SELECT 'QC-01 Null critical fields' AS check_name,
       SUM(CASE WHEN patient_id   IS NULL THEN 1 ELSE 0 END) AS null_patient_id,
       SUM(CASE WHEN service_date IS NULL THEN 1 ELSE 0 END) AS null_service_date,
       SUM(CASE WHEN total_cost   IS NULL THEN 1 ELSE 0 END) AS null_total_cost,
       SUM(CASE WHEN diagnosis_code IS NULL THEN 1 ELSE 0 END) AS null_diag_code
FROM claims;

-- QC-02: Negative or zero costs
SELECT 'QC-02 Non-positive costs' AS check_name,
       COUNT(*) AS records_flagged
FROM claims
WHERE total_cost <= 0 OR paid_amount < 0;

-- QC-03: Paid > billed (overpayment anomaly)
SELECT 'QC-03 Overpayment anomaly' AS check_name,
       COUNT(*) AS records_flagged,
       ROUND(AVG(paid_amount - total_cost), 2) AS avg_overpayment
FROM claims
WHERE paid_amount > total_cost;

-- QC-04: Orphaned claims (patient not in patients table)
SELECT 'QC-04 Orphaned claims' AS check_name,
       COUNT(*) AS records_flagged
FROM claims c
LEFT JOIN patients p ON c.patient_id = p.patient_id
WHERE p.patient_id IS NULL;

-- QC-05: Unrealistic length of stay
SELECT 'QC-05 LOS > 30 days (review)' AS check_name,
       COUNT(*) AS records_flagged
FROM claims
WHERE length_of_stay > 30;

-- QC-06: Duplicate claim check
SELECT 'QC-06 Duplicate claims' AS check_name,
       COUNT(*) AS duplicate_groups
FROM (
    SELECT patient_id, service_date, diagnosis_code, procedure_code,
           COUNT(*) AS cnt
    FROM claims
    GROUP BY patient_id, service_date, diagnosis_code, procedure_code
    HAVING COUNT(*) > 1
) dup;

-- QC-07: Future-dated claims
SELECT 'QC-07 Future-dated claims' AS check_name,
       COUNT(*) AS records_flagged
FROM claims
WHERE service_date > CURRENT_DATE;


-- =============================================================================
-- SECTION 3 – CORE ANALYTICS QUERIES
-- =============================================================================

-- ── A. Healthcare Utilization ─────────────────────────────────────────────────

-- A1: Monthly claim volume trend
SELECT service_year,
       service_month,
       COUNT(*)                          AS total_claims,
       ROUND(AVG(total_cost), 2)         AS avg_claim_cost,
       ROUND(SUM(total_cost), 2)         AS total_spend
FROM claims
GROUP BY service_year, service_month
ORDER BY service_year, service_month;

-- A2: Utilization by facility type
SELECT facility_type,
       COUNT(*)                                    AS claim_count,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
       ROUND(AVG(total_cost), 2)                   AS avg_cost,
       ROUND(SUM(total_cost), 2)                   AS total_spend
FROM claims
GROUP BY facility_type
ORDER BY claim_count DESC;

-- A3: Top 10 diagnosis codes by volume & cost
SELECT diagnosis_code,
       diagnosis_desc,
       COUNT(*)                          AS claim_count,
       ROUND(AVG(total_cost), 2)         AS avg_cost,
       ROUND(SUM(total_cost), 2)         AS total_cost
FROM claims
GROUP BY diagnosis_code, diagnosis_desc
ORDER BY claim_count DESC
LIMIT 10;

-- A4: Procedure utilization rate
SELECT procedure_code,
       procedure_desc,
       COUNT(*)                          AS times_performed,
       ROUND(AVG(total_cost), 2)         AS avg_cost
FROM claims
GROUP BY procedure_code, procedure_desc
ORDER BY times_performed DESC;


-- ── B. Cost Analysis ──────────────────────────────────────────────────────────

-- B1: Cost by payer (allowed vs paid vs OOP)
SELECT payer,
       COUNT(*)                          AS claims,
       ROUND(AVG(total_cost), 2)         AS avg_allowed,
       ROUND(AVG(paid_amount), 2)        AS avg_paid,
       ROUND(AVG(patient_oop), 2)        AS avg_oop,
       ROUND(100.0 * AVG(paid_amount) / NULLIF(AVG(total_cost),0), 1) AS payer_coverage_pct
FROM claims
GROUP BY payer
ORDER BY avg_allowed DESC;

-- B2: Regional cost variation
SELECT region,
       COUNT(*)                          AS claims,
       ROUND(AVG(total_cost), 2)         AS avg_cost,
       ROUND(MIN(total_cost), 2)         AS min_cost,
       ROUND(MAX(total_cost), 2)         AS max_cost,
       ROUND(SUM(total_cost), 2)         AS total_spend
FROM claims
GROUP BY region
ORDER BY avg_cost DESC;

-- B3: Cost percentiles by region (PostgreSQL window functions)
SELECT region,
       ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_cost)::NUMERIC, 2) AS p25,
       ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_cost)::NUMERIC, 2) AS median,
       ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_cost)::NUMERIC, 2) AS p75,
       ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_cost)::NUMERIC, 2) AS p90,
       ROUND(AVG(total_cost)::NUMERIC, 2)                                           AS mean
FROM claims
GROUP BY region
ORDER BY median DESC;

-- B4: High-cost claimant cohort (top 5 %)
WITH ranked AS (
    SELECT patient_id,
           SUM(total_cost) AS total_patient_cost,
           NTILE(20) OVER (ORDER BY SUM(total_cost) DESC) AS cost_quintile_20
    FROM claims
    GROUP BY patient_id
)
SELECT 'Top 5% high-cost patients' AS cohort,
       COUNT(*)                    AS patient_count,
       ROUND(SUM(total_patient_cost), 2) AS cohort_spend,
       ROUND(100.0 * SUM(total_patient_cost) /
             (SELECT SUM(total_cost) FROM claims), 2) AS pct_of_total_spend
FROM ranked
WHERE cost_quintile_20 = 1;


-- ── C. Readmission Analysis ───────────────────────────────────────────────────

-- C1: 30-day readmission rate by region
SELECT region,
       COUNT(*)                                           AS hospital_claims,
       SUM(readmission_30d)                               AS readmissions,
       ROUND(100.0 * SUM(readmission_30d) / COUNT(*), 2) AS readmission_rate_pct
FROM claims
WHERE facility_type = 'Hospital'
GROUP BY region
ORDER BY readmission_rate_pct DESC;

-- C2: Readmission rate by diagnosis
SELECT diagnosis_code,
       diagnosis_desc,
       COUNT(*)                                           AS hospital_admits,
       SUM(readmission_30d)                               AS readmissions,
       ROUND(100.0 * SUM(readmission_30d) / COUNT(*), 2) AS readmission_rate_pct,
       ROUND(AVG(total_cost), 2)                          AS avg_cost
FROM claims
WHERE facility_type = 'Hospital'
GROUP BY diagnosis_code, diagnosis_desc
HAVING COUNT(*) >= 10
ORDER BY readmission_rate_pct DESC;

-- C3: Readmission rate trend by year
SELECT service_year,
       COUNT(*)                                           AS hospital_claims,
       SUM(readmission_30d)                               AS readmissions,
       ROUND(100.0 * SUM(readmission_30d) / COUNT(*), 2) AS readmission_rate_pct
FROM claims
WHERE facility_type = 'Hospital'
GROUP BY service_year
ORDER BY service_year;

-- C4: Chronic-condition impact on readmissions
SELECT p.chronic_conditions,
       COUNT(c.claim_id)                                  AS hospital_claims,
       SUM(c.readmission_30d)                             AS readmissions,
       ROUND(100.0 * SUM(c.readmission_30d) / COUNT(*), 2) AS readmission_rate_pct,
       ROUND(AVG(c.total_cost), 2)                        AS avg_cost
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
WHERE c.facility_type = 'Hospital'
GROUP BY p.chronic_conditions
ORDER BY p.chronic_conditions;


-- ── D. Denial & Claims Management ─────────────────────────────────────────────

-- D1: Denial rate by payer
SELECT payer,
       COUNT(*)                                              AS total_claims,
       SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied,
       ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                  AS denial_rate_pct
FROM claims
GROUP BY payer
ORDER BY denial_rate_pct DESC;

-- D2: Claim status distribution
SELECT claim_status,
       COUNT(*)                                        AS claims,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct,
       ROUND(SUM(total_cost), 2)                       AS value_at_risk
FROM claims
GROUP BY claim_status;


-- ── E. Patient-Level Summary (for Tableau patient detail view) ────────────────

CREATE VIEW IF NOT EXISTS vw_patient_summary AS
SELECT  p.patient_id,
        p.age,
        p.gender,
        p.region,
        p.payer,
        p.chronic_conditions,
        COUNT(c.claim_id)                   AS total_claims,
        ROUND(SUM(c.total_cost),  2)        AS total_cost,
        ROUND(AVG(c.total_cost),  2)        AS avg_cost_per_claim,
        ROUND(SUM(c.patient_oop), 2)        AS total_oop,
        SUM(c.readmission_30d)              AS readmissions,
        MAX(c.service_date)                 AS last_service_date
FROM patients p
LEFT JOIN claims c ON p.patient_id = c.patient_id
GROUP BY p.patient_id, p.age, p.gender, p.region,
         p.payer, p.chronic_conditions;


-- ── F. YOY Cost Comparison ────────────────────────────────────────────────────

WITH yearly AS (
    SELECT region, service_year,
           ROUND(AVG(total_cost), 2) AS avg_cost
    FROM claims
    GROUP BY region, service_year
)
SELECT  a.region,
        a.service_year                             AS year,
        a.avg_cost                                 AS avg_cost,
        LAG(a.avg_cost) OVER (PARTITION BY a.region ORDER BY a.service_year) AS prev_year_cost,
        ROUND(100.0 * (a.avg_cost - LAG(a.avg_cost) OVER
              (PARTITION BY a.region ORDER BY a.service_year))
              / NULLIF(LAG(a.avg_cost) OVER
              (PARTITION BY a.region ORDER BY a.service_year), 0), 2) AS yoy_pct_change
FROM yearly a
ORDER BY a.region, a.service_year;
