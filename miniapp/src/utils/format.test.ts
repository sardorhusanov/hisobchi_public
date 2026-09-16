import assert from "node:assert/strict";
import test from "node:test";
import { formatMoney, normalizeMoney, previousMonth } from "./format.ts";
test("formats money without losing integer precision", () => {
  assert.equal(formatMoney("16.6666666667"), "16.67 so'm");
  assert.equal(formatMoney("6000000.00"), "6 000 000 so'm");
  assert.equal(
    formatMoney("9999999999999999.99"),
    "9 999 999 999 999 999.99 so'm",
  );
  assert.equal(formatMoney("-2700000.50"), "-2 700 000.50 so'm");
});
test("accepts supported money inputs", () => {
  for (const value of ["6000000", "6 000 000", "6,000,000"])
    assert.equal(normalizeMoney(value), "6000000");
});
test("rejects invalid and excessive money", () => {
  for (const value of [
    "0",
    "-1",
    "NaN",
    "1e6",
    "1,5",
    "1.001",
    "6 00 000",
    "10000000000000000",
  ])
    assert.throws(() => normalizeMoney(value));
});
test("previous month crosses year", () => {
  assert.equal(previousMonth("2026-01"), "2025-12");
});
