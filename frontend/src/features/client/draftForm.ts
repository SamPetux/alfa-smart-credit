import type { DraftFields, DraftFieldName, DraftFieldsInput, Money, Product } from "../../api/types";
import { formatAmount, toKopecks } from "../../shared/money";
import { amountStep } from "./policy";

/** Поля формы, которые клиент заполняет сам. purpose задан продуктом и не редактируется. */
export const EDITABLE_FIELDS = [
  "requested_amount",
  "term_months",
  "company_form",
  "monthly_revenue",
  "monthly_operating_costs",
  "declared_monthly_debt_payments",
] as const satisfies readonly DraftFieldName[];

export type EditableField = (typeof EDITABLE_FIELDS)[number];

export interface DraftFormValues {
  requested_amount: Money | null;
  term_months: number | null;
  company_form: string | null;
  monthly_revenue: Money | null;
  monthly_operating_costs: Money | null;
  declared_monthly_debt_payments: Money | null;
}

export const FIELD_LABELS: Record<EditableField | "purpose" | "documents", string> = {
  purpose: "Цель кредита",
  requested_amount: "Сумма кредита",
  term_months: "Срок",
  company_form: "Организационно-правовая форма",
  monthly_revenue: "Выручка в месяц",
  monthly_operating_costs: "Операционные расходы в месяц",
  declared_monthly_debt_payments: "Платежи по действующим кредитам в месяц",
  documents: "Документы",
};

/** Значения не из enum контракта: company_form в API — свободная строка (уточнить у Олега). */
export const COMPANY_FORMS = [
  { value: "LLC", label: "ООО" },
  { value: "IP", label: "ИП" },
] as const;

export function valuesFromDraft(draft: DraftFields | null | undefined): DraftFormValues {
  return {
    requested_amount: draft?.requested_amount ?? null,
    term_months: draft?.term_months ?? null,
    company_form: draft?.company_form ?? null,
    monthly_revenue: draft?.monthly_revenue ?? null,
    monthly_operating_costs: draft?.monthly_operating_costs ?? null,
    declared_monthly_debt_payments: draft?.declared_monthly_debt_payments ?? null,
  };
}

/**
 * PATCH только изменённых полей. Очищенное поле уходит как null — сервер удаляет его
 * из черновика, а не записывает ноль.
 */
export function changedFields(
  saved: DraftFormValues,
  current: DraftFormValues,
  allowed: readonly EditableField[] = EDITABLE_FIELDS,
): DraftFieldsInput {
  const patch: DraftFieldsInput = {};
  for (const field of allowed) {
    if (saved[field] !== current[field]) {
      (patch as Record<string, unknown>)[field] = current[field];
    }
  }
  return patch;
}

export function isDirty(saved: DraftFormValues, current: DraftFormValues, allowed?: readonly EditableField[]): boolean {
  return Object.keys(changedFields(saved, current, allowed)).length > 0;
}

export type FieldErrors = Partial<Record<EditableField | "documents" | "purpose", string>>;

/**
 * Подсказки до отправки на сервер: формат и границы продукта. Сервер повторяет проверку,
 * его field_errors имеют приоритет.
 */
export function validateForSubmit(values: DraftFormValues, product: Product | undefined): FieldErrors {
  const errors: FieldErrors = {};
  for (const field of EDITABLE_FIELDS) {
    if (values[field] === null || values[field] === "") errors[field] = "Заполните поле";
  }
  if (product && values.requested_amount) {
    const amount = toKopecks(values.requested_amount);
    const step = toKopecks(amountStep(product.code));
    if (amount < toKopecks(product.amount_min) || amount > toKopecks(product.amount_max)) {
      errors.requested_amount = `Допустимо от ${formatAmount(product.amount_min)} до ${formatAmount(product.amount_max)}`;
    } else if (step > 0n && amount % step !== 0n) {
      errors.requested_amount = `Сумма должна быть кратна ${formatAmount(amountStep(product.code))}`;
    }
  }
  if (product && values.term_months !== null && !product.term_months.includes(values.term_months)) {
    errors.term_months = "Выберите срок из доступных для продукта";
  }
  if (values.monthly_revenue && toKopecks(values.monthly_revenue) === 0n) {
    errors.monthly_revenue = "Выручка должна быть больше нуля";
  }
  return errors;
}

/** Ошибки сервера (field_errors) в формат формы. */
export function serverFieldErrors(fieldErrors: Array<{ field: string; message: string }>): FieldErrors {
  const errors: FieldErrors = {};
  for (const item of fieldErrors) {
    const key = item.field as keyof FieldErrors;
    errors[key] = errors[key] ? `${errors[key]}; ${item.message}` : item.message;
  }
  return errors;
}
