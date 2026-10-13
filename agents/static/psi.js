/* Two-step adult PSI/PORT (Fine et al., NEJM 1997;336:243-250).
 * Plain JavaScript for GitHub Pages. Does not send or persist data.
 */
(function (root) {
  "use strict";
  const FACTORS = Object.freeze([
    ["nursing_home_resident", "Nursing-home resident", 10, "demographic"],
    ["neoplastic_disease", "Neoplastic disease", 30, "comorbidity"],
    ["liver_disease", "Liver disease", 20, "comorbidity"],
    ["congestive_heart_failure", "Congestive heart failure", 10, "comorbidity"],
    ["cerebrovascular_disease", "Cerebrovascular disease", 10, "comorbidity"],
    ["renal_disease", "Renal disease", 10, "comorbidity"],
    ["altered_mental_status", "Altered mental status", 20, "examination"],
    ["respiratory_rate_ge_30", "Respiratory rate ≥30/min", 20, "examination"],
    ["systolic_bp_lt_90", "Systolic BP <90 mmHg", 20, "examination"],
    ["temperature_extreme", "Temperature <35°C or ≥40°C", 15, "examination"],
    ["pulse_ge_125", "Pulse ≥125/min", 10, "examination"],
    ["arterial_ph_lt_7_35", "Arterial pH <7.35", 30, "investigation"],
    ["bun_ge_30", "BUN ≥30 mg/dL", 20, "investigation"],
    ["sodium_lt_130", "Sodium <130 mmol/L", 20, "investigation"],
    ["glucose_ge_250", "Glucose ≥250 mg/dL", 10, "investigation"],
    ["hematocrit_lt_30", "Hematocrit <30%", 10, "investigation"],
    ["hypoxemia", "PaO₂ <60 mmHg or O₂ saturation <90%", 10, "investigation"],
    ["pleural_effusion", "Pleural effusion", 10, "investigation"]
  ]);
  const DISPOSITION = Object.freeze({
    I: ["Very low", "Outpatient care may be appropriate after clinical assessment"],
    II: ["Low", "Outpatient care may be appropriate after clinical assessment"],
    III: ["Intermediate", "Consider observation or short hospitalization"],
    IV: ["High", "Hospital assessment/admission generally indicated"],
    V: ["Very high", "Hospital assessment/admission generally indicated"]
  });
  function scorePSI(input) {
    if (!input || typeof input !== "object" || Array.isArray(input)) throw new TypeError("Input must be an object");
    if (!Number.isInteger(input.age) || input.age < 18 || input.age > 120) {
      throw new RangeError("Age must be an integer from 18 to 120 (adult CAP only)");
    }
    if (input.sex !== "male" && input.sex !== "female") {
      throw new TypeError("Select male or female for the original PSI formula");
    }
    const allowed = new Set(["age", "sex", ...FACTORS.map(f => f[0])]);
    for (const key of Object.keys(input)) if (!allowed.has(key)) throw new TypeError("Unknown PSI input: " + key);
    for (const [key] of FACTORS) if (typeof input[key] !== "boolean") {
      throw new TypeError("Finding " + key + " must be explicitly assessed true or false");
    }
    let score = input.age - (input.sex === "female" ? 10 : 0);
    const components = [{factor: "Age / sex", points: score}];
    for (const [key, label, points] of FACTORS) {
      if (input[key]) {
        score += points;
        components.push({factor: label, points: points});
      }
    }
    const classIScreen = input.age <= 50 && !FACTORS.some(
      ([key, , , group]) => (group === "comorbidity" || group === "examination") && input[key]
    );
    const riskClass = classIScreen ? "I" : score <= 70 ? "II" : score <= 90 ? "III" : score <= 130 ? "IV" : "V";
    return {
      score: score, risk_class: riskClass, class_i_screen: classIScreen,
      risk_level: DISPOSITION[riskClass][0],
      recommended_disposition: DISPOSITION[riskClass][1],
      components: components
    };
  }
  const API = Object.freeze({FACTORS, scorePSI});
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.PSI = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
