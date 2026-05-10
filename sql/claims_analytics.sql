-- ============================================================
-- Healthcare Claims Analytics - SQL Query Library
-- Author: Claims Analytics Team
-- Description: Core analytical queries for claims reporting
-- ============================================================

-- ─────────────────────────────────────────────────
-- 1. SCHEMA DEFINITION
-- ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS claims (
    claim_id          VARCHAR(12)    PRIMARY KEY,
    patient_id        VARCHAR(10)    NOT NULL,
    service_date      DATE           NOT NULL,
    region            VARCHAR(20)    NOT NULL,
    facility_type     VARCHAR(30)    NOT NULL,
    diagnosis_code    VARCHAR(10)    NOT NULL,
    diagnosis_name    VARCHAR(60)    NOT NULL,
    diagnosis_category VARCHAR(40)  NOT NULL,
    procedure_code    VARCHAR(10)    NOT NULL,
    procedure_name    VARCHAR(60)    NOT NULL,
    payer             VARCHAR(20)    NOT NULL,
    age               INTEGER        NOT NULL,
    age_group         VARCHAR(10)    NOT NULL,
    gender            VARCHAR(10)    NOT NULL,
    billed_amount     DECIMAL(12,2)  NOT NULL,
    allowed_amount    DECIMAL(12,2)  NOT NULL,
    paid_amount       DECIMAL(12,2)  NOT NULL,
    patient_responsibility DECIMAL(12,2) NOT NULL,
    length_of_stay    INTEGER        DEFAULT 0,
    readmitted        BOOLEAN        DEFAULT FALSE,
    quality_score     DECIMAL(4,2)   NOT NULL,
    preventable       BOOLEAN        DEFAULT FALSE,
    created_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claims_service_date   ON claims(service_date);
CREATE INDEX idx_claims_region         ON claims(region);
CREATE INDEX idx_claims_payer          ON claims(payer);
CREATE INDEX idx_claims_diagnosis_code ON claims(diagnosis_code);
CREATE INDEX idx_claims_patient_id     ON claims(patient_id);


-- ─────────────────────────────────────────────────
-- 2. KPI SUMMARY
-- ─────────────────────────────────────────────────

-- Overall executive KPIs
SELECT
    COUNT(*)                                           AS total_claims,
    COUNT(DISTINCT patient_id)                         AS unique_patients,
    SUM(billed_amount)                                 AS total_billed,
    SUM(paid_amount)                                   AS total_paid,
    ROUND(AVG(paid_amount), 2)                         AS avg_cost_per_claim,
    ROUND(SUM(paid_amount) / SUM(billed_amount) * 100, 1) AS payment_ratio_pct,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 1) AS readmission_rate_pct,
    ROUND(AVG(CASE WHEN length_of_stay > 0 THEN length_of_stay END), 1) AS avg_los_inpatient,
    ROUND(AVG(quality_score) * 100, 1)                 AS avg_quality_score,
    ROUND(AVG(CASE WHEN preventable THEN 1.0 ELSE 0.0 END) * 100, 1) AS preventable_rate_pct
FROM claims;


-- ─────────────────────────────────────────────────
-- 3. READMISSION ANALYSIS
-- ─────────────────────────────────────────────────

-- 30-day readmission rate by region and diagnosis category
SELECT
    region,
    diagnosis_category,
    COUNT(*)                                                              AS total_claims,
    SUM(CASE WHEN readmitted THEN 1 ELSE 0 END)                          AS readmissions,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2)     AS readmission_rate_pct,
    ROUND(AVG(paid_amount), 2)                                           AS avg_cost,
    ROUND(AVG(length_of_stay), 1)                                        AS avg_los
FROM claims
WHERE length_of_stay > 0          -- Inpatient only
GROUP BY region, diagnosis_category
ORDER BY readmission_rate_pct DESC;


-- Readmission trend by month
SELECT
    DATE_TRUNC('month', service_date)                                    AS month,
    COUNT(*)                                                             AS total_claims,
    SUM(CASE WHEN readmitted THEN 1 ELSE 0 END)                         AS readmissions,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2)    AS readmission_rate_pct
FROM claims
GROUP BY DATE_TRUNC('month', service_date)
ORDER BY month;


-- High-risk readmission cohort (readmitted + high cost + elderly)
SELECT
    patient_id,
    COUNT(*)                   AS claim_count,
    SUM(paid_amount)           AS total_paid,
    MAX(service_date)          AS last_service,
    STRING_AGG(DISTINCT diagnosis_name, ', ') AS diagnoses,
    STRING_AGG(DISTINCT region, ', ')         AS regions
FROM claims
WHERE readmitted = TRUE
  AND age >= 65
GROUP BY patient_id
HAVING COUNT(*) > 1
ORDER BY total_paid DESC
LIMIT 50;


