"""
Healthcare Claims Analytics
Runs all SQL queries against SQLite, produces Matplotlib/Plotly charts,
and exports a summary Excel workbook — ready to import into Tableau / Power BI.
"""

import os, sqlite3, textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

BASE   = os.path.dirname(os.path.abspath(__file__))
DATA   = os.path.join(BASE, "..", "data")
OUT    = os.path.join(BASE, "..", "dashboard")
DB     = os.path.join(DATA, "claims.db")
os.makedirs(OUT, exist_ok=True)

# ── Palette ────────────────────────────────────────────────────────────────────
TEAL     = "#00B4D8"
NAVY     = "#03045E"
SKY      = "#90E0EF"
CORAL    = "#FF6B6B"
AMBER    = "#FFB347"
MINT     = "#52C8A4"
LAVENDER = "#A78BFA"
SLATE    = "#1E293B"
BG       = "#F0F4F8"
ACCENT_PALETTE = [TEAL, CORAL, AMBER, MINT, LAVENDER, "#F97316", "#EC4899"]
REGION_COLORS  = dict(zip(
    ["Northeast","West","Midwest","Southeast","Southwest"],
    [TEAL, CORAL, AMBER, MINT, LAVENDER]
))

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   "white",
    "axes.edgecolor":   "#CBD5E1",
    "axes.labelcolor":  SLATE,
    "xtick.color":      SLATE,
    "ytick.color":      SLATE,
    "text.color":       SLATE,
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "grid.color":       "#E2E8F0",
    "grid.linewidth":   0.6,
})


# ── DB helpers ─────────────────────────────────────────────────────────────────
def load_db():
    """Load CSVs into SQLite in-memory-ish file."""
    conn = sqlite3.connect(DB)
    for name in ["patients", "claims", "quality_metrics"]:
        df = pd.read_csv(f"{DATA}/{name}.csv")
        df.to_sql(name, conn, if_exists="replace", index=False)
    return conn

