// Снимает экраны кабинетов на разных устройствах против локального стенда (vite preview :4174 + API :8000).
// Использование: node capture.cjs views <device...|all>   — статичные экраны по данным seed.json
//                node capture.cjs final <device...>       — сценарии с изменением данных, tour, «в обработке»
const fs = require("node:fs");
const path = require("node:path");
const { execSync } = require("node:child_process");
const { chromium } = require("playwright");
const L = require("./lib.cjs");
const DEVICES = require("./devices.cjs");

const BASE = process.env.BASE_URL || "http://127.0.0.1:4174";
const OUT = process.env.SHOTS_OUT || path.resolve(__dirname, "../../../docs/screenshots");
const { ids } = JSON.parse(fs.readFileSync(path.join(__dirname, "seed.json"), "utf8"));

const PROFILE = { romashka: "client-romashka", ivanov: "client-ivanov", officer: "officer" };

async function openContext(browser, device, extra = {}) {
  return browser.newContext({
    baseURL: BASE,
    viewport: device.viewport,
    deviceScaleFactor: device.dpr,
    isMobile: Boolean(device.mobile),
    hasTouch: Boolean(device.mobile),
    userAgent: device.userAgent,
    locale: "ru-RU",
    timezoneId: "Europe/Moscow",
    colorScheme: "light",
    reducedMotion: "no-preference",
    ...extra,
  });
}

async function loginContext(browser, device, who, extra) {
  const ctx = await openContext(browser, device, extra);
  if (who !== "anon") {
    const res = await ctx.request.post("/api/v1/demo/session", { data: { profile_id: PROFILE[who] } });
    if (!res.ok()) throw new Error(`login ${who} ${res.status()}`);
  }
  return ctx;
}

/** API-вызовы от имени уже открытого в браузере профиля (демо-сессия одна на пользователя). */
async function callAs(ctx) {
  const me = await (await ctx.request.get("/api/v1/auth/me")).json();
  return async (method, apiPath, { data, idem } = {}) => {
    const headers = { "X-CSRF-Token": me.csrf_token, ...(idem ? { "Idempotency-Key": L.key() } : {}) };
    const res = await ctx.request[method](`/api/v1${apiPath}`, { headers, data });
    if (!res.ok()) throw new Error(`${method} ${apiPath} -> ${res.status()} ${(await res.text()).slice(0, 200)}`);
    return res.json();
  };
}

async function settle(page, ms = 900) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(ms);
}

async function snap(page, dir, name, { full = false, settleMs } = {}) {
  await settle(page, settleMs);
  fs.mkdirSync(dir, { recursive: true });
  if (full) await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(dir, `${name}.png`), fullPage: full });
  console.log("  shot", path.relative(OUT, path.join(dir, `${name}.png`)));
}

const click = (page, name, opts = {}) => page.getByRole("button", { name, ...opts }).click();