-- ─────────────────────────────────────────────────
-- 4. TREATMENT UTILIZATION
-- ─────────────────────────────────────────────────

-- Procedure utilization summary
SELECT
    procedure_code,
    procedure_name,
    COUNT(*)                                  AS utilization_count,
    COUNT(DISTINCT patient_id)                AS unique_patients,
    ROUND(AVG(paid_amount), 2)                AS avg_paid,
    SUM(paid_amount)                          AS total_paid,
    ROUND(SUM(paid_amount) / SUM(SUM(paid_amount)) OVER () * 100, 2) AS pct_of_total_spend
FROM claims
GROUP BY procedure_code, procedure_name
ORDER BY total_paid DESC;


-- Top diagnoses by claim volume and cost
SELECT
    diagnosis_code,
    diagnosis_name,
    diagnosis_category,
    COUNT(*)                                                          AS claim_count,
    ROUND(AVG(paid_amount), 2)                                        AS avg_paid,
    SUM(paid_amount)                                                  AS total_paid,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2) AS readmission_rate_pct,
    ROUND(AVG(length_of_stay), 1)                                     AS avg_los
FROM claims
GROUP BY diagnosis_code, diagnosis_name, diagnosis_category
ORDER BY claim_count DESC;


-- Facility type utilization
SELECT
    facility_type,
    COUNT(*)                                                           AS claim_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)               AS pct_of_claims,
    ROUND(AVG(paid_amount), 2)                                         AS avg_cost,
    SUM(paid_amount)                                                   AS total_cost,
    ROUND(AVG(CASE WHEN length_of_stay > 0 THEN length_of_stay END), 1) AS avg_los_when_admitted
FROM claims
GROUP BY facility_type
ORDER BY claim_count DESC;


-- ─────────────────────────────────────────────────
-- 5. REGIONAL COST VARIATION
-- ─────────────────────────────────────────────────

-- Regional cost summary with statistical spread
SELECT
    region,
    COUNT(*)                                                          AS claim_count,
    ROUND(AVG(paid_amount), 2)                                        AS avg_paid,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY paid_amount), 2) AS median_paid,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY paid_amount), 2) AS p90_paid,
    MIN(paid_amount)                                                  AS min_paid,
    MAX(paid_amount)                                                  AS max_paid,
    SUM(paid_amount)                                                  AS total_paid,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2) AS readmission_rate_pct,
    ROUND(AVG(quality_score) * 100, 1)                                AS avg_quality
FROM claims
GROUP BY region
ORDER BY avg_paid DESC;


-- Cost variation by region and payer (cross-tab)
SELECT
    region,
    payer,
    COUNT(*)                   AS claims,
    ROUND(AVG(paid_amount), 2) AS avg_paid,
    ROUND(SUM(paid_amount), 2) AS total_paid
FROM claims
GROUP BY region, payer
ORDER BY region, avg_paid DESC;


-- ─────────────────────────────────────────────────
-- 6. PATIENT COST ANALYSIS
-- ─────────────────────────────────────────────────

-- Patient-level cost summary (top spenders)
SELECT
    patient_id,
    COUNT(*)                                  AS claim_count,
    SUM(paid_amount)                          AS total_paid,
    ROUND(AVG(paid_amount), 2)                AS avg_paid,
    MAX(age)                                  AS age,
    STRING_AGG(DISTINCT payer, ', ')          AS payers,
    STRING_AGG(DISTINCT region, ', ')         AS regions,
    SUM(CASE WHEN readmitted THEN 1 ELSE 0 END) AS readmissions,
    SUM(CASE WHEN preventable THEN 1 ELSE 0 END) AS preventable_events
FROM claims
GROUP BY patient_id
ORDER BY total_paid DESC
LIMIT 100;


-- Cost by age group and gender
SELECT
    age_group,
    gender,
    COUNT(*)                                  AS claim_count,
    ROUND(AVG(paid_amount), 2)                AS avg_paid,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2) AS readmission_rate_pct,
    SUM(paid_amount)                          AS total_paid
FROM claims
GROUP BY age_group, gender
ORDER BY age_group, gender;


-- ─────────────────────────────────────────────────
-- 7. QUALITY METRICS
-- ─────────────────────────────────────────────────

-- Quality score distribution by diagnosis category
SELECT
    diagnosis_category,
    COUNT(*)                                                          AS claim_count,
    ROUND(AVG(quality_score) * 100, 1)                               AS avg_quality_pct,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY quality_score) * 100, 1) AS q25,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY quality_score) * 100, 1) AS q75,
    ROUND(AVG(CASE WHEN preventable THEN 1.0 ELSE 0.0 END) * 100, 2) AS preventable_rate_pct,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2) AS readmission_rate_pct
