import policy from "@contracts/schemas/policy-v1.json";
import type { Money, ProductCode } from "../../api/types";

/**
 * Шаг суммы и обязательные документы есть только в contracts/schemas/policy-v1.json —
 * API /products их пока не отдаёт. Границы суммы и сроки берутся из /products.
 */
interface PolicyProduct {
  purpose: string;
  amount_step: Money;
  required_documents: string[];
}

const PRODUCTS = policy.products as Record<ProductCode, PolicyProduct>;

export function amountStep(code: ProductCode): Money {
  return PRODUCTS[code]?.amount_step ?? "1000.00";
}

export function requiredDocuments(code: ProductCode): string[] {
  return PRODUCTS[code]?.required_documents ?? [];
}

export const DOCUMENT_LABELS: Record<string, { title: string; hint: string }> = {
  FINANCIAL_SUMMARY: {
    title: "Финансовая справка",
    hint: "Демонстрационный файл: сервер проверяет тип и размер, содержание не анализируется.",
  },
  EQUIPMENT_QUOTE: {
    title: "Коммерческое предложение на оборудование",
    hint: "Демонстрационный файл: подтверждает только факт загрузки.",
  },
};

export function documentTitle(kind: string): string {
  return DOCUMENT_LABELS[kind]?.title ?? kind;
}