/** Описание статичных экранов: [имя, роль, путь, {full, core, prep}] */
function viewList() {
  const app = (name) => `/applications/${ids[name]}`;
  const bank = (name) => `/bank/applications/${ids[name]}`;
  return [
    // Клиент
    ["client/01-demo-login", "anon", "/demo", { full: true, core: true }],
    ["client/02-home-romashka", "romashka", "/applications", { full: true, core: true }],
    ["client/03-home-ivanov", "ivanov", "/applications", { full: true }],
    [
      "client/04-new-application-choose-product",
      "romashka",
      "/applications/new",
      { full: true, core: true, prep: (p) => p.getByRole("radio", { name: /Кредит на оборудование/ }).check() },
    ],
    ["client/05-draft-empty-equipment", "romashka", `${app("draft_empty")}/edit`, { full: true }],
    ["client/06-draft-partial", "ivanov", `${app("draft_partial")}/edit`, { full: true, core: true }],
    [
      "client/07-draft-validation-errors",
      "ivanov",
      `${app("draft_partial")}/edit`,
      { full: true, prep: (p) => click(p, "Отправить заявку") },
    ],
    ["client/08-offer-full-amount", "ivanov", app("offered_full"), { full: true, core: true }],
    ["client/09-offer-alternative-amount", "romashka", app("offered_alt"), { full: true, core: true }],
    ["client/10-accepted-agreement-to-sign", "romashka", app("accepted"), { full: true, core: true }],
    ["client/11-completed-equipment", "ivanov", app("completed_equipment"), { full: true }],
    ["client/12-completed-large-amount", "romashka", app("completed_large"), { full: true }],
    ["client/13-rejected", "romashka", app("rejected_overdue"), { full: true, core: true }],
    ["client/14-declined-by-client", "ivanov", app("declined_by_client"), { full: true }],
    ["client/15-needs-info-system-request", "romashka", app("needs_info_system"), { full: true, core: true }],
    ["client/16-needs-info-officer-request", "ivanov", app("needs_info_officer"), { full: true }],
    ["client/17-after-resubmit-second-revision", "romashka", app("resubmitted"), { full: true }],
    ["client/18-processing-error-timeout", "ivanov", app("error_timeout"), { full: true, core: true }],
    ["client/19-processing-error-incomplete-data", "romashka", app("error_incomplete"), { full: true }],
    ["client/20-waiting-for-specialist", "romashka", app("pending_alt"), { full: true }],
    // Банк
    ["bank/01-queue", "officer", "/bank/applications", { full: true, core: true }],
    ["bank/02-queue-filter-needs-action-status", "officer", "/bank/applications?status=MANUAL_REVIEW", { full: true }],
    ["bank/03-queue-filter-equipment", "officer", "/bank/applications?product=EQUIPMENT", { full: true }],
    ["bank/04-queue-filter-empty", "officer", "/bank/applications?status=CHECKING", { full: true }],
    ["bank/05-dossier-alternative-amount", "officer", bank("pending_alt"), { full: true, core: true }],
    ["bank/06-dossier-full-amount", "officer", bank("pending_full"), { full: true }],
    ["bank/07-dossier-equipment-product", "officer", bank("pending_equipment"), { full: true, core: true }],
    ["bank/08-dossier-affordability-below-minimum", "officer", bank("pending_afford_below_min"), { full: true }],
    ["bank/09-dossier-overdue-reject-recommended", "officer", bank("pending_overdue"), { full: true, core: true }],
    ["bank/10-dossier-processing-error-retry", "officer", bank("error_timeout"), { full: true, core: true }],
    ["bank/11-dossier-source-incomplete", "officer", bank("error_incomplete"), { full: true }],
    ["bank/12-dossier-needs-info", "officer", bank("needs_info_officer"), { full: true }],
    ["bank/13-dossier-two-revisions", "officer", bank("resubmitted"), { full: true }],
    ["bank/14-dossier-completed-history", "officer", bank("completed_equipment"), { full: true }],
    ["bank/15-dossier-rejected", "officer", bank("rejected_overdue"), { full: true }],
    [
      "bank/16-dialog-approve-offer",
      "officer",
      bank("pending_full"),
      { core: true, prep: (p) => click(p, "Подтвердить рассчитанное предложение") },
    ],
    [
      "bank/17-dialog-request-info",
      "officer",
      bank("pending_alt"),
      {
        prep: async (p) => {
          await click(p, "Запросить уточнение");
          await p.getByLabel("Платежи по действующим кредитам в месяц").check();
          await p.getByLabel(/Сообщение клиенту/).fill("Подтвердите платежи по действующим кредитам справкой из банка.");
        },
      },
    ],
    [
      "bank/18-dialog-reject-with-reason",
      "officer",
      bank("pending_overdue"),
      {
        prep: async (p) => {
          await click(p, "Отказать с причиной");
          await p.getByLabel(/Причина/).selectOption("OVERDUE_LIMIT");
          await p.getByLabel(/Комментарий/).fill("Просрочка выше порога политики. Решение подтверждено сотрудником.");
        },
      },
    ],
    [
      "bank/19-dialog-retry-checks",
      "officer",
      bank("error_timeout"),
      { prep: (p) => click(p, "Перезапустить проверку") },
    ],
    // Состояния
    ["states/01-foreign-application-404", "ivanov", app("pending_alt"), { full: true, core: true }],
    ["states/02-wrong-role-screen", "officer", "/applications", { full: true }],
    ["states/03-page-not-found", "romashka", "/no-such-page", { full: true }],
    ["states/04-client-profile-open-on-demo", "romashka", "/demo", { full: true }],
  ];
}

async function networkStates(browser, device, dir) {
  // Состояния, которые вызываются подменой сети: подпись в README помечает это как эмуляцию.
  const ctx = await loginContext(browser, device, "romashka");
  const page = await ctx.newPage();
  await page.route("**/api/v1/applications", (route) => route.abort());
  await page.goto("/applications");
  await page.waitForSelector(".notice-error", { timeout: 15000 });
  await snap(page, dir, "states/05-network-error-with-retry", { full: false });
  await page.unroute("**/api/v1/applications");
  await page.close();

  const slow = await ctx.newPage();
  await slow.route("**/api/v1/applications", async (route) => {
    await new Promise((r) => setTimeout(r, 4000));
    await route.continue().catch(() => {});
  });
  await slow.goto("/applications", { waitUntil: "domcontentloaded" });
  await slow.waitForTimeout(700);
  fs.mkdirSync(path.join(dir, "states"), { recursive: true });
  await slow.screenshot({ path: path.join(dir, "states/06-loading-skeleton.png") });
  console.log("  shot states/06-loading-skeleton.png");
  await slow.close();

  const empty = await ctx.newPage();
  await empty.route("**/api/v1/applications", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: [], next_cursor: null }) }),
  );
  await empty.goto("/applications");
  await snap(empty, dir, "states/07-empty-applications-list", { full: true });
  await ctx.close();
}

