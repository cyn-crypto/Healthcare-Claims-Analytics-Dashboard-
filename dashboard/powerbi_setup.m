// ═══════════════════════════════════════════════════════════════════════════════
// Healthcare Claims Analytics – Power BI Setup
// Power Query M transformations + DAX Measures
// ═══════════════════════════════════════════════════════════════════════════════

// ────────────────────────────────────────────────────────────────────────────
// STEP 1 – Load Excel file (paste in Power Query Advanced Editor)
// ────────────────────────────────────────────────────────────────────────────

// Claims_Summary table
let
    Source          = Excel.Workbook(File.Contents("healthcare_claims_analytics.xlsx"), null, true),
    Claims_Sheet    = Source{[Item="Claims_Summary",Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Claims_Sheet, [PromoteAllScalars=true]),
    ChangedTypes    = Table.TransformColumnTypes(PromotedHeaders,{
        {"service_year",   Int64.Type},
        {"total_spend",    type number},
        {"avg_cost",       type number},
        {"claims",         Int64.Type},
        {"readmissions",   Int64.Type},
        {"readmit_pct",    type number}
    })
in
    ChangedTypes


// ────────────────────────────────────────────────────────────────────────────
// STEP 2 – Date Table (calculated)
// ────────────────────────────────────────────────────────────────────────────
// In DAX (Model view → New table):
DateTable =
ADDCOLUMNS(
    CALENDAR(DATE(2022,1,1), DATE(2024,12,31)),
    "Year",         YEAR([Date]),
    "Quarter",      "Q" & FORMAT(ROUNDUP(MONTH([Date])/3,0),"0"),
    "Month",        MONTH([Date]),
    "MonthName",    FORMAT([Date],"MMM"),
    "YearMonth",    FORMAT([Date],"YYYY-MM")
)


// ────────────────────────────────────────────────────────────────────────────
// STEP 3 – DAX Measures (create in the Claims_Summary table)
// ────────────────────────────────────────────────────────────────────────────

// Core KPIs
Total Spend ($M) =
DIVIDE(SUMX(Claims_Summary, Claims_Summary[total_spend]), 1000000)

Total Claims =
SUM(Claims_Summary[claims])

Avg Cost per Claim =
DIVIDE(SUM(Claims_Summary[total_spend]), SUM(Claims_Summary[claims]))

Readmission Rate % =
DIVIDE(SUM(Claims_Summary[readmissions]), SUM(Claims_Summary[claims])) * 100

// YoY comparisons
Spend YoY % =
VAR CurrentYear  = CALCULATE([Total Spend ($M)], FILTER(ALL(Claims_Summary[service_year]),
                   Claims_Summary[service_year] = MAX(Claims_Summary[service_year])))
VAR PrevYear     = CALCULATE([Total Spend ($M)], FILTER(ALL(Claims_Summary[service_year]),
                   Claims_Summary[service_year] = MAX(Claims_Summary[service_year]) - 1))
RETURN DIVIDE(CurrentYear - PrevYear, PrevYear) * 100

// Ranking
Region Rank by Cost =
RANKX(ALL(Claims_Summary[region]),
      CALCULATE([Avg Cost per Claim]),, DESC, Dense)

// Conditional formatting measure for denial rate
Denial Color =
IF([Denial Rate %] > 5, "#FF6B6B",
   IF([Denial Rate %] > 3, "#FFB347", "#52C8A4"))

Denial Rate % =
DIVIDE(
    CALCULATE(SUM(Payer_Analysis[claims]),
              FILTER(Payer_Analysis, Payer_Analysis[denial_rate_pct] > 0)),
    SUM(Payer_Analysis[claims])
) * 100


// ────────────────────────────────────────────────────────────────────────────
// STEP 4 – Recommended Visuals Layout
// ────────────────────────────────────────────────────────────────────────────
/*
PAGE 1 – Executive Summary
  ┌─────────────────────────────────────────────────────────────┐
  │  [Card] Total Spend  [Card] Claims  [Card] Avg Cost  [Card] Readmit%  │
  ├────────────────────────┬────────────────────────────────────┤
  │  Line – Monthly Spend  │  Donut – Payer Mix                 │
  ├────────────────────────┴────────────────────────────────────┤
  │  Bar – Avg Cost by Region (sorted DESC)                      │
  └─────────────────────────────────────────────────────────────┘

PAGE 2 – Readmission Deep-Dive
  ┌──────────────────┬──────────────────────────────────────────┐
  │  Matrix          │  Bar – Readmit by Diagnosis              │
  │  Region × Year   │                                          │
  │  (readmit_pct)   ├──────────────────────────────────────────┤
  │                  │  Line – Readmit Trend by Year            │
  └──────────────────┴──────────────────────────────────────────┘

PAGE 3 – Cost & Regional Analysis
  Filled Map → Region colored by avg_cost
  Scatter     → total_spend vs readmit_pct (size = claims)

PAGE 4 – Patient Cohort
  Histogram – Age groups vs avg_cost
  Scatter   – chronic_conditions vs total_cost

SLICERS (all pages):
  service_year | region | payer | facility_type
*/