def q(conn, sql):
    return pd.read_sql_query(textwrap.dedent(sql), conn)


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1 – Executive KPI Summary (4 big numbers + sparklines)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_kpi_summary(conn, out):
    claims   = q(conn, "SELECT * FROM claims")
    patients = q(conn, "SELECT * FROM patients")

    total_spend   = claims["total_cost"].sum()
    total_claims  = len(claims)
    avg_cost      = claims["total_cost"].mean()
    readmit_rate  = claims[claims["facility_type"]=="Hospital"]["readmission_30d"].mean()*100
    denial_rate   = (claims["claim_status"]=="Denied").mean()*100

    monthly = (claims.groupby(["service_year","service_month"])["total_cost"]
               .sum().reset_index().sort_values(["service_year","service_month"]))
    months  = range(len(monthly))
    spend_vals = monthly["total_cost"].values

    fig = plt.figure(figsize=(16, 5), facecolor=BG)
    fig.suptitle("Healthcare Claims Analytics — Executive Dashboard",
                 fontsize=18, fontweight="bold", color=NAVY, y=1.01)

    kpis = [
        ("Total Spend",     f"${total_spend/1e6:.1f}M",  TEAL),
        ("Total Claims",    f"{total_claims:,}",          CORAL),
        ("Avg Cost/Claim",  f"${avg_cost:,.0f}",          AMBER),
        ("30-d Readmit %",  f"{readmit_rate:.1f}%",       MINT),
        ("Denial Rate",     f"{denial_rate:.1f}%",        LAVENDER),
    ]

    gs = gridspec.GridSpec(1, len(kpis)+1, figure=fig,
                           width_ratios=[1]*len(kpis)+[1.5], wspace=0.3)

    for i, (label, val, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[i])
        ax.set_facecolor("white")
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
        # card
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.05,0.05), 0.9, 0.9, boxstyle="round,pad=0.03",
            linewidth=2, edgecolor=color, facecolor="white",
            transform=ax.transAxes, zorder=2))
        ax.text(0.5, 0.68, val,  ha="center", va="center",
                fontsize=22, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.35, label, ha="center", va="center",
                fontsize=10, color=SLATE, transform=ax.transAxes)

    # Sparkline
    ax_sp = fig.add_subplot(gs[-1])
    ax_sp.set_facecolor("white")
    ax_sp.fill_between(months, spend_vals/1e6, alpha=0.25, color=TEAL)
    ax_sp.plot(months, spend_vals/1e6, color=TEAL, lw=2)
    ax_sp.set_title("Monthly Spend ($M)", fontsize=10, color=SLATE)
    ax_sp.set_xlabel("Month Index", fontsize=8)
    ax_sp.set_ylabel("$M", fontsize=8)

    plt.tight_layout()
    path = f"{out}/01_kpi_summary.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2 – Regional Cost Variation (bar + map-style heatmap)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_regional_cost(conn, out):
    df = q(conn, """
        SELECT region,
               ROUND(AVG(total_cost),2)  AS avg_cost,
               ROUND(SUM(total_cost),2)  AS total_spend,
               COUNT(*)                  AS claims
        FROM claims
        GROUP BY region
        ORDER BY avg_cost DESC
    """)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG)
    fig.suptitle("Regional Cost Variation", fontsize=15, fontweight="bold", color=NAVY)

    # Bar
    ax = axes[0]
    colors = [REGION_COLORS[r] for r in df["region"]]
    bars = ax.barh(df["region"], df["avg_cost"], color=colors, height=0.6,
                   edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, fmt="$%.0f", padding=4, fontsize=9, color=SLATE)
    ax.set_xlabel("Avg Cost per Claim ($)")
    ax.set_title("Average Claim Cost by Region", fontsize=11, color=SLATE)
    ax.grid(axis="x", linestyle="--")

    # Bubble / scatter representing total spend
    ax2 = axes[1]
    x = np.arange(len(df))
    sizes = (df["total_spend"] / df["total_spend"].max()) * 3000
    scatter = ax2.scatter(x, df["avg_cost"], s=sizes, c=colors, alpha=0.8,
                          edgecolors="white", linewidth=1.5, zorder=3)
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["region"], rotation=15, ha="right")
    ax2.set_ylabel("Avg Cost ($)")
    ax2.set_title("Bubble = Total Spend Volume", fontsize=11, color=SLATE)
    ax2.grid(True, linestyle="--")

    for xi, row in zip(x, df.itertuples()):
        ax2.annotate(f"${row.total_spend/1e6:.1f}M",
                     (xi, row.avg_cost), textcoords="offset points",
                     xytext=(0, 14), ha="center", fontsize=8, color=SLATE)

    plt.tight_layout()
    path = f"{out}/02_regional_cost.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 – Readmission Rate Analysis
