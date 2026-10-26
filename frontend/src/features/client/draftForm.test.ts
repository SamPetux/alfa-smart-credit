import { describe, expect, it } from "vitest";
import type { Product } from "../../api/types";
import { isWorkerDriven } from "../../shared/status";
import { changedFields, serverFieldErrors, validateForSubmit, valuesFromDraft, type DraftFormValues } from "./draftForm";
import { requiredDocuments } from "./policy";

const product: Product = {
  code: "WORKING_CAPITAL",
  title: "Оборотный кредит",
  amount_min: "100000.00",
  amount_max: "3000000.00",
  term_months: [6, 12, 18, 24],
};

const filled: DraftFormValues = {
  requested_amount: "1000000.00",
  term_months: 12,
  company_form: "LLC",
  monthly_revenue: "600000.00",
  monthly_operating_costs: "400000.00",
  declared_monthly_debt_payments: "0.00",
};

describe("draft form", () => {
  it("patches only changed fields and sends cleared fields as null, never zero", () => {
    const saved = valuesFromDraft({ requested_amount: "1000000.00", monthly_revenue: "600000.00" });
    const patch = changedFields(saved, { ...saved, requested_amount: null, term_months: 12 });
    expect(patch).toEqual({ requested_amount: null, term_months: 12 });
  });

  it("restricts the patch to requested fields in NEEDS_INFO", () => {
    const saved = valuesFromDraft(filled);
    const patch = changedFields(
      saved,
      { ...saved, requested_amount: "5.00", declared_monthly_debt_payments: "120000.00" },
      ["declared_monthly_debt_payments"],
    );
    expect(patch).toEqual({ declared_monthly_debt_payments: "120000.00" });
  });

  it("accepts a complete draft and treats an explicit zero debt as filled", () => {
    expect(validateForSubmit(filled, product)).toEqual({});
  });

  it("flags missing fields, product bounds and the amount step", () => {
    expect(validateForSubmit({ ...filled, monthly_revenue: null }, product).monthly_revenue).toBe("Заполните поле");
    expect(validateForSubmit({ ...filled, requested_amount: "99000.00" }, product).requested_amount).toMatch(/Допустимо/);
    expect(validateForSubmit({ ...filled, requested_amount: "100500.00" }, product).requested_amount).toMatch(/кратна/);
    expect(validateForSubmit({ ...filled, term_months: 36 }, product).term_months).toBeDefined();
  });

  it("merges server field errors per field", () => {
    expect(
      serverFieldErrors([
        { field: "documents", message: "Нужен документ A" },
        { field: "documents", message: "Нужен документ B" },
      ]),
    ).toEqual({ documents: "Нужен документ A; Нужен документ B" });
  });

  it("takes required documents from contracts policy-v1", () => {
    expect(requiredDocuments("EQUIPMENT")).toEqual(["FINANCIAL_SUMMARY", "EQUIPMENT_QUOTE"]);
  });

  it("polls only while the worker owns the next step", () => {
    expect(isWorkerDriven("CHECKING")).toBe(true);
    expect(isWorkerDriven("SIGNED")).toBe(true);
    expect(isWorkerDriven("MANUAL_REVIEW")).toBe(false);
    expect(isWorkerDriven("COMPLETED")).toBe(false);
  });
});
