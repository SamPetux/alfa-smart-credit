/**
 * Типы API v1 для frontend.
 *
 * Основа — `schema.gen.ts`, сгенерированный из contracts/openapi.json (`npm run gen:api`).
 * Ниже вручную описаны только те ответы, которые backend отдаёт как `dict` без схемы
 * (досье, история, explain, upload). Их нужно перенести в OpenAPI — зависимость Олега.
 */
import type { components } from "./schema.gen";

type Schemas = components["schemas"];

/** Money в JSON — строка с двумя знаками после точки ("1234.56"), никогда number. */
export type Money = string;

export type ApplicationStatus = Schemas["ApplicationStatus"];
export type AllowedAction = Schemas["AllowedAction"];
export type ProductCode = Schemas["ProductCode"];
export type Role = Schemas["Role"];

export type SessionInfo = Schemas["SessionInfo"];
export type UserBrief = Schemas["UserBrief"];
export type DemoProfile = Schemas["DemoProfile"];
export type Product = Schemas["ProductOut"];
export type ClientApplication = Schemas["ClientApplication"];
export type BankApplicationBase = Schemas["BankApplication"];
export type InfoRequest = Schemas["InfoRequestOut"];
export type Agreement = Schemas["AgreementOut"];
export type FieldError = { field: string; message: string };

export type DraftFields = Schemas["DraftFields-Output"];

/** Вход PATCH: OpenAPI допускает number для Decimal, frontend отправляет только строки. */
export type DraftFieldsInput = {
  purpose?: DraftFields["purpose"];
  requested_amount?: Money | null;
  term_months?: number | null;
  company_form?: string | null;
  monthly_revenue?: Money | null;
  monthly_operating_costs?: Money | null;
  declared_monthly_debt_payments?: Money | null;
};

export type DraftFieldName = keyof DraftFieldsInput;

export interface OfferTerms {
  product_code?: ProductCode;
  amount?: Money;
  term_months?: number;
  annual_rate?: string;
  currency?: string;
  fees?: Money;
  is_alternative?: boolean;
  /** Пока не передаются сервером (B07): см. limitations в README frontend. */
  monthly_payment?: Money;
  total_payment?: Money;
}

export type Offer = Omit<Schemas["OfferOut"], "terms"> & { terms: OfferTerms };

/* ---- Ответы backend без схемы в OpenAPI (dict) ---- */

export interface AuditEvent {
  action: string;
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus | null;
  revision_no: number;
  created_at: string | null;
}

export interface HistoryResponse {
  events: AuditEvent[];
}

export interface UploadedDocument {
  id: string;
  kind: string;
  content_hash: string;
  version: number;
}

export interface ExplainResponse {
  engine: string;
  is_simulation: boolean;
  uses_llm: boolean;
  topic: string;
  headline: string;
  next_step: string;
  reason_codes: string[];
  bullets: string[];
  disclaimer: string;
}

export interface RiskFactor {
  code: string;
  points: number;
}

/** Совпадает с полем affordability в contracts/schemas/risk-v1.output.json. */
export interface Affordability {
  free_cashflow?: Money | null;
  existing_payment?: Money | null;
  requested_payment?: Money | null;
  requested_dscr?: string | null;
  offered_payment?: Money | null;
  offered_dscr?: string | null;
  total_payment?: Money | null;
}

export interface RiskSummary {
  score: number | null;
  band: string | null;
  recommendation: "OFFER" | "REJECT" | "NEEDS_INFO" | string | null;
  reasons: string[] | null;
  candidate: OfferTerms | null;
  candidate_hash: string | null;
  affordability: Affordability | null;
  factors: RiskFactor[] | null;
}

export interface IntegrationCheck {
  source: string;
  outcome: string;
  attempt_count: number;
  observed_at: string | null;
}

export interface RevisionRow {
  revision_no: number;
  snapshot_hash: string;
  submitted_at: string;
}

export type BankApplication = Omit<
  BankApplicationBase,
  "risk_summary" | "checks" | "revisions" | "audit"
> & {
  risk_summary: RiskSummary | null;
  checks: IntegrationCheck[];
  revisions: RevisionRow[];
  audit: AuditEvent[];
};

export interface ApplicationListResponse {
  items: ClientApplication[];
  next_cursor?: string | null;
}

export interface BankApplicationListResponse {
  items: BankApplication[];
  next_cursor?: string | null;
}

export interface BankQueueFilters {
  status?: ApplicationStatus;
  product_code?: ProductCode;
  limit?: number;
}

export interface MetaResponse {
  app_env: string;
  demo_mode: boolean;
  api_version: string;
  is_simulation: boolean;
  privacy_notice: string;
}
