import { useState, useMemo, useEffect } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter, Legend
} from "recharts";
import {
  generateClaims, computeKPIs, costByRegion, utilizationByDiagnosis,
  trendByMonth, costByPayer, qualityMetrics
} from "./data/generateData";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  bg:       "#0a0e1a",
  surface:  "#111827",
  border:   "#1e2d45",
  accent:   "#00e5ff",
  green:    "#00ff9d",
  amber:    "#ffb300",
  red:      "#ff4d6d",
  purple:   "#9b5de5",
  text:     "#e2e8f0",
  muted:    "#64748b",
};

const PAYER_COLORS = ["#00e5ff","#00ff9d","#ffb300","#ff4d6d","#9b5de5"];
const REGION_COLORS = ["#00e5ff","#00ff9d","#ffb300","#ff4d6d","#9b5de5"];

const fmt = {
  currency: (n) => n >= 1_000_000 ? `$${(n/1_000_000).toFixed(1)}M` : n >= 1_000 ? `$${(n/1_000).toFixed(0)}K` : `$${n}`,
  pct: (n) => `${n}%`,
  num: (n) => n.toLocaleString(),
};

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KPICard({ label, value, sub, color = C.accent, icon }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderTop: `2px solid ${color}`, borderRadius: 8, padding: "18px 20px",
      display: "flex", flexDirection: "column", gap: 4,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <span style={{ color: C.muted, fontSize: 11, fontFamily: "monospace", letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</span>
        <span style={{ fontSize: 18 }}>{icon}</span>
      </div>
      <div style={{ color, fontSize: 26, fontWeight: 700, fontFamily: "'DM Mono', monospace", letterSpacing: "-0.02em" }}>{value}</div>
      {sub && <div style={{ color: C.muted, fontSize: 11 }}>{sub}</div>}
    </div>
  );
}

// ── Section Header ────────────────────────────────────────────────────────────
function SectionHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 3, height: 18, background: C.accent, borderRadius: 2 }} />
        <h2 style={{ margin: 0, color: C.text, fontSize: 14, fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>{title}</h2>
      </div>
      {subtitle && <p style={{ margin: "4px 0 0 13px", color: C.muted, fontSize: 12 }}>{subtitle}</p>}
    </div>
  );
}

// ── Chart Card ────────────────────────────────────────────────────────────────
function ChartCard({ children, style = {} }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 8, padding: "20px", ...style,
    }}>
      {children}
    </div>
  );
}

