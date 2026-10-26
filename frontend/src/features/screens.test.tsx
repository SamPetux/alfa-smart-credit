import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { vi } from "vitest";
import { resetSessionScope } from "../api/http";
import type { BankApplication, ClientApplication } from "../api/types";
import { RequireRole } from "../app/guards";
import { clientSession, json, mockFetch, officerSession, renderRoute } from "../test/render";
import { OfficerActions } from "./bank/OfficerActions";
import { OfferPanel } from "./client/OfferPanel";

afterEach(() => {
  vi.unstubAllGlobals();
  resetSessionScope();
});

describe("RequireRole", () => {
  it("sends a visitor without a session to /demo", async () => {
    mockFetch((url) => (url.endsWith("/auth/me") ? json(401, { detail: "Not authenticated" }) : undefined));
    renderRoute(
      <RequireRole role="OFFICER">
        <p>queue</p>
      </RequireRole>,
    );
    expect(await screen.findByText("demo page")).toBeInTheDocument();
  });

  it("explains instead of rendering another role's screen", async () => {
    mockFetch((url) => (url.endsWith("/auth/me") ? json(200, clientSession) : undefined));
    renderRoute(
      <RequireRole role="OFFICER">
        <p>queue</p>
      </RequireRole>,
    );
    expect(await screen.findByText("Раздел недоступен для текущего профиля")).toBeInTheDocument();
    expect(screen.queryByText("queue")).not.toBeInTheDocument();
  });
});

const offeredApp: ClientApplication = {
  id: "app-1",
  status: "OFFERED",
  version: 7,
  current_revision: 1,
  next_action: "Принять или отклонить",
  allowed_actions: ["ACCEPT_OFFER", "DECLINE_OFFER"],
  is_simulation: true,
  updated_at: "2026-10-26T10:00:00Z",
  product_code: "WORKING_CAPITAL",
  draft_fields: { requested_amount: "1000000.00" },
};

describe("OfferPanel", () => {
  it("shows server payment terms and does not invent missing ones", async () => {
    mockFetch((url) => {
      if (url.endsWith("/auth/me")) return json(200, clientSession);
      if (url.endsWith("/offer"))
        return json(200, {
          id: "offer-1",
          status: "ACTIVE",
          revision_no: 1,
          created_at: "2026-10-26T10:00:00Z",
          terms: {
            amount: "641000.00",
            term_months: 12,
            annual_rate: "0.22",
            fees: "0.00",
            is_alternative: true,
            monthly_payment: "59994.00",
            total_payment: "719928.00",
          },
        });
      if (url.includes("/explain")) return json(200, { bullets: [], disclaimer: "", headline: "", reason_codes: [] });
      return undefined;
    });
    renderRoute(<OfferPanel app={offeredApp} />);
    expect(await screen.findByText(/^641\s000\s₽$/)).toBeInTheDocument();
    expect(screen.getByText(/Вы запрашивали 1\s000\s000\s₽/)).toBeInTheDocument();
    expect(screen.getByText(/59\s994/)).toBeInTheDocument();
    expect(screen.getByText(/719\s928/)).toBeInTheDocument();
  });

  it("sends accept with the current version and an idempotency key", async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url.endsWith("/auth/me")) return json(200, clientSession);
      if (url.endsWith("/offer"))
        return json(200, { id: "offer-1", status: "ACTIVE", revision_no: 1, created_at: "x", terms: { amount: "641000.00" } });
      if (url.endsWith("/offer/accept") && init?.method === "POST") return json(200, { ...offeredApp, status: "ACCEPTED", version: 8 });
      if (url.includes("/explain")) return json(200, { bullets: [], disclaimer: "", headline: "", reason_codes: [] });
      return undefined;
    });
    renderRoute(<OfferPanel app={offeredApp} />);
    await userEvent.click(await screen.findByRole("button", { name: "Принять условия" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([u]) => String(u).endsWith("/offer/accept"))).toBe(true));
    const [, init] = fetchMock.mock.calls.find(([u]) => String(u).endsWith("/offer/accept"))!;
    expect(JSON.parse(String(init?.body))).toEqual({ expected_version: 7, offer_id: "offer-1" });
    expect((init?.headers as Record<string, string>)["Idempotency-Key"]).toMatch(/[0-9a-f-]{36}/);
  });
});

const reviewApp = {
  id: "app-2",
  status: "MANUAL_REVIEW",
  version: 6,
  current_revision: 1,
  allowed_actions: ["REQUEST_INFO", "REJECT"],
  is_simulation: true,
  active_run_id: "run-1",
  product_code: "WORKING_CAPITAL",
  risk_summary: {
    score: null,
    band: null,
    recommendation: "REJECT",
    reasons: ["OVERDUE_LIMIT"],
    candidate: null,
    candidate_hash: null,
    affordability: null,
    factors: [],
  },
  checks: [],
  revisions: [],
  audit: [],
} as unknown as BankApplication;

describe("OfficerActions", () => {
  it("offers no approval without a current OFFER recommendation", async () => {
    mockFetch((url) => (url.endsWith("/auth/me") ? json(200, officerSession) : undefined));
    renderRoute(<OfficerActions app={reviewApp} />);
    expect(await screen.findByRole("button", { name: "Отказать с причиной" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Подтвердить/ })).not.toBeInTheDocument();
  });

  it("reports a 409 and does not resend the decision", async () => {
    const fetchMock = mockFetch((url, init) => {
      if (url.endsWith("/auth/me")) return json(200, officerSession);
      if (url.endsWith("/decision") && init?.method === "POST")
        return json(409, { error: { code: "VERSION_CONFLICT", message: "m", field_errors: [], request_id: "r" } });
      return json(200, reviewApp);
    });
    renderRoute(<OfficerActions app={reviewApp} />);
    await userEvent.click(await screen.findByRole("button", { name: "Отказать с причиной" }));
    expect(screen.getByLabelText(/Причина/)).toHaveValue("OVERDUE_LIMIT");
    await userEvent.type(screen.getByLabelText(/Комментарий/), "Просрочка");
    await userEvent.click(screen.getByRole("button", { name: "Отказать" }));
    expect(await screen.findByText("Заявка изменилась, пока вы её рассматривали.")).toBeInTheDocument();
    const decisions = fetchMock.mock.calls.filter(([u]) => String(u).endsWith("/decision"));
    expect(decisions).toHaveLength(1);
    expect(JSON.parse(String(decisions[0]![1]?.body))).toMatchObject({
      expected_version: 6,
      run_id: "run-1",
      type: "REJECT",
      reason_code: "OVERDUE_LIMIT",
    });
  });
});