# ═══════════════════════════════════════════════════════════════════════════════
def chart_readmission(conn, out):
    by_region = q(conn, """
        SELECT region,
               ROUND(100.0*SUM(readmission_30d)/COUNT(*),2) AS readmit_pct,
               COUNT(*) AS admits
        FROM claims WHERE facility_type='Hospital'
        GROUP BY region ORDER BY readmit_pct DESC
    """)

    by_diag = q(conn, """
        SELECT diagnosis_desc,
               ROUND(100.0*SUM(readmission_30d)/COUNT(*),2) AS readmit_pct,
               COUNT(*) AS admits
        FROM claims WHERE facility_type='Hospital'
        GROUP BY diagnosis_desc
        HAVING COUNT(*) >= 10
        ORDER BY readmit_pct DESC LIMIT 8
    """)

    by_year = q(conn, """
        SELECT service_year,
               ROUND(100.0*SUM(readmission_30d)/COUNT(*),2) AS readmit_pct
        FROM claims WHERE facility_type='Hospital'
        GROUP BY service_year ORDER BY service_year
    """)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), facecolor=BG)
    fig.suptitle("30-Day Readmission Analysis", fontsize=15, fontweight="bold", color=NAVY)

    # By region
    colors = [REGION_COLORS[r] for r in by_region["region"]]
    bars = axes[0].bar(by_region["region"], by_region["readmit_pct"],
                       color=colors, edgecolor="white", linewidth=0.5)
    axes[0].bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    axes[0].set_ylim(0, by_region["readmit_pct"].max()*1.25)
    axes[0].set_title("By Region", fontsize=11)
    axes[0].set_ylabel("30-d Readmission Rate (%)")
    axes[0].tick_params(axis="x", rotation=15)

    # By diagnosis (horizontal)
    pal = ACCENT_PALETTE[:len(by_diag)]
    h = axes[1].barh(by_diag["diagnosis_desc"], by_diag["readmit_pct"],
                     color=pal, edgecolor="white")
    axes[1].bar_label(h, fmt="%.1f%%", padding=3, fontsize=8)
    axes[1].set_title("By Diagnosis", fontsize=11)
    axes[1].set_xlabel("30-d Readmit %")
    axes[1].invert_yaxis()

    # Trend by year
    axes[2].plot(by_year["service_year"], by_year["readmit_pct"],
                 marker="o", color=TEAL, lw=2.5, markersize=8, zorder=3)
    for _, row in by_year.iterrows():
        axes[2].annotate(f"{row.readmit_pct:.1f}%",
                         (row.service_year, row.readmit_pct),
                         textcoords="offset points", xytext=(0,8),
                         ha="center", fontsize=10, color=TEAL, fontweight="bold")
    axes[2].set_title("Trend by Year", fontsize=11)
    axes[2].set_ylabel("30-d Readmit %")
    axes[2].set_xticks(by_year["service_year"])
    axes[2].fill_between(by_year["service_year"], by_year["readmit_pct"],
                         alpha=0.15, color=TEAL)

    plt.tight_layout()
    path = f"{out}/03_readmission_analysis.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 4 – Payer Mix & Cost Coverage
# ═══════════════════════════════════════════════════════════════════════════════
def chart_payer(conn, out):
    df = q(conn, """
        SELECT payer,
               COUNT(*) AS claims,
               ROUND(AVG(total_cost),2)   AS avg_billed,
               ROUND(AVG(paid_amount),2)  AS avg_paid,
               ROUND(AVG(patient_oop),2)  AS avg_oop,
               ROUND(100.0*AVG(paid_amount)/AVG(total_cost),1) AS coverage_pct
        FROM claims
        GROUP BY payer ORDER BY claims DESC
    """)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=BG)
    fig.suptitle("Payer Mix & Cost Coverage", fontsize=15, fontweight="bold", color=NAVY)

    # Pie – claim volume
    axes[0].pie(df["claims"], labels=df["payer"], autopct="%1.1f%%",
                colors=ACCENT_PALETTE[:len(df)], startangle=140,
                wedgeprops=dict(edgecolor="white", linewidth=1.5))
    axes[0].set_title("Claim Volume by Payer", fontsize=11)

    # Grouped bar – billed vs paid
    x = np.arange(len(df))
    w = 0.35
    axes[1].bar(x - w/2, df["avg_billed"], w, label="Avg Billed",
                color=TEAL, alpha=0.9)
    axes[1].bar(x + w/2, df["avg_paid"],   w, label="Avg Paid",
                color=CORAL, alpha=0.9)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(df["payer"], rotation=20, ha="right", fontsize=8)
    axes[1].set_ylabel("$")
    axes[1].set_title("Avg Billed vs Paid", fontsize=11)
    axes[1].legend(fontsize=8)

    # Coverage % horizontal bar
    cmap = LinearSegmentedColormap.from_list("cov", [CORAL, AMBER, MINT])
    norm = plt.Normalize(df["coverage_pct"].min(), df["coverage_pct"].max())
    colors = [cmap(norm(v)) for v in df["coverage_pct"]]
    h = axes[2].barh(df["payer"], df["coverage_pct"], color=colors)
    axes[2].bar_label(h, fmt="%.1f%%", padding=4, fontsize=9)
    axes[2].set_xlim(0, 100)
    axes[2].set_xlabel("Coverage %")
    axes[2].set_title("Payer Coverage Rate", fontsize=11)
    axes[2].axvline(75, color=NAVY, lw=1, ls="--", label="75% benchmark")
    axes[2].legend(fontsize=8)

    plt.tight_layout()
    path = f"{out}/04_payer_analysis.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 5 – Treatment Utilization Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
