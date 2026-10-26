import riskOutput from "@contracts/schemas/risk-v1.output.json";

/** Коды причин — только из contracts/schemas/risk-v1.output.json. */
export const REASON_CODES: string[] = riskOutput.properties.reason_codes.items.enum;

/** Пояснения для сотрудника по таблице причин из docs/planning/02-architecture.md §7. */
const REASON_TEXT: Record<string, string> = {
  MISSING_DATA: "Не хватает сведений для расчёта",
  DEBT_DATA_MISMATCH: "Заявленные платежи расходятся с данными бюро",
  REGISTRY_INACTIVE: "Статус компании в реестре требует отказа",
  BUSINESS_TOO_YOUNG: "Возраст бизнеса ниже минимума продукта",
  OVERDUE_LIMIT: "Просрочка выше допустимого порога",
  RISK_POLICY_LIMIT: "Профиль не проходит демонстрационную политику",
  LOWER_AMOUNT_REQUIRED: "Доступна меньшая сумма по DSCR",
  AFFORDABILITY_BELOW_MINIMUM: "Доступная сумма ниже минимума продукта",
  CASHFLOW_NON_POSITIVE: "Неположительный денежный поток",
};

export function reasonText(code: string): string {
  return REASON_TEXT[code] ?? code;
}

const RECOMMENDATIONS: Record<string, string> = {
  OFFER: "Предложить условия",
  REJECT: "Отказать",
  NEEDS_INFO: "Запросить сведения",
};

export function recommendationText(value: string | null | undefined): string {
  if (!value) return "Нет рекомендации";
  return RECOMMENDATIONS[value] ?? value;
}

const FACTORS: Record<string, string> = {
  AGE: "Возраст бизнеса",
  MARGIN: "Маржинальность",
  PAYMENT_HISTORY: "Платёжная дисциплина",
  EXISTING_DEBT: "Текущая долговая нагрузка",
};

export function factorText(code: string): string {
  return FACTORS[code] ?? code;
}

const SOURCES: Record<string, string> = {
  registry: "Реестр юрлиц",
  bureau: "Кредитное бюро",
};

export function sourceText(source: string): string {
  return SOURCES[source] ?? source;
}

const OUTCOMES: Record<string, { label: string; ok: boolean }> = {
  success: { label: "Получен ответ", ok: true },
  timeout: { label: "Нет ответа (таймаут)", ok: false },
  unavailable: { label: "Источник недоступен", ok: false },
  incomplete: { label: "Неполный ответ", ok: false },
  schema_error: { label: "Ответ неверного формата", ok: false },
};

export function outcomeOf(outcome: string): { label: string; ok: boolean } {
  return OUTCOMES[outcome.toLowerCase()] ?? { label: outcome, ok: false };
}

/** DSCR приходит строкой: только замена разделителя, без округления на клиенте. */
export function formatRatio(value: string | null | undefined): string {
  return value ? value.replace(".", ",") : "—";
}
