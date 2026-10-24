/**
 * Типы API v1 для frontend. Зеркало contracts/; генерация из OpenAPI — позже.
 * Не дублировать enum статусов вручную в других местах.
 */

export type ApplicationStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "CHECKING"
  | "NEEDS_INFO"
  | "PROCESSING_ERROR"
  | "MANUAL_REVIEW"
  | "OFFERED"
  | "ACCEPTED"
  | "SIGNED"
  | "COMPLETED"
  | "REJECTED"
  | "DECLINED_BY_CLIENT";

export type AllowedAction =
  | "SAVE"
  | "SUBMIT"
  | "SAVE_SUPPLEMENT"
  | "RESUBMIT"
  | "ACCEPT_OFFER"
  | "DECLINE_OFFER"
  | "SIMULATE_SIGN"
  | "REQUEST_INFO"
  | "APPROVE_OFFER"
  | "REJECT"
  | "RETRY_CHECKS"
  | "RETRY_DISBURSEMENT";

export type ProductCode = "WORKING_CAPITAL" | "EQUIPMENT";

export type Role = "CLIENT" | "OFFICER";

/** Money in JSON is always a string with two decimal places. */
export type Money = string;

export interface ClientApplication {
  id: string;
  status: ApplicationStatus;
  version: number;
  current_revision: number;
  next_action: string;
  allowed_actions: AllowedAction[];
  is_simulation: boolean;
  updated_at: string;
  product_code?: ProductCode;
  draft_fields?: Record<string, unknown>;
}

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    field_errors: Array<{ field: string; message: string }>;
    request_id: string;
  };
}