def chart_utilization_heatmap(conn, out):
    df = q(conn, """
        SELECT facility_type, region, COUNT(*) AS claims
        FROM claims
        GROUP BY facility_type, region
    """)
    pivot = df.pivot(index="facility_type", columns="region", values="claims").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 5), facecolor=BG)
    fig.suptitle("Utilization Heatmap: Facility × Region", fontsize=15,
                 fontweight="bold", color=NAVY)

    cmap = LinearSegmentedColormap.from_list("hc", [BG, SKY, TEAL, NAVY])
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.columns, fontsize=10)
    ax.set_yticklabels(pivot.index, fontsize=10)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = int(pivot.values[i, j])
            ax.text(j, i, f"{val:,}", ha="center", va="center",
                    fontsize=9, color="white" if val > pivot.values.max()*0.5 else SLATE,
                    fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Claim Count", color=SLATE)
    plt.tight_layout()
    path = f"{out}/05_utilization_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 6 – Cost Trend & YoY Change
# ═══════════════════════════════════════════════════════════════════════════════
def chart_cost_trend(conn, out):
    monthly = q(conn, """
        SELECT service_year, service_month,
               ROUND(AVG(total_cost),2) AS avg_cost,
               ROUND(SUM(total_cost),2) AS total_spend,
               COUNT(*) AS claims
        FROM claims
        GROUP BY service_year, service_month
        ORDER BY service_year, service_month
    """)
    monthly["period"] = (monthly["service_year"].astype(str) + "-"
                         + monthly["service_month"].astype(str).str.zfill(2))

    regional_yearly = q(conn, """
        SELECT region, service_year, ROUND(AVG(total_cost),2) AS avg_cost
        FROM claims
        GROUP BY region, service_year ORDER BY region, service_year
    """)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), facecolor=BG)
    fig.suptitle("Cost Trends & Year-over-Year Analysis", fontsize=15,
                 fontweight="bold", color=NAVY)

    # Monthly spend
    x = range(len(monthly))
    axes[0].fill_between(x, monthly["total_spend"]/1e6, alpha=0.2, color=TEAL)
    axes[0].plot(x, monthly["total_spend"]/1e6, color=TEAL, lw=2)
    # Year boundary lines
    for yr in [2023, 2024]:
        idx = monthly[monthly["service_year"]==yr].index[0] - monthly.index[0]
        axes[0].axvline(idx, color=NAVY, ls="--", lw=1, alpha=0.5)
        axes[0].text(idx+0.3, monthly["total_spend"].max()/1e6*0.95,
                     str(yr), color=NAVY, fontsize=9)
    axes[0].set_xticks(list(x)[::3])
    axes[0].set_xticklabels(monthly["period"].tolist()[::3], rotation=35, ha="right", fontsize=8)
    axes[0].set_ylabel("Total Spend ($M)")
    axes[0].set_title("Monthly Total Spend", fontsize=11)
    axes[0].grid(axis="y", linestyle="--")

    # Regional YoY lines
    for region, grp in regional_yearly.groupby("region"):
        color = REGION_COLORS[region]
        axes[1].plot(grp["service_year"], grp["avg_cost"],
                     marker="o", label=region, color=color, lw=2, markersize=6)
    axes[1].set_xticks([2022, 2023, 2024])
    axes[1].set_ylabel("Avg Cost per Claim ($)")
    axes[1].set_title("Avg Claim Cost by Region (YoY)", fontsize=11)
    axes[1].legend(fontsize=8, loc="upper left")
    axes[1].grid(True, linestyle="--")

    plt.tight_layout()
    path = f"{out}/06_cost_trend.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 7 – Denial Rate & Quality Metrics