async function runViews(browser, key) {
  const device = DEVICES[key];
  const dir = path.join(OUT, device.dir);
  console.log(`== ${device.label}`);
  const contexts = {};
  for (const who of ["anon", "romashka", "ivanov", "officer"]) contexts[who] = await loginContext(browser, device, who);
  for (const [name, who, url, opts] of viewList()) {
    if (device.tier === "core" && !opts.core) continue;
    const page = await contexts[who].newPage();
    try {
      await page.goto(url);
      await settle(page, 300);
      if (opts.prep) await opts.prep(page);
      await snap(page, dir, name, { full: Boolean(opts.full) });
    } catch (error) {
      console.log("  FAIL", name, String(error.message).split("\n")[0]);
    }
    await page.close();
  }
  for (const ctx of Object.values(contexts)) await ctx.close();
  if (device.tier === "full" || key === "android") await networkStates(browser, device, dir);
}

/* ---------- final: сценарии, меняющие данные ---------- */

async function draftConflict(browser, device, dir) {
  const romashka = await L.session("client-romashka");
  const draft = await L.createApplication(romashka, {
    product: "WORKING_CAPITAL",
    fields: { purpose: "working_capital", requested_amount: "350000.00", term_months: 12, company_form: "LLC" },
    docs: false,
    submit: false,
  });
  const ctx = await loginContext(browser, device, "romashka");
  const page = await ctx.newPage();
  await page.goto(`/applications/${draft.id}/edit`);
  await settle(page, 300);
  await page.getByLabel(/Выручка в месяц/).fill("900000");
  // «Другая вкладка» того же клиента меняет черновик: версия на сервере вырастает.
  const otherTab = await callAs(ctx);
  await otherTab("patch", `/applications/${draft.id}`, {
    data: { expected_version: draft.version, draft_fields: { monthly_operating_costs: "500000.00" } },
  });
  await click(page, "Сохранить черновик");
  await page.getByText("Черновик изменился").waitFor();
  await snap(page, dir, "states/08-draft-version-conflict-409", { full: true });
  await page.getByLabel(/Выручка в месяц/).fill("900000");
  await page.getByRole("link", { name: /Мои заявки/ }).first().click();
  await page.getByRole("dialog").waitFor();
  await snap(page, dir, "states/09-unsaved-changes-warning", { full: false });
  await ctx.close();
}

async function bankConflict(browser, device, dir) {
  const ivanov = await L.session("client-ivanov");
  const officer = await L.session("officer");
  const app = await L.createApplication(ivanov, {
    product: "WORKING_CAPITAL",
    fields: {
      purpose: "working_capital",
      requested_amount: "1300000.00",
      term_months: 18,
      company_form: "IP",
      monthly_revenue: "1500000.00",
      monthly_operating_costs: "1000000.00",
      declared_monthly_debt_payments: "100000.00",
    },
  });
  await L.waitFor(officer, app.id, ["MANUAL_REVIEW"], 30000);
  const ctx = await loginContext(browser, device, "officer");
  const page = await ctx.newPage();
  await page.goto(`/bank/applications/${app.id}`);
  await settle(page, 300);
  await click(page, "Отказать с причиной");
  await page.getByLabel(/Причина/).selectOption("RISK_POLICY_LIMIT");
  await page.getByLabel(/Комментарий/).fill("Решение по политике.");
  // «Второй сотрудник» (другая вкладка того же профиля) подтвердил предложение раньше.
  const otherTab = await callAs(ctx);
  const dossier = await otherTab("get", `/bank/applications/${app.id}`);
  await otherTab("post", `/bank/applications/${app.id}/decision`, {
    data: { expected_version: dossier.version, run_id: dossier.active_run_id, type: "APPROVE_OFFER", candidate_hash: dossier.risk_summary.candidate_hash },
    idem: true,
  });
  await page.getByRole("dialog").getByRole("button", { name: "Отказать" }).click();
  await page.getByText("Заявка изменилась, пока вы её рассматривали.").waitFor();
  await snap(page, dir, "states/10-bank-decision-conflict-409", { full: true });
  await ctx.close();
}

