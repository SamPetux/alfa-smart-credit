// Наполняет чистый локальный стенд разными заявками через настоящий API (клиенты и сотрудник
// действуют так же, как в UI). Результат: seed.json с id заявок по именам сценариев.
const fs = require("node:fs");
const path = require("node:path");
const L = require("./lib.cjs");

const OUT = process.env.SEED_OUT || path.join(__dirname, "seed.json");
const WC = "WORKING_CAPITAL";
const EQ = "EQUIPMENT";

const money = (n) => `${n}.00`;
const fields = (o) => ({
  purpose: o.product === EQ ? "equipment" : "working_capital",
  requested_amount: money(o.amount),
  term_months: o.term,
  company_form: o.form,
  monthly_revenue: money(o.revenue),
  monthly_operating_costs: money(o.costs),
  declared_monthly_debt_payments: money(o.debt),
  ...(o.scenario ? { demo_scenario: o.scenario } : {}),
});

(async () => {
  const romashka = await L.session("client-romashka");
  const ivanov = await L.session("client-ivanov");
  const officer = await L.session("officer");
  const ids = {};
  const submit = async (name, who, spec) => {
    const app = await L.createApplication(who, { product: spec.product, fields: fields(spec), docs: true, submit: true });
    ids[name] = app.id;
    console.log("submitted", name, app.id);
  };

  // Спецификации: клиент, продукт, сумма, срок, выручка/расходы/долги в месяц.
  // Долг 100 000 совпадает с данными бюро-симулятора; другое значение даёт уточнение DEBT_DATA_MISMATCH.
  const S = {
    pending_alt: [romashka, { product: WC, amount: 1000000, term: 12, form: "LLC", revenue: 600000, costs: 400000, debt: 100000 }],
    pending_full: [ivanov, { product: WC, amount: 1500000, term: 18, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000 }],
    pending_equipment: [romashka, { product: EQ, amount: 2400000, term: 36, form: "LLC", revenue: 2500000, costs: 1600000, debt: 100000 }],
    pending_afford_below_min: [ivanov, { product: WC, amount: 100000, term: 6, form: "IP", revenue: 300000, costs: 260000, debt: 100000 }],
    pending_overdue: [ivanov, { product: WC, amount: 600000, term: 12, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000, scenario: "g04" }],
    offered_full: [ivanov, { product: WC, amount: 900000, term: 12, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000 }],
    offered_alt: [romashka, { product: WC, amount: 1200000, term: 12, form: "LLC", revenue: 600000, costs: 400000, debt: 100000 }],
    accepted: [romashka, { product: WC, amount: 500000, term: 12, form: "LLC", revenue: 1500000, costs: 1000000, debt: 100000 }],
    completed_equipment: [ivanov, { product: EQ, amount: 1800000, term: 24, form: "IP", revenue: 1800000, costs: 1200000, debt: 100000 }],
    completed_large: [romashka, { product: WC, amount: 3000000, term: 24, form: "LLC", revenue: 4000000, costs: 2500000, debt: 100000 }],
    declined_by_client: [ivanov, { product: EQ, amount: 1200000, term: 24, form: "IP", revenue: 1800000, costs: 1200000, debt: 100000 }],
    rejected_overdue: [romashka, { product: WC, amount: 800000, term: 12, form: "LLC", revenue: 1500000, costs: 1000000, debt: 100000, scenario: "g04" }],
    needs_info_system: [romashka, { product: WC, amount: 700000, term: 12, form: "LLC", revenue: 600000, costs: 400000, debt: 0 }],
    needs_info_officer: [ivanov, { product: WC, amount: 400000, term: 6, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000 }],
    resubmitted: [romashka, { product: WC, amount: 650000, term: 12, form: "LLC", revenue: 600000, costs: 400000, debt: 0 }],
    error_timeout: [ivanov, { product: WC, amount: 1000000, term: 12, form: "IP", revenue: 1500000, costs: 1000000, debt: 100000, scenario: "timeout" }],
    error_incomplete: [romashka, { product: WC, amount: 600000, term: 12, form: "LLC", revenue: 1500000, costs: 1000000, debt: 100000, scenario: "incomplete" }],
  };
  for (const [name, [who, spec]] of Object.entries(S)) await submit(name, who, spec);

  // Черновики без отправки.
  const emptyDraft = await L.createApplication(romashka, { product: EQ, fields: null, docs: false, submit: false });
  ids.draft_empty = emptyDraft.id;
  const partial = await L.createApplication(ivanov, {
    product: WC,
    fields: { purpose: "working_capital", requested_amount: money(450000), term_months: 12, company_form: "IP" },
    docs: false,
    submit: false,
  });
  ids.draft_partial = partial.id;

  const REVIEW = ["MANUAL_REVIEW"];
  const settled = ["MANUAL_REVIEW", "NEEDS_INFO", "PROCESSING_ERROR"];
  for (const name of Object.keys(S)) {
    const d = await L.waitFor(officer, ids[name], settled, 90000);
    console.log("settled", name.padEnd(26), d.status.padEnd(16), d.risk_summary?.recommendation || "-", (d.risk_summary?.reasons || []).join(","));
  }

  // Решения сотрудника и действия клиентов.
  for (const name of ["offered_full", "offered_alt", "accepted", "completed_equipment", "completed_large", "declined_by_client"]) {
    await L.approve(officer, ids[name]);
  }
  await L.reject(officer, ids.rejected_overdue, "OVERDUE_LIMIT", "Просрочка 35 дней выше порога демонстрационной политики.");
  await L.requestInfo(
    officer,
    ids.needs_info_officer,
    ["monthly_operating_costs"],
    "Уточните операционные расходы за последний квартал: в заявке они выглядят заниженными.",
  );
  await L.accept(romashka, ids.accepted);
  await L.accept(ivanov, ids.completed_equipment);
  await L.sign(ivanov, ids.completed_equipment);
  await L.accept(romashka, ids.completed_large);
  await L.sign(romashka, ids.completed_large);
  await L.decline(ivanov, ids.declined_by_client);

  // Клиент отвечает на системный запрос уточнения: новая ревизия и повторная проверка.
  const info = await romashka.call("get", `/applications/${ids.resubmitted}/info-request`);
  let app = await romashka.call("get", `/applications/${ids.resubmitted}`);
  app = await romashka.call("patch", `/applications/${ids.resubmitted}`, {
    data: { expected_version: app.version, draft_fields: { declared_monthly_debt_payments: money(100000) } },
  });
  await romashka.call("post", `/applications/${ids.resubmitted}/resubmit`, {
    data: { expected_version: app.version, info_request_id: info.id },
    idem: true,
  });

  await L.waitFor(officer, ids.resubmitted, REVIEW, 60000);
  for (const name of ["completed_equipment", "completed_large"]) await L.waitFor(officer, ids[name], ["COMPLETED"], 60000);

  const summary = {};
  for (const [name, id] of Object.entries(ids)) {
    const d = await officer.call("get", `/bank/applications/${id}`);
    summary[name] = d.status;
  }
  fs.writeFileSync(OUT, JSON.stringify({ ids, summary }, null, 2));
  console.table(summary);
  console.log("written", OUT);
})().catch((e) => {
  console.error("SEED FAIL", e.message);
  process.exit(1);
});