# ═══════════════════════════════════════════════════════════════════════════════
def chart_quality(conn, out):
    denial = q(conn, """
        SELECT payer,
               ROUND(100.0*SUM(CASE WHEN claim_status='Denied' THEN 1 ELSE 0 END)/COUNT(*),2)
               AS denial_pct
        FROM claims GROUP BY payer ORDER BY denial_pct DESC
    """)

    qm = q(conn, "SELECT * FROM quality_metrics")

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), facecolor=BG)
    fig.suptitle("Claims Quality & Operational Metrics", fontsize=15,
                 fontweight="bold", color=NAVY)

    # Denial rate
    colors = [CORAL if v > 5 else AMBER if v > 3 else MINT for v in denial["denial_pct"]]
    h = axes[0].barh(denial["payer"], denial["denial_pct"], color=colors)
    axes[0].bar_label(h, fmt="%.1f%%", padding=4, fontsize=9)
    axes[0].set_xlabel("Denial Rate %")
    axes[0].set_title("Denial Rate by Payer", fontsize=11)
    axes[0].axvline(5, color=CORAL, lw=1.5, ls="--", label=">5% = Alert")
    axes[0].legend(fontsize=8)

    # Avg LOS by region/year
    pivot_los = qm.pivot(index="region", columns="year", values="avg_los_hospital").fillna(0)
    x = np.arange(len(pivot_los))
    w = 0.25
    for i, yr in enumerate(pivot_los.columns):
        axes[1].bar(x + i*w, pivot_los[yr], w, label=str(yr),
                    color=ACCENT_PALETTE[i], alpha=0.85)
    axes[1].set_xticks(x + w)
    axes[1].set_xticklabels(pivot_los.index, rotation=20, ha="right", fontsize=8)
    axes[1].set_ylabel("Avg LOS (days)")
    axes[1].set_title("Avg Length of Stay (Hospital)", fontsize=11)
    axes[1].legend(title="Year", fontsize=8)

    # ER visit rate
    pivot_er = qm.pivot(index="region", columns="year", values="er_visit_rate_pct").fillna(0)
    for i, yr in enumerate(pivot_er.columns):
        axes[2].plot(pivot_er.index, pivot_er[yr], marker="o",
                     label=str(yr), color=ACCENT_PALETTE[i], lw=2)
    axes[2].set_ylabel("ER Visit Rate %")
    axes[2].set_title("ER Visit Rate by Region", fontsize=11)
    axes[2].legend(title="Year", fontsize=8)
    axes[2].tick_params(axis="x", rotation=15)
    axes[2].grid(True, linestyle="--")

    plt.tight_layout()
    path = f"{out}/07_quality_metrics.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 8 – Patient Demographics & Cost Stratification
# ═══════════════════════════════════════════════════════════════════════════════
def chart_demographics(conn, out):
    age_cost = q(conn, """
        SELECT p.age, c.total_cost, p.chronic_conditions, p.gender
        FROM claims c JOIN patients p ON c.patient_id = p.patient_id
    """)

    age_bins = [18,30,40,50,60,70,80,95]
    labels   = ["18-29","30-39","40-49","50-59","60-69","70-79","80+"]
    age_cost["age_group"] = pd.cut(age_cost["age"], bins=age_bins, labels=labels, right=False)

    by_age = age_cost.groupby("age_group", observed=True)["total_cost"].mean().reset_index()

    chronic_cost = age_cost.groupby("chronic_conditions")["total_cost"].mean().reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), facecolor=BG)
    fig.suptitle("Patient Demographics & Cost Stratification", fontsize=15,
                 fontweight="bold", color=NAVY)

    # Avg cost by age group
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(by_age)))
    b = axes[0].bar(by_age["age_group"].astype(str), by_age["total_cost"],
                    color=colors, edgecolor="white")
    axes[0].bar_label(b, fmt="$%.0f", padding=3, fontsize=8)
    axes[0].set_xlabel("Age Group")
    axes[0].set_ylabel("Avg Claim Cost ($)")
    axes[0].set_title("Avg Cost by Age Group", fontsize=11)
    axes[0].tick_params(axis="x", rotation=20)

    # Cost by chronic conditions
    axes[1].plot(chronic_cost["chronic_conditions"], chronic_cost["total_cost"],
                 marker="s", color=CORAL, lw=2.5, markersize=9, zorder=3)
    axes[1].fill_between(chronic_cost["chronic_conditions"],
                         chronic_cost["total_cost"], alpha=0.15, color=CORAL)
    axes[1].set_xlabel("Number of Chronic Conditions")
    axes[1].set_ylabel("Avg Claim Cost ($)")
    axes[1].set_title("Cost by Chronic Condition Count", fontsize=11)
    axes[1].set_xticks(chronic_cost["chronic_conditions"])
    axes[1].grid(True, linestyle="--")

    # Gender distribution
    gender_df = q(conn, """
        SELECT p.gender, COUNT(*) AS patients
        FROM patients p GROUP BY p.gender
    """)
    axes[2].pie(gender_df["patients"], labels=gender_df["gender"],
                autopct="%1.1f%%", colors=[TEAL, CORAL, AMBER],
                wedgeprops=dict(edgecolor="white", linewidth=2), startangle=90)
    axes[2].set_title("Patient Gender Distribution", fontsize=11)

    plt.tight_layout()
    path = f"{out}/08_demographics.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT – Tableau/Power BI ready Excel workbook
