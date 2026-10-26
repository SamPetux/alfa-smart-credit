import { request } from "./http";
import type {
  Agreement,
  ApplicationListResponse,
  BankApplication,
  BankApplicationListResponse,
  BankQueueFilters,
  ClientApplication,
  DemoProfile,
  DraftFieldsInput,
  ExplainResponse,
  HistoryResponse,
  InfoRequest,
  MetaResponse,
  Offer,
  Product,
  SessionInfo,
  UploadedDocument,
} from "./types";

type Signal = { signal?: AbortSignal };
type Command = { idempotencyKey: string };

export const api = {
  meta: ({ signal }: Signal = {}) => request<MetaResponse>("GET", "/meta", { signal }),

  /* identity */
  demoProfiles: ({ signal }: Signal = {}) =>
    request<{ profiles: DemoProfile[] }>("GET", "/demo/profiles", { signal }).then((r) => r.profiles),
  startDemoSession: (profileId: string) =>
    request<SessionInfo>("POST", "/demo/session", { body: { profile_id: profileId } }),
  login: (username: string, password: string) =>
    request<SessionInfo>("POST", "/auth/login", { body: { username, password } }),
  me: ({ signal }: Signal = {}) => request<SessionInfo>("GET", "/auth/me", { signal }),
  logout: () => request<null>("POST", "/auth/logout"),

  /* catalog */
  products: ({ signal }: Signal = {}) =>
    request<{ products: Product[] }>("GET", "/products", { signal }).then((r) => r.products),

  /* client applications */
  listApplications: ({ signal }: Signal = {}) =>
    request<ApplicationListResponse>("GET", "/applications", { signal }).then((r) => r.items),
  createApplication: (productCode: Product["code"], { idempotencyKey }: Command) =>
    request<ClientApplication>("POST", "/applications", {
      body: { product_code: productCode },
      idempotencyKey,
    }),
  getApplication: (id: string, { signal }: Signal = {}) =>
    request<ClientApplication>("GET", `/applications/${id}`, { signal }),
  saveDraft: (id: string, expectedVersion: number, draftFields: DraftFieldsInput) =>
    request<ClientApplication>("PATCH", `/applications/${id}`, {
      body: { expected_version: expectedVersion, draft_fields: draftFields },
    }),
  listDocuments: (id: string, { signal }: Signal = {}) =>
    request<{ items: UploadedDocument[] }>("GET", `/applications/${id}/documents`, { signal }).then(
      (r) => r.items,
    ),
  uploadDocument: (
    id: string,
    input: { kind: string; file: File; expectedVersion: number },
    { idempotencyKey }: Command,
  ) => {
    const form = new FormData();
    form.set("kind", input.kind);
    form.set("expected_version", String(input.expectedVersion));
    form.set("file", input.file);
    return request<UploadedDocument>("POST", `/applications/${id}/documents`, {
      formData: form,
      idempotencyKey,
    });
  },
  submit: (id: string, expectedVersion: number, { idempotencyKey }: Command) =>
    request<ClientApplication>("POST", `/applications/${id}/submit`, {
      body: { expected_version: expectedVersion },
      idempotencyKey,
    }),
  history: (id: string, { signal }: Signal = {}) =>
    request<HistoryResponse>("GET", `/applications/${id}/history`, { signal }).then((r) => r.events),
  infoRequest: (id: string, { signal }: Signal = {}) =>
    request<InfoRequest | null>("GET", `/applications/${id}/info-request`, { signal }),
  resubmit: (id: string, expectedVersion: number, infoRequestId: string, { idempotencyKey }: Command) =>
    request<ClientApplication>("POST", `/applications/${id}/resubmit`, {
      body: { expected_version: expectedVersion, info_request_id: infoRequestId },
      idempotencyKey,
    }),
  offer: (id: string, { signal }: Signal = {}) =>
    request<Offer | null>("GET", `/applications/${id}/offer`, { signal }),
  acceptOffer: (id: string, expectedVersion: number, offerId: string, { idempotencyKey }: Command) =>
    request<ClientApplication>("POST", `/applications/${id}/offer/accept`, {
      body: { expected_version: expectedVersion, offer_id: offerId },
      idempotencyKey,
    }),
  declineOffer: (id: string, expectedVersion: number, offerId: string, { idempotencyKey }: Command) =>
    request<ClientApplication>("POST", `/applications/${id}/offer/decline`, {
      body: { expected_version: expectedVersion, offer_id: offerId },
      idempotencyKey,
    }),
  agreement: (id: string, { signal }: Signal = {}) =>
    request<Agreement | null>("GET", `/applications/${id}/agreement`, { signal }),
  simulateSign: (
    id: string,
    input: { expectedVersion: number; agreementId: string; contentHash: string },
    { idempotencyKey }: Command,
  ) =>
    request<ClientApplication>("POST", `/applications/${id}/agreement/simulate-sign`, {
      body: {
        expected_version: input.expectedVersion,
        agreement_id: input.agreementId,
        content_hash: input.contentHash,
        consent: true,
      },
      idempotencyKey,
    }),
  explain: (id: string, topic: "general" | "why" | "next" | "amount", { signal }: Signal = {}) =>
    request<ExplainResponse>("GET", `/applications/${id}/explain`, { query: { topic }, signal }),

  /* bank */
  bankQueue: (filters: BankQueueFilters, { signal }: Signal = {}) =>
    request<BankApplicationListResponse>("GET", "/bank/applications", {
      query: { status: filters.status, product_code: filters.product_code, limit: filters.limit },
      signal,
    }).then((r) => r.items),
  bankApplication: (id: string, { signal }: Signal = {}) =>
    request<BankApplication>("GET", `/bank/applications/${id}`, { signal }),
  requestInfo: (
    id: string,
    input: { expectedVersion: number; fields: string[]; documentKinds: string[]; message: string },
    { idempotencyKey }: Command,
  ) =>
    request<BankApplication>("POST", `/bank/applications/${id}/request-info`, {
      body: {
        expected_version: input.expectedVersion,
        fields: input.fields,
        document_kinds: input.documentKinds,
        message: input.message,
      },
      idempotencyKey,
    }),
  approveOffer: (
    id: string,
    input: { expectedVersion: number; runId: string; candidateHash: string },
    { idempotencyKey }: Command,
  ) =>
    request<BankApplication>("POST", `/bank/applications/${id}/decision`, {
      body: {
        expected_version: input.expectedVersion,
        run_id: input.runId,
        type: "APPROVE_OFFER",
        candidate_hash: input.candidateHash,
      },
      idempotencyKey,
    }),
  reject: (
    id: string,
    input: { expectedVersion: number; runId: string; reasonCode: string; comment: string },
    { idempotencyKey }: Command,
  ) =>
    request<BankApplication>("POST", `/bank/applications/${id}/decision`, {
      body: {
        expected_version: input.expectedVersion,
        run_id: input.runId,
        type: "REJECT",
        reason_code: input.reasonCode,
        comment: input.comment,
      },
      idempotencyKey,
    }),
  retryChecks: (id: string, expectedVersion: number, { idempotencyKey }: Command) =>
    request<BankApplication>("POST", `/bank/applications/${id}/retry-checks`, {
      body: { expected_version: expectedVersion },
      idempotencyKey,
    }),
  retryDisbursement: (id: string, expectedVersion: number, { idempotencyKey }: Command) =>
    request<BankApplication>("POST", `/bank/applications/${id}/retry-disbursement`, {
      body: { expected_version: expectedVersion },
      idempotencyKey,
    }),
};
