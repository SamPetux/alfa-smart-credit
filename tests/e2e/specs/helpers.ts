import { type APIRequestContext, type Browser, type BrowserContext, type Page, expect } from "@playwright/test";
import path from "node:path";

/** Fixture relative to Playwright cwd (`tests/e2e`). */
export const MIN_PDF = path.join(process.cwd(), "fixtures", "summary.pdf");

export async function newRoleContext(browser: Browser): Promise<{ context: BrowserContext; page: Page }> {
  const context = await browser.newContext();
  const page = await context.newPage();
  return { context, page };
}

export async function openDemoProfile(page: Page, displayNamePart: string, intent: "new" | "home" | "queue") {
  await page.goto("/demo");
  const card = page.locator(".profile-card").filter({ hasText: displayNamePart });
  await expect(card).toBeVisible();
  if (intent === "new") {
    await card.getByRole("button", { name: "Начать новую заявку" }).click();
  } else if (intent === "queue") {
    await card.getByRole("button", { name: "Открыть очередь" }).click();
  } else {
    await card.getByRole("button", { name: /Мои заявки|Открыть очередь/ }).click();
  }
}

/** Cookie-сессия уже в context; читаем заявку через same-origin API. */
export async function waitApplicationStatus(
  request: APIRequestContext,
  applicationId: string,
  status: string,
  { timeoutMs = 90_000 } = {},
) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = await request.get(`/api/v1/applications/${applicationId}`);
    if (res.ok()) {
      const body = await res.json();
      if (body.status === status) return body;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`Timeout waiting for status=${status} on ${applicationId}`);
}

/** Radio перехватывает клик по title-span — выбираем input напрямую. */
export async function selectWorkingCapital(page: Page) {
  await page.locator('input[type="radio"][name="product"][value="WORKING_CAPITAL"]').check();
}

export async function fillWorkingCapitalDraft(page: Page) {
  await page.getByLabel("Сумма кредита").fill("1000000");
  await page.getByRole("radio", { name: "12 мес." }).check();
  await page.getByLabel("Организационно-правовая форма").selectOption("LLC");
  await page.getByLabel("Выручка в месяц").fill("1500000");
  await page.getByLabel("Операционные расходы в месяц").fill("1000000");
  await page.getByLabel("Платежи по действующим кредитам в месяц").fill("100000");
  await page.getByRole("button", { name: "Сохранить черновик" }).click();
  await expect(page.getByText(/Сохранено на сервере/)).toBeVisible({ timeout: 15_000 });
}