async function focusRing(browser, device, dir) {
  const ctx = await loginContext(browser, device, "ivanov");
  const page = await ctx.newPage();
  await page.goto(`/applications/${ids.draft_partial}/edit`);
  await settle(page, 300);
  for (let i = 0; i < 9; i++) await page.keyboard.press("Tab");
  await snap(page, dir, "states/11-keyboard-focus-visible", { full: false });
  await ctx.close();
}

/** Полный путь клиента через UI с одним переключением профилей, как на защите. */
async function tour(browser, device, dir, { who, product, spec, video, key }) {
  const label = `${device.dir} tour`;
  console.log(`== ${label}`);
  const videoDir = path.join(OUT, "video");
  const scale = device.mobile ? 2 : 1;
  const videoSize = { width: device.viewport.width * scale, height: device.viewport.height * scale };
  const ctx = await loginContext(browser, device, "anon", video ? { recordVideo: { dir: videoDir, size: videoSize } } : {});
  const page = await ctx.newPage();
  const shot = (name, opts) => snap(page, dir, `flow/${name}`, opts);
  const isEquipment = product === "EQUIPMENT";
  const companyLabel = who === "romashka" ? "ООО Ромашка" : "ИП Иванов";

  await page.goto("/demo");
  await shot("01-demo-choose-profile", { full: true });
  await page.locator(".profile-card", { hasText: companyLabel }).getByRole("button", { name: "Начать новую заявку" }).click();
  await page.waitForURL("**/applications/new");
  await page.getByRole("radio", { name: new RegExp(isEquipment ? "Кредит на оборудование" : "Оборотный кредит") }).check();
  await shot("02-choose-product");
  await click(page, "Создать черновик");
  await page.waitForURL(/\/edit$/);
  const id = page.url().split("/").at(-2);
  await shot("03-empty-draft", { full: true });
  await click(page, "Отправить заявку");
  await shot("04-validation-errors", { full: true });

  await page.getByLabel(/Сумма кредита/).fill(String(spec.amount));
  await page.getByRole("radio", { name: `${spec.term} мес.` }).check();
  await page.getByLabel(/Организационно-правовая форма/).selectOption(spec.form);
  await page.getByLabel(/Выручка в месяц/).fill(String(spec.revenue));
  await page.getByLabel(/Операционные расходы/).fill(String(spec.costs));
  await page.getByLabel(/Платежи по действующим/).fill(String(spec.debt));
  await shot("05-filled-unsaved-changes", { full: true, settleMs: 300 });
  await click(page, "Сохранить черновик");
  await page.getByText(/Сохранено на сервере в/).waitFor();
  const docFiles = isEquipment ? ["Финансовая справка", "Коммерческое предложение на оборудование"] : ["Финансовая справка"];
  const pdf = path.join(__dirname, "sample-document.pdf");
  fs.writeFileSync(pdf, "%PDF-1.4\n% synthetic demo document\n%%EOF\n");
  for (const title of docFiles) {
    await page.getByLabel(new RegExp(title)).setInputFiles(pdf);
    await page.locator(".doc-slot", { hasText: title }).getByRole("button", { name: /^Загрузить/ }).click();
    await page.locator(".doc-slot", { hasText: title }).getByText("Загружен", { exact: true }).waitFor();
  }
  await shot("06-saved-and-documents-uploaded", { full: true, settleMs: 300 });
  await click(page, "Отправить заявку");
  await shot("07-confirm-submit-dialog");
  await page.getByRole("dialog").getByRole("button", { name: "Отправить" }).click();
  await page.waitForURL(new RegExp(`/applications/${id}$`));
  await shot("08-submitted-toast-and-stepper", { settleMs: 500 });
  await page.locator(".page-header .badge", { hasText: "Заявка у специалиста" }).waitFor({ timeout: 30000 });
  await shot("09-waiting-for-specialist", { full: true });

  // Смена профиля на сотрудника
  await page.getByRole("link", { name: "Сменить профиль" }).click();
  await page.locator(".profile-card", { hasText: "Кредитный специалист" }).getByRole("button", { name: "Открыть очередь" }).click();
  await page.waitForURL("**/bank/applications");
  await shot("10-officer-queue-new-application", { full: true });
  await page.goto(`/bank/applications/${id}`);
  await shot("11-officer-dossier", { full: true });
  await click(page, "Подтвердить рассчитанное предложение");
  await shot("12-officer-approve-dialog");
  await page.getByRole("dialog").getByRole("button", { name: "Подтвердить условия" }).click();
  await page.locator(".page-header .badge", { hasText: "Предложены условия" }).waitFor();
  await shot("13-officer-approved-toast", { settleMs: 500 });

  // Обратно к клиенту
  await page.getByRole("link", { name: "Сменить профиль" }).click();
  await page.locator(".profile-card", { hasText: companyLabel }).getByRole("button", { name: "Мои заявки" }).click();
  await page.waitForURL("**/applications");
  await shot("14-client-home-new-card", { full: true });
  await page.goto(`/applications/${id}`);
  await page.getByRole("button", { name: "Принять условия" }).waitFor();
  await shot("15-client-offer", { full: true });
  await click(page, "Принять условия");
  await page.getByRole("button", { name: "Смоделировать подписание" }).waitFor();
  await shot("16-accepted-toast-and-agreement", { settleMs: 500 });
  await page.getByRole("checkbox").check();
  await shot("17-consent-checked", { full: true, settleMs: 300 });
  await click(page, "Смоделировать подписание");
  await page.getByText("Выдача смоделирована. Реальные средства не переводились.").waitFor({ timeout: 30000 });
  await shot("18-completed-simulation", { full: true });
  const recording = video ? page.video() : null;
  await ctx.close();
  if (recording) {
    await recording.saveAs(path.join(videoDir, `e01-${key}.webm`));
    await recording.delete();
  }
}

