// Synthetic Healthcare Claims Data Generator
// All data is entirely fictional for demonstration purposes

const REGIONS = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'];

const DIAGNOSES = [
  { code: 'I21', name: 'Acute MI', category: 'Cardiovascular' },
  { code: 'J18', name: 'Pneumonia', category: 'Respiratory' },
  { code: 'E11', name: 'Type 2 Diabetes', category: 'Endocrine' },
  { code: 'M54', name: 'Back Pain', category: 'Musculoskeletal' },
  { code: 'F32', name: 'Depression', category: 'Mental Health' },
  { code: 'N18', name: 'Chronic Kidney Disease', category: 'Renal' },
  { code: 'I10', name: 'Hypertension', category: 'Cardiovascular' },
  { code: 'J44', name: 'COPD', category: 'Respiratory' },
  { code: 'K92', name: 'GI Hemorrhage', category: 'Gastrointestinal' },
  { code: 'A41', name: 'Sepsis', category: 'Infectious Disease' },
];

const PROCEDURES = [
  { code: '99213', name: 'Office Visit', baseCost: 180 },
  { code: '99223', name: 'Inpatient Admission', baseCost: 3200 },
  { code: '93000', name: 'ECG', baseCost: 220 },
  { code: '71046', name: 'Chest X-Ray', baseCost: 340 },
  { code: '80053', name: 'Metabolic Panel', baseCost: 110 },
  { code: '43239', name: 'GI Endoscopy', baseCost: 1800 },
  { code: '27447', name: 'Knee Replacement', baseCost: 28000 },
  { code: '33533', name: 'CABG', baseCost: 65000 },
  { code: '70553', name: 'MRI Brain', baseCost: 2400 },
  { code: '99291', name: 'Critical Care', baseCost: 900 },
];

const PAYERS = ['Medicare', 'Medicaid', 'Commercial', 'Self-Pay', 'CHIP'];
const FACILITY_TYPES = ['Hospital', 'Outpatient Clinic', 'Urgent Care', 'Specialty Center', 'Rehab Facility'];

function seededRand(seed) {
  let s = seed;
  return function () {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 4294967295;
  };
}

export function generateClaims(count = 2000) {
  const rand = seededRand(42);
  const claims = [];

  for (let i = 0; i < count; i++) {
    const r = () => rand();
    const region = REGIONS[Math.floor(r() * REGIONS.length)];
    const diagnosis = DIAGNOSES[Math.floor(r() * DIAGNOSES.length)];
    const procedure = PROCEDURES[Math.floor(r() * PROCEDURES.length)];
    const payer = PAYERS[Math.floor(r() * PAYERS.length)];
    const facilityType = FACILITY_TYPES[Math.floor(r() * FACILITY_TYPES.length)];

    const year = 2022 + Math.floor(r() * 3);
    const month = Math.floor(r() * 12);
    const day = Math.floor(r() * 28) + 1;
    const serviceDate = new Date(year, month, day);

    const age = Math.floor(r() * 65) + 18;
    const gender = r() > 0.48 ? 'Female' : 'Male';

    const costMultiplier =
      0.6 + r() * 0.9 + (region === 'Northeast' || region === 'West' ? 0.3 : 0);
    const billedAmount = Math.round(procedure.baseCost * costMultiplier * 100) / 100;
    const allowedAmount = Math.round(billedAmount * (0.55 + r() * 0.3) * 100) / 100;
    const paidAmount = Math.round(
      allowedAmount * (payer === 'Self-Pay' ? 0.3 + r() * 0.2 : 0.8 + r() * 0.15) * 100
    ) / 100;
    const patientResponsibility = Math.round((allowedAmount - paidAmount) * 100) / 100;

    const losBase =
      diagnosis.category === 'Cardiovascular' ? 5
      : diagnosis.category === 'Respiratory' ? 4
      : 2;
    const lengthOfStay =
      facilityType === 'Hospital' ? Math.floor(r() * losBase * 2) + 1 : 0;

    const readmitProb =
      (diagnosis.category === 'Cardiovascular' ? 0.18 : 0.08) +
      (age > 65 ? 0.08 : 0) +
      (payer === 'Medicaid' ? 0.05 : 0);
    const readmitted = r() < readmitProb;
    const qualityScore = Math.round((0.5 + r() * 0.5) * 100) / 100;
    const preventable = r() < 0.12;

    claims.push({
      claimId: `CLM${String(i + 1).padStart(6, '0')}`,
      patientId: `PT${String(Math.floor(r() * 800) + 1).padStart(5, '0')}`,
      serviceDate: serviceDate.toISOString().split('T')[0],
      year,
      month: month + 1,
      region,
      facilityType,
      diagnosis,
      procedure,
      payer,
      age,
      ageGroup:
        age < 35 ? '18-34'
        : age < 50 ? '35-49'
        : age < 65 ? '50-64'
        : '65+',
      gender,
      billedAmount,
      allowedAmount,
      paidAmount,
      patientResponsibility,
      lengthOfStay,
      readmitted,
      qualityScore,
      preventable,
    });
  }
  return claims;
}

