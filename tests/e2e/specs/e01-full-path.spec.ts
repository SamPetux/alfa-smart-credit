import { expect, test } from "@playwright/test";
import {
  fillWorkingCapitalDraft,
  MIN_PDF,
  newRoleContext,
  openDemoProfile,
  selectWorkingCapital,
  waitApplicationStatus,
} from "./helpers";

/**
 * E01: отдельные browser contexts для CLIENT и OFFICER.
 * Проверяем UI-шаги и итоговый статус через API той же cookie-сессии клиента.
 */
test("E01 empty application to simulated disbursement", async ({ browser }) => {
  const client = await newRoleContext(browser);
  const officer = await newRoleContext(browser);

  await openDemoProfile(client.page, "Ромашка", "new");
  await expect(client.page).toHaveURL(/\/applications\/new/);
  await selectWorkingCapital(client.page);
  await client.page.getByRole("button", { name: "Создать черновик" }).click();
  await expect(client.page).toHaveURL(/\/applications\/[^/]+\/edit/);
  const applicationId = client.page.url().split("/applications/")[1].split("/")[0];

  await fillWorkingCapitalDraft(client.page);
  await client.page.locator('input[type="file"]').setInputFiles(MIN_PDF);
  await client.page.getByRole("button", { name: "Загрузить", exact: true }).click();
  await expect(client.page.getByText("Загружен").first()).toBeVisible({ timeout: 20_000 });

  await client.page.getByRole("button", { name: "Отправить заявку" }).click();
  await client.page.getByRole("button", { name: "Отправить", exact: true }).click();

  await waitApplicationStatus(client.context.request, applicationId, "MANUAL_REVIEW");

  await openDemoProfile(officer.page, "специалист", "queue");
  await expect(officer.page).toHaveURL(/\/bank\/applications/);
  await officer.page.goto(`/bank/applications/${applicationId}`);
  await officer.page.getByRole("button", { name: "Подтвердить рассчитанное предложение" }).click();
  await officer.page.getByRole("button", { name: "Подтвердить условия" }).click();
  await expect(officer.page.getByText(/Подтвержден|предложен|OFFERED|услови/i).first()).toBeVisible({
    timeout: 20_000,
  });

  await client.page.goto(`/applications/${applicationId}`);
  await expect(client.page.getByRole("button", { name: "Принять условия" })).toBeVisible({ timeout: 30_000 });
  await client.page.getByRole("button", { name: "Принять условия" }).click();
  await client.page.locator("label.checkbox").filter({ hasText: /ознакомился с документом/i }).click();
  await client.page.getByRole("button", { name: "Смоделировать подписание" }).click();

  const completed = await waitApplicationStatus(client.context.request, applicationId, "COMPLETED");
  expect(completed.status).toBe("COMPLETED");
  await expect(client.page.getByText(/Выдача смоделирована|смоделирован/i).first()).toBeVisible({
    timeout: 60_000,
  });

  await client.context.close();
  await officer.context.close();
});