FROM claims
GROUP BY diagnosis_category
ORDER BY avg_quality_pct;


-- Preventable admission analysis
SELECT
    diagnosis_name,
    region,
    payer,
    COUNT(*)                   AS total_claims,
    SUM(CASE WHEN preventable THEN 1 ELSE 0 END)                        AS preventable_count,
    ROUND(AVG(CASE WHEN preventable THEN 1.0 ELSE 0.0 END) * 100, 2)   AS preventable_rate_pct,
    SUM(CASE WHEN preventable THEN paid_amount ELSE 0 END)              AS preventable_spend
FROM claims
GROUP BY diagnosis_name, region, payer
HAVING SUM(CASE WHEN preventable THEN 1 ELSE 0 END) > 0
ORDER BY preventable_spend DESC;


-- ─────────────────────────────────────────────────
-- 8. DATA VALIDATION QUERIES
-- ─────────────────────────────────────────────────

-- Check for duplicate claim IDs
SELECT claim_id, COUNT(*) AS cnt
FROM claims
GROUP BY claim_id
HAVING COUNT(*) > 1;

-- Check for negative amounts
SELECT claim_id, billed_amount, allowed_amount, paid_amount, patient_responsibility
FROM claims
WHERE billed_amount < 0
   OR allowed_amount < 0
   OR paid_amount < 0
   OR patient_responsibility < 0;

-- Check for logically invalid amounts (paid > billed)
SELECT claim_id, billed_amount, paid_amount
FROM claims
WHERE paid_amount > billed_amount * 1.05;  -- 5% tolerance

-- Check for future service dates
SELECT claim_id, service_date
FROM claims
WHERE service_date > CURRENT_DATE;

-- Check for missing required fields
SELECT
    SUM(CASE WHEN patient_id IS NULL OR patient_id = '' THEN 1 ELSE 0 END) AS missing_patient_id,
    SUM(CASE WHEN diagnosis_code IS NULL OR diagnosis_code = '' THEN 1 ELSE 0 END) AS missing_dx_code,
    SUM(CASE WHEN service_date IS NULL THEN 1 ELSE 0 END) AS missing_service_date,
    SUM(CASE WHEN payer IS NULL OR payer = '' THEN 1 ELSE 0 END) AS missing_payer,
    SUM(CASE WHEN region IS NULL OR region = '' THEN 1 ELSE 0 END) AS missing_region
FROM claims;

-- Outlier detection: costs > 3 standard deviations from mean
WITH stats AS (
    SELECT AVG(paid_amount) AS mean_paid, STDDEV(paid_amount) AS std_paid FROM claims
)
SELECT c.claim_id, c.paid_amount, c.diagnosis_name, c.procedure_name,
       ROUND((c.paid_amount - s.mean_paid) / s.std_paid, 2) AS z_score
FROM claims c, stats s
WHERE ABS(c.paid_amount - s.mean_paid) > 3 * s.std_paid
ORDER BY z_score DESC;


-- ─────────────────────────────────────────────────
-- 9. DASHBOARD REPORTING VIEWS
-- ─────────────────────────────────────────────────

-- Monthly dashboard rollup view
CREATE OR REPLACE VIEW v_monthly_dashboard AS
SELECT
    DATE_TRUNC('month', service_date)                                    AS report_month,
    region,
    payer,
    diagnosis_category,
    COUNT(*)                                                             AS claim_count,
    SUM(billed_amount)                                                   AS total_billed,
    SUM(paid_amount)                                                     AS total_paid,
    ROUND(AVG(paid_amount), 2)                                           AS avg_paid,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2)    AS readmission_rate,
    ROUND(AVG(quality_score) * 100, 1)                                   AS avg_quality,
    SUM(CASE WHEN preventable THEN 1 ELSE 0 END)                        AS preventable_count
FROM claims
GROUP BY 1, 2, 3, 4;

-- Quality scorecard view
CREATE OR REPLACE VIEW v_quality_scorecard AS
SELECT
    region,
    diagnosis_category,
    COUNT(*)                                                              AS claims,
    ROUND(AVG(quality_score) * 100, 1)                                   AS quality_score,
    ROUND(AVG(CASE WHEN readmitted THEN 1.0 ELSE 0.0 END) * 100, 2)    AS readmission_rate,
    ROUND(AVG(CASE WHEN preventable THEN 1.0 ELSE 0.0 END) * 100, 2)   AS preventable_rate,
    ROUND(AVG(paid_amount), 2)                                           AS avg_cost,
    CASE
        WHEN AVG(quality_score) >= 0.80 THEN 'High'
        WHEN AVG(quality_score) >= 0.65 THEN 'Medium'
        ELSE 'Low'
    END AS quality_tier
FROM claims
GROUP BY region, diagnosis_category;
