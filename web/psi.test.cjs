"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { FACTORS, scorePSI } = require("./psi.js");

function patient(age = 65, sex = "male", features = {}) {
  return Object.assign({age, sex}, Object.fromEntries(FACTORS.map(([key]) => [key, false])), features);
}
test("Class I is a screening rule, not a score band", () => {
  assert.equal(scorePSI(patient(50)).risk_class, "I");
  const caseWithLabs = scorePSI(patient(50, "female", {
    arterial_ph_lt_7_35: true, bun_ge_30: true, sodium_lt_130: true
  }));
  assert.equal(caseWithLabs.score, 110);
  assert.equal(caseWithLabs.risk_class, "I");
  assert.equal(scorePSI(patient(50, "male", {pulse_ge_125: true})).risk_class, "II");
});
test("Numerical bands and class-V boundary", () => {
  for (const [age, expected] of [[51,"II"],[70,"II"],[71,"III"],[90,"III"],[91,"IV"],[120,"IV"]]) {
    assert.equal(scorePSI(patient(age)).risk_class, expected);
  }
  assert.equal(scorePSI(patient(101, "male", {neoplastic_disease:true})).risk_class, "V");
});
test("Core point weights and female adjustment", () => {
  assert.equal(scorePSI(patient(65, "male", {temperature_extreme:true})).score, 80);
  assert.equal(scorePSI(patient(65, "female", {temperature_extreme:true})).score, 70);
  assert.equal(scorePSI(patient(72, "male", {hypoxemia:true})).score, 82);
});
test("Reject unknown or unassessed inputs", () => {
  for (const age of [17,121, 50.5, NaN, Infinity]) {
    assert.throws(() => scorePSI(patient(age)), /Age/);
  }
  assert.throws(() => scorePSI(patient(65, "other")), /sex|male/i);
  assert.throws(() => scorePSI(patient(65, "male", {bun_ge_30:undefined})), /assessed/);
  assert.throws(() => scorePSI(patient(65, "male", {extra:true})), /Unknown/);
});
test("All published fields are represented exactly once", () => {
  const names = FACTORS.map(row => row[0]);
  assert.equal(names.length, 18);
  assert.equal(new Set(names).size, 18);
});