# ═══════════════════════════════════════════════════════════════════════════════
def export_excel(conn, out):
    print("  Exporting Excel workbook …")
    path = f"{out}/healthcare_claims_analytics.xlsx"
    sheets = {
        "Claims_Summary": q(conn, """
            SELECT service_year, service_quarter, region, payer, facility_type,
                   diagnosis_desc, COUNT(*) AS claims,
                   ROUND(AVG(total_cost),2) AS avg_cost,
                   ROUND(SUM(total_cost),2) AS total_spend,
                   ROUND(SUM(paid_amount),2) AS total_paid,
                   SUM(readmission_30d) AS readmissions,
                   ROUND(100.0*SUM(readmission_30d)/COUNT(*),2) AS readmit_pct
            FROM claims GROUP BY 1,2,3,4,5,6
        """),
        "Regional_Cost": q(conn, """
            SELECT region, service_year,
                   COUNT(*) AS claims,
                   ROUND(AVG(total_cost),2) AS avg_cost,
                   ROUND(SUM(total_cost),2) AS total_spend
            FROM claims GROUP BY region, service_year
        """),
        "Payer_Analysis": q(conn, """
            SELECT payer, service_year,
                   COUNT(*) AS claims,
                   ROUND(AVG(total_cost),2) AS avg_billed,
                   ROUND(AVG(paid_amount),2) AS avg_paid,
                   ROUND(100.0*SUM(CASE WHEN claim_status='Denied' THEN 1 ELSE 0 END)/COUNT(*),2)
                   AS denial_rate_pct
            FROM claims GROUP BY payer, service_year
        """),
        "Readmissions": q(conn, """
            SELECT region, service_year, diagnosis_desc, facility_type,
                   COUNT(*) AS admits,
                   SUM(readmission_30d) AS readmissions,
                   ROUND(100.0*SUM(readmission_30d)/COUNT(*),2) AS readmit_pct,
                   ROUND(AVG(total_cost),2) AS avg_cost
            FROM claims WHERE facility_type='Hospital'
            GROUP BY region, service_year, diagnosis_desc, facility_type
        """),
        "Quality_Metrics": q(conn, "SELECT * FROM quality_metrics"),
        "Patient_Level": q(conn, """
            SELECT p.patient_id, p.age, p.gender, p.region, p.payer,
                   p.chronic_conditions,
                   COUNT(c.claim_id) AS total_claims,
                   ROUND(SUM(c.total_cost),2) AS total_cost,
                   SUM(c.readmission_30d) AS readmissions
            FROM patients p LEFT JOIN claims c ON p.patient_id=c.patient_id
            GROUP BY p.patient_id, p.age, p.gender, p.region, p.payer, p.chronic_conditions
        """),
    }
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    print(f"  ✓ {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("Loading data into SQLite …")
    conn = load_db()
    print(f"Generating charts → {OUT}/\n")

    chart_kpi_summary(conn, OUT)
    chart_regional_cost(conn, OUT)
    chart_readmission(conn, OUT)
    chart_payer(conn, OUT)
    chart_utilization_heatmap(conn, OUT)
    chart_cost_trend(conn, OUT)
    chart_quality(conn, OUT)
    chart_demographics(conn, OUT)
    export_excel(conn, OUT)

    conn.close()
    print("\n✅  All charts and exports complete.")


if __name__ == "__main__":
    main()