/** Состояние «в обработке»: на время съёмки останавливаем worker, затем запускаем снова. */
async function inflight(browser, deviceKeys) {
  execSync("pkill -f '[j]obs.worker' || true");
  await L.sleep(1500);
  const romashka = await L.session("client-romashka");
  const app = await L.createApplication(romashka, {
    product: "WORKING_CAPITAL",
    fields: {
      purpose: "working_capital",
      requested_amount: "850000.00",
      term_months: 12,
      company_form: "LLC",
      monthly_revenue: "1500000.00",
      monthly_operating_costs: "1000000.00",
      declared_monthly_debt_payments: "100000.00",
    },
  });
  for (const key of deviceKeys) {
    const device = DEVICES[key];
    const dir = path.join(OUT, device.dir);
    console.log(`== inflight ${device.label}`);
    const client = await loginContext(browser, device, "romashka");
    const p1 = await client.newPage();
    await p1.goto("/applications");
    await snap(p1, dir, "client/21-home-with-application-in-progress", { full: true });
    await p1.goto(`/applications/${app.id}`);
    await snap(p1, dir, "client/22-application-submitted-checking", { full: true });
    await client.close();
    const officer = await loginContext(browser, device, "officer");
    const p2 = await officer.newPage();
    await p2.goto(`/bank/applications/${app.id}`);
    await snap(p2, dir, "bank/20-dossier-checks-not-finished", { full: true });
    await officer.close();
  }
  execSync("/var/tmp/pgdev/up.sh > /dev/null 2>&1");
}

(async () => {
  const [mode, ...names] = process.argv.slice(2);
  const keys = names.includes("all") ? Object.keys(DEVICES) : names;
  const browser = await chromium.launch();
  if (mode === "views") {
    for (const key of keys) await runViews(browser, key);
  } else if (mode === "netstates") {
    for (const key of keys) await networkStates(browser, DEVICES[key], path.join(OUT, DEVICES[key].dir));
  } else if (mode === "tour" || mode === "final") {
    const tours = {
      desktop: { who: "romashka", product: "WORKING_CAPITAL", video: true, spec: { amount: 1000000, term: 12, form: "LLC", revenue: 600000, costs: 400000, debt: 100000 } },
      ipad: { who: "ivanov", product: "WORKING_CAPITAL", video: false, spec: { amount: 1500000, term: 18, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000 } },
      iphone: { who: "romashka", product: "EQUIPMENT", video: true, spec: { amount: 2400000, term: 36, form: "LLC", revenue: 2500000, costs: 1600000, debt: 100000 } },
    };
    for (const key of keys) {
      const device = DEVICES[key];
      const dir = path.join(OUT, device.dir);
      if (mode === "final" && device.tier === "full") {
        await focusRing(browser, device, dir);
        await draftConflict(browser, device, dir);
        await bankConflict(browser, device, dir);
      }
      if (tours[key]) await tour(browser, device, dir, { ...tours[key], key });
    }
    if (mode === "final") await inflight(browser, keys.filter((k) => DEVICES[k].tier === "full"));
  }
  await browser.close();
})().catch((error) => {
  console.error("CAPTURE FAIL", error);
  process.exit(1);
});