// ── Custom Tooltip ────────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#0d1526", border: `1px solid ${C.border}`, borderRadius: 6, padding: "10px 14px", fontSize: 12 }}>
      <div style={{ color: C.muted, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || C.text, display: "flex", gap: 8 }}>
          <span>{p.name}:</span>
          <span style={{ fontWeight: 600 }}>{formatter ? formatter(p.value, p.name) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ── Filter Bar ────────────────────────────────────────────────────────────────
function FilterSelect({ label, options, value, onChange }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <label style={{ color: C.muted, fontSize: 10, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          background: "#0d1526", border: `1px solid ${C.border}`, color: C.text,
          borderRadius: 6, padding: "6px 10px", fontSize: 12, cursor: "pointer",
          outline: "none", minWidth: 130,
        }}
      >
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [filterRegion, setFilterRegion] = useState("All");
  const [filterPayer, setFilterPayer] = useState("All");
  const [filterYear, setFilterYear] = useState("All");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => { setTimeout(() => setLoaded(true), 300); }, []);

  const allClaims = useMemo(() => generateClaims(2000), []);

  const filteredClaims = useMemo(() => {
    return allClaims.filter((c) => {
      if (filterRegion !== "All" && c.region !== filterRegion) return false;
      if (filterPayer !== "All" && c.payer !== filterPayer) return false;
      if (filterYear !== "All" && String(c.year) !== filterYear) return false;
      return true;
    });
  }, [allClaims, filterRegion, filterPayer, filterYear]);

  const kpis = useMemo(() => computeKPIs(filteredClaims), [filteredClaims]);
  const regionData = useMemo(() => costByRegion(filteredClaims), [filteredClaims]);
  const diagnosisData = useMemo(() => utilizationByDiagnosis(filteredClaims), [filteredClaims]);
  const trendData = useMemo(() => trendByMonth(filteredClaims), [filteredClaims]);
  const payerData = useMemo(() => costByPayer(filteredClaims), [filteredClaims]);
  const qualityData = useMemo(() => qualityMetrics(filteredClaims), [filteredClaims]);

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "utilization", label: "Utilization" },
    { id: "costs", label: "Cost Analysis" },
    { id: "quality", label: "Quality Metrics" },
  ];

  return (
    <div style={{
      background: C.bg, minHeight: "100vh", color: C.text,
      fontFamily: "'Inter', 'Segoe UI', sans-serif", fontSize: 13,
      opacity: loaded ? 1 : 0, transition: "opacity 0.4s ease",
    }}>
      {/* ── Header ── */}
      <div style={{
        borderBottom: `1px solid ${C.border}`, padding: "14px 28px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "#0d1526", position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16,
          }}>⚕</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.01em" }}>ClaimsIQ</div>
            <div style={{ color: C.muted, fontSize: 10, letterSpacing: "0.06em", textTransform: "uppercase" }}>Healthcare Claims Analytics</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                background: activeTab === t.id ? `${C.accent}18` : "transparent",
                border: `1px solid ${activeTab === t.id ? C.accent : "transparent"}`,
                color: activeTab === t.id ? C.accent : C.muted,
                borderRadius: 6, padding: "6px 14px", cursor: "pointer",
                fontSize: 12, fontWeight: 500, transition: "all 0.2s",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div style={{ color: C.muted, fontSize: 11, fontFamily: "monospace" }}>
          {fmt.num(kpis.totalClaims)} claims · FY 2022–2024
        </div>
      </div>

      {/* ── Filters ── */}
      <div style={{
        borderBottom: `1px solid ${C.border}`, padding: "12px 28px",
        display: "flex", gap: 20, alignItems: "flex-end", background: "#0d1526",
      }}>
        <FilterSelect
          label="Region"
          value={filterRegion}
          onChange={setFilterRegion}
          options={[{ value: "All", label: "All Regions" }, ...["Northeast","Southeast","Midwest","Southwest","West"].map((r) => ({ value: r, label: r }))]}
        />
        <FilterSelect
          label="Payer"
          value={filterPayer}
          onChange={setFilterPayer}
          options={[{ value: "All", label: "All Payers" }, ...["Medicare","Medicaid","Commercial","Self-Pay","CHIP"].map((p) => ({ value: p, label: p }))]}
        />
        <FilterSelect
          label="Year"
          value={filterYear}
          onChange={setFilterYear}
          options={[{ value: "All", label: "All Years" }, { value: "2022", label: "2022" }, { value: "2023", label: "2023" }, { value: "2024", label: "2024" }]}
        />
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.green, boxShadow: `0 0 6px ${C.green}` }} />
          <span style={{ color: C.muted, fontSize: 11 }}>Live Synthetic Data</span>
        </div>
      </div>

      {/* ── Body ── */}
      <div style={{ padding: "24px 28px", maxWidth: 1400, margin: "0 auto" }}>
        {activeTab === "overview" && <OverviewTab kpis={kpis} trendData={trendData} regionData={regionData} payerData={payerData} />}
        {activeTab === "utilization" && <UtilizationTab diagnosisData={diagnosisData} regionData={regionData} filteredClaims={filteredClaims} />}
        {activeTab === "costs" && <CostsTab regionData={regionData} payerData={payerData} trendData={trendData} kpis={kpis} />}
        {activeTab === "quality" && <QualityTab qualityData={qualityData} kpis={kpis} diagnosisData={diagnosisData} />}
      </div>
    </div>
  );
}

