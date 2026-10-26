import type { Money } from "../api/types";

/**
 * Money живёт строкой "1234.56". Здесь только форматирование и проверка ввода —
 * без float и без кредитной арифметики (ставки, платежи, решения считает сервер).
 */

const MONEY_PATTERN = /^\d{1,13}(\.\d{1,2})?$/;
const NBSP = " ";

function groupThousands(digits: string): string {
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, NBSP);
}

/** "641000.00" → "641 000,00 ₽". Пустое значение — тире, ноль печатается как ноль. */
export function formatMoney(value: Money | null | undefined, { currency = true } = {}): string {
  if (value === null || value === undefined || value === "") return "—";
  const negative = value.startsWith("-");
  const [intPart = "0", fracPart = ""] = (negative ? value.slice(1) : value).split(".");
  const fraction = fracPart.padEnd(2, "0").slice(0, 2);
  const text = `${negative ? "−" : ""}${groupThousands(intPart.replace(/^0+(?=\d)/, ""))},${fraction}`;
  return currency ? `${text}${NBSP}₽` : text;
}

/** Целые рубли без копеек, когда копейки нулевые: для сумм кредита. */
export function formatAmount(value: Money | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const [intPart = "0", fracPart = ""] = value.split(".");
  if (/^0*$/.test(fracPart)) return `${groupThousands(intPart)}${NBSP}₽`;
  return formatMoney(value);
}

/** Десятичная доля строкой → проценты строкой: "0.22" → "22 %", "0.225" → "22,5 %". */
export function formatRate(value: string | null | undefined): string {
  if (!value) return "—";
  const [intPart = "0", fracPart = ""] = value.split(".");
  const padded = fracPart.padEnd(2, "0");
  const whole = `${intPart}${padded.slice(0, 2)}`.replace(/^0+(?=\d)/, "");
  const rest = padded.slice(2).replace(/0+$/, "");
  return `${whole}${rest ? `,${rest}` : ""}${NBSP}%`;
}

/** Ввод пользователя → Money или null, если формат неверен. Пробелы и запятая допустимы. */
export function parseMoneyInput(raw: string): Money | null {
  const compact = raw.replace(/[\s  ]/g, "").replace(",", ".");
  if (!MONEY_PATTERN.test(compact)) return null;
  const [intPart = "0", fracPart = ""] = compact.split(".");
  return `${intPart.replace(/^0+(?=\d)/, "")}.${fracPart.padEnd(2, "0")}`;
}

/** Money → копейки (BigInt) только для сравнения с границами продукта. */
export function toKopecks(value: Money): bigint {
  const [intPart = "0", fracPart = ""] = value.split(".");
  return BigInt(intPart) * 100n + BigInt(fracPart.padEnd(2, "0").slice(0, 2));
}

/** Значение для поля ввода: "1000000.00" → "1 000 000". */
export function moneyToInput(value: Money | null | undefined): string {
  if (!value) return "";
  const [intPart = "0", fracPart = ""] = value.split(".");
  const grouped = groupThousands(intPart);
  return /^0*$/.test(fracPart) ? grouped : `${grouped},${fracPart.padEnd(2, "0")}`;
}