export function computeKPIs(claims) {
  const total = claims.length;
  const totalBilled = claims.reduce((s, c) => s + c.billedAmount, 0);
  const totalPaid = claims.reduce((s, c) => s + c.paidAmount, 0);
  const readmissions = claims.filter((c) => c.readmitted).length;
  const hospitalClaims = claims.filter((c) => c.lengthOfStay > 0);
  const avgLOS =
    hospitalClaims.length > 0
      ? hospitalClaims.reduce((s, c) => s + c.lengthOfStay, 0) / hospitalClaims.length
      : 0;
  const preventable = claims.filter((c) => c.preventable).length;
  const avgQuality = claims.reduce((s, c) => s + c.qualityScore, 0) / total;
  return {
    totalClaims: total,
    totalBilled: Math.round(totalBilled),
    totalPaid: Math.round(totalPaid),
    avgCostPerClaim: Math.round(totalPaid / total),
    readmissionRate: Math.round((readmissions / total) * 1000) / 10,
    avgLengthOfStay: Math.round(avgLOS * 10) / 10,
    preventableClaims: preventable,
    preventableRate: Math.round((preventable / total) * 1000) / 10,
    avgQualityScore: Math.round(avgQuality * 1000) / 10,
  };
}

export function costByRegion(claims) {
  const map = {};
  claims.forEach((c) => {
    if (!map[c.region])
      map[c.region] = { region: c.region, totalPaid: 0, count: 0, readmissions: 0 };
    map[c.region].totalPaid += c.paidAmount;
    map[c.region].count++;
    if (c.readmitted) map[c.region].readmissions++;
  });
  return Object.values(map).map((r) => ({
    ...r,
    avgCost: Math.round(r.totalPaid / r.count),
    readmissionRate: Math.round((r.readmissions / r.count) * 1000) / 10,
  }));
}

export function utilizationByDiagnosis(claims) {
  const map = {};
  claims.forEach((c) => {
    const key = c.diagnosis.name;
    if (!map[key])
      map[key] = { name: key, category: c.diagnosis.category, count: 0, totalCost: 0, readmissions: 0 };
    map[key].count++;
    map[key].totalCost += c.paidAmount;
    if (c.readmitted) map[key].readmissions++;
  });
  return Object.values(map)
    .map((d) => ({
      ...d,
      avgCost: Math.round(d.totalCost / d.count),
      readmissionRate: Math.round((d.readmissions / d.count) * 1000) / 10,
    }))
    .sort((a, b) => b.count - a.count);
}

export function trendByMonth(claims) {
  const map = {};
  claims.forEach((c) => {
    const key = `${c.year}-${String(c.month).padStart(2, '0')}`;
    if (!map[key])
      map[key] = { period: key, year: c.year, month: c.month, count: 0, totalCost: 0, readmissions: 0 };
    map[key].count++;
    map[key].totalCost += c.paidAmount;
    if (c.readmitted) map[key].readmissions++;
  });
  return Object.values(map)
    .sort((a, b) => a.period.localeCompare(b.period))
    .map((m) => ({
      ...m,
      avgCost: Math.round(m.totalCost / m.count),
      readmissionRate: Math.round((m.readmissions / m.count) * 1000) / 10,
    }));
}

export function costByPayer(claims) {
  const map = {};
  claims.forEach((c) => {
    if (!map[c.payer])
      map[c.payer] = { payer: c.payer, count: 0, totalPaid: 0, totalBilled: 0 };
    map[c.payer].count++;
    map[c.payer].totalPaid += c.paidAmount;
    map[c.payer].totalBilled += c.billedAmount;
  });
  return Object.values(map).map((p) => ({
    ...p,
    avgCost: Math.round(p.totalPaid / p.count),
    paymentRatio: Math.round((p.totalPaid / p.totalBilled) * 1000) / 10,
  }));
}

export function qualityMetrics(claims) {
  const map = {};
  claims.forEach((c) => {
    const cat = c.diagnosis.category;
    if (!map[cat])
      map[cat] = { category: cat, count: 0, totalQuality: 0, preventable: 0, readmissions: 0 };
    map[cat].count++;
    map[cat].totalQuality += c.qualityScore;
    if (c.preventable) map[cat].preventable++;
    if (c.readmitted) map[cat].readmissions++;
  });
  return Object.values(map).map((c) => ({
    ...c,
    avgQuality: Math.round((c.totalQuality / c.count) * 1000) / 10,
    preventableRate: Math.round((c.preventable / c.count) * 1000) / 10,
    readmissionRate: Math.round((c.readmissions / c.count) * 1000) / 10,
  }));
}