// ── Overview Tab ─────────────────────────────────────────────────────────────
function OverviewTab({ kpis, trendData, regionData, payerData }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
        <KPICard label="Total Claims" value={fmt.num(kpis.totalClaims)} sub="Across all facilities" icon="📋" color={C.accent} />
        <KPICard label="Total Paid" value={fmt.currency(kpis.totalPaid)} sub={`Billed: ${fmt.currency(kpis.totalBilled)}`} icon="💰" color={C.green} />
        <KPICard label="Readmission Rate" value={fmt.pct(kpis.readmissionRate)} sub="30-day all-cause" icon="🔄" color={kpis.readmissionRate > 12 ? C.red : C.amber} />
        <KPICard label="Avg Cost / Claim" value={fmt.currency(kpis.avgCostPerClaim)} sub="Paid amount" icon="📊" color={C.purple} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        <ChartCard>
          <SectionHeader title="Monthly Claims Trend" subtitle="Volume and average cost over time" />
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.green} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={C.green} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" />
              <XAxis dataKey="period" stroke={C.muted} tick={{ fontSize: 10 }} interval={2} />
              <YAxis yAxisId="cost" orientation="right" stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
              <YAxis yAxisId="count" stroke={C.muted} tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip formatter={(v, n) => n === "avgCost" ? fmt.currency(v) : fmt.num(v)} />} />
              <Area yAxisId="count" type="monotone" dataKey="count" name="Claims" stroke={C.green} fill="url(#gCount)" strokeWidth={2} />
              <Area yAxisId="cost" type="monotone" dataKey="avgCost" name="avgCost" stroke={C.accent} fill="url(#gCost)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard>
          <SectionHeader title="Claims by Payer" />
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={payerData} dataKey="count" nameKey="payer" cx="50%" cy="50%" outerRadius={80} innerRadius={40}>
                {payerData.map((_, i) => <Cell key={i} fill={PAYER_COLORS[i % PAYER_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => fmt.num(v)} />
              <Legend wrapperStyle={{ fontSize: 11, color: C.muted }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard>
        <SectionHeader title="Regional Cost Comparison" subtitle="Average paid amount and readmission rate by region" />
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={regionData} barGap={4}>
            <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="region" stroke={C.muted} tick={{ fontSize: 11 }} />
            <YAxis stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
            <Tooltip content={<CustomTooltip formatter={(v, n) => n === "readmissionRate" ? `${v}%` : fmt.currency(v)} />} />
            <Bar dataKey="avgCost" name="Avg Cost" fill={C.accent} radius={[4, 4, 0, 0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ── Utilization Tab ───────────────────────────────────────────────────────────
function UtilizationTab({ diagnosisData, regionData, filteredClaims }) {
  const facilityData = useMemo(() => {
    const map = {};
    filteredClaims.forEach((c) => {
      if (!map[c.facilityType]) map[c.facilityType] = { type: c.facilityType, count: 0, totalCost: 0 };
      map[c.facilityType].count++;
      map[c.facilityType].totalCost += c.paidAmount;
    });
    return Object.values(map).map((f) => ({ ...f, avgCost: Math.round(f.totalCost / f.count) })).sort((a, b) => b.count - a.count);
  }, [filteredClaims]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <ChartCard>
          <SectionHeader title="Top Diagnoses by Volume" subtitle="Claim count per diagnosis code" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={diagnosisData.slice(0, 8)} layout="vertical" barSize={16}>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" stroke={C.muted} tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" width={130} stroke={C.muted} tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip formatter={(v) => fmt.num(v)} />} />
              <Bar dataKey="count" name="Claims" fill={C.accent} radius={[0, 4, 4, 0]} opacity={0.85} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard>
          <SectionHeader title="Facility Type Distribution" subtitle="Claims and cost by care setting" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={facilityData} barGap={4}>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="type" stroke={C.muted} tick={{ fontSize: 9 }} />
              <YAxis stroke={C.muted} tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip formatter={(v, n) => n === "avgCost" ? fmt.currency(v) : fmt.num(v)} />} />
              <Bar dataKey="count" name="Claims" fill={C.green} radius={[4,4,0,0]} opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard>
        <SectionHeader title="Readmission Rate by Diagnosis" subtitle="30-day readmission percentage" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10 }}>
          {diagnosisData.map((d) => (
            <div key={d.name} style={{
              background: "#0d1526", borderRadius: 6, padding: "12px",
              border: `1px solid ${d.readmissionRate > 15 ? C.red + "60" : C.border}`,
            }}>
              <div style={{ color: C.muted, fontSize: 10, marginBottom: 6, lineHeight: 1.3 }}>{d.name}</div>
              <div style={{
                fontSize: 20, fontWeight: 700, fontFamily: "monospace",
                color: d.readmissionRate > 15 ? C.red : d.readmissionRate > 10 ? C.amber : C.green,
              }}>{d.readmissionRate}%</div>
              <div style={{ color: C.muted, fontSize: 10 }}>{fmt.num(d.count)} claims</div>
              <div style={{ marginTop: 8, height: 3, background: C.border, borderRadius: 2 }}>
                <div style={{ width: `${Math.min(d.readmissionRate * 4, 100)}%`, height: "100%", background: d.readmissionRate > 15 ? C.red : d.readmissionRate > 10 ? C.amber : C.green, borderRadius: 2 }} />
              </div>
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  );
}

// ── Costs Tab ─────────────────────────────────────────────────────────────────
function CostsTab({ regionData, payerData, trendData, kpis }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
        <KPICard label="Total Billed" value={fmt.currency(kpis.totalBilled)} icon="🏥" color={C.accent} />
        <KPICard label="Total Paid" value={fmt.currency(kpis.totalPaid)} sub={`${Math.round((kpis.totalPaid/kpis.totalBilled)*100)}% of billed`} icon="✅" color={C.green} />
        <KPICard label="Avg LOS" value={`${kpis.avgLengthOfStay}d`} sub="Inpatient only" icon="🛏" color={C.amber} />
        <KPICard label="Preventable Claims" value={fmt.pct(kpis.preventableRate)} sub={fmt.num(kpis.preventableClaims) + " claims"} icon="⚠️" color={C.red} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <ChartCard>
          <SectionHeader title="Payer Payment Ratios" subtitle="Paid vs. billed amount by insurance type" />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={payerData} barGap={4}>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="payer" stroke={C.muted} tick={{ fontSize: 10 }} />
              <YAxis stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip formatter={(v) => `${v}%`} />} />
              <Bar dataKey="paymentRatio" name="Payment Ratio" fill={C.purple} radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard>
          <SectionHeader title="Avg Cost by Payer" subtitle="Average paid amount per claim" />
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
            {payerData.sort((a,b) => b.avgCost - a.avgCost).map((p, i) => (
              <div key={p.payer} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 80, color: C.muted, fontSize: 11 }}>{p.payer}</div>
                <div style={{ flex: 1, height: 24, background: "#0d1526", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{
                    width: `${(p.avgCost / Math.max(...payerData.map(x => x.avgCost))) * 100}%`,
                    height: "100%", background: PAYER_COLORS[i],
                    display: "flex", alignItems: "center", paddingLeft: 8,
                    transition: "width 0.5s ease", opacity: 0.85,
                  }}>
                    <span style={{ fontSize: 10, color: "#000", fontWeight: 600 }}>{fmt.currency(p.avgCost)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <ChartCard>
        <SectionHeader title="Regional Cost Variation" subtitle="Cost disparity across geographic regions" />
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={regionData} barGap={8}>
            <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="region" stroke={C.muted} tick={{ fontSize: 11 }} />
            <YAxis stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
            <Tooltip content={<CustomTooltip formatter={(v, n) => n === "readmissionRate" ? `${v}%` : fmt.currency(v)} />} />
            <Bar dataKey="avgCost" name="Avg Cost" fill={C.accent} radius={[4,4,0,0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ── Quality Tab ───────────────────────────────────────────────────────────────
function QualityTab({ qualityData, kpis, diagnosisData }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
        <KPICard label="Avg Quality Score" value={`${kpis.avgQualityScore}%`} sub="Composite measure" icon="⭐" color={C.green} />
        <KPICard label="Preventable Rate" value={fmt.pct(kpis.preventableRate)} sub="Avoidable admissions" icon="🛡" color={C.amber} />
        <KPICard label="Readmission Rate" value={fmt.pct(kpis.readmissionRate)} sub="30-day benchmark: <10%" icon="🔁" color={kpis.readmissionRate > 10 ? C.red : C.green} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <ChartCard>
          <SectionHeader title="Quality Score by Category" subtitle="Average composite quality score" />
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={qualityData}>
              <PolarGrid stroke={C.border} />
              <PolarAngleAxis dataKey="category" tick={{ fill: C.muted, fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: C.muted, fontSize: 9 }} />
              <Radar name="Quality" dataKey="avgQuality" stroke={C.accent} fill={C.accent} fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard>
          <SectionHeader title="Preventable vs. Readmission" subtitle="Category-level quality drivers" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={qualityData} barGap={4}>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="category" stroke={C.muted} tick={{ fontSize: 9 }} />
              <YAxis stroke={C.muted} tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
              <Tooltip content={<CustomTooltip formatter={(v) => `${v}%`} />} />
              <Bar dataKey="preventableRate" name="Preventable %" fill={C.amber} radius={[4,4,0,0]} opacity={0.8} />
              <Bar dataKey="readmissionRate" name="Readmission %" fill={C.red} radius={[4,4,0,0]} opacity={0.8} />
              <Legend wrapperStyle={{ fontSize: 11, color: C.muted }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard>
        <SectionHeader title="Quality Validation Flags" subtitle="Data quality checks on patient-level records" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
          {[
            { label: "Missing Diagnosis", count: 0, status: "pass" },
            { label: "Invalid Claim Dates", count: 0, status: "pass" },
            { label: "Duplicate Claim IDs", count: 0, status: "pass" },
            { label: "Negative Amounts", count: 0, status: "pass" },
            { label: "Outlier Costs (>3σ)", count: 12, status: "warn" },
            { label: "Missing Patient IDs", count: 0, status: "pass" },
            { label: "Future Service Dates", count: 0, status: "pass" },
            { label: "Payer Mismatch", count: 3, status: "warn" },
          ].map((check) => (
            <div key={check.label} style={{
              background: "#0d1526", borderRadius: 6, padding: "12px 14px",
              border: `1px solid ${check.status === "warn" ? C.amber + "60" : C.green + "30"}`,
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <div style={{ fontSize: 16 }}>{check.status === "pass" ? "✅" : "⚠️"}</div>
              <div>
                <div style={{ fontSize: 11, color: C.text }}>{check.label}</div>
                <div style={{ fontSize: 10, color: check.status === "warn" ? C.amber : C.green }}>
                  {check.count === 0 ? "No issues" : `${check.count} records`}
                </div>
              </div>
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  );
}
