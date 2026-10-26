import { expect, test } from "@playwright/test";
import { newRoleContext, openDemoProfile, selectWorkingCapital } from "./helpers";

test("E07/E13: foreign application hidden; profile switch clears prior company", async ({ browser }) => {
  const romashka = await newRoleContext(browser);
  await openDemoProfile(romashka.page, "Ромашка", "new");
  await selectWorkingCapital(romashka.page);
  const create = romashka.page.getByRole("button", { name: "Создать черновик" });
  await expect(create).toBeEnabled();
  await create.click();
  await expect(romashka.page).toHaveURL(/\/applications\/[^/]+\/edit/, { timeout: 30_000 });
  const appId = romashka.page.url().split("/applications/")[1].split("/")[0];

  // Чужой клиент: API без UI (меньше гонок с E01).
  const ivanov = await newRoleContext(browser);
  await openDemoProfile(ivanov.page, "Иванов", "home");
  await expect(ivanov.page).toHaveURL(/\/applications$/);
  const listRes = await ivanov.context.request.get("/api/v1/applications");
  expect(listRes.ok()).toBeTruthy();
  const items = (await listRes.json()).items as { id: string }[];
  expect(items.every((row) => row.id !== appId)).toBeTruthy();

  const direct = await ivanov.context.request.get(`/api/v1/applications/${appId}`);
  expect(direct.status()).toBe(404);

  const bank = await ivanov.context.request.get("/api/v1/bank/applications");
  expect(bank.status()).toBe(403);

  // E13: смена профиля в том же browser context.
  await romashka.page.goto("/demo");
  await openDemoProfile(romashka.page, "Иванов", "home");
  await expect(romashka.page).toHaveURL(/\/applications$/);
  const afterSwitch = await romashka.context.request.get(`/api/v1/applications/${appId}`);
  expect(afterSwitch.status()).toBe(404);

  await romashka.context.close();
  await ivanov.context.close();
});
