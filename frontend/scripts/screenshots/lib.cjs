// Общие помощники для подготовки демо-данных и скриншотов. Запускается Node (CommonJS) с Playwright.
// Работает только против локального стенда с синтетическими данными (DEMO_MODE=true).
const { request } = require("playwright");
const crypto = require("node:crypto");

const API = process.env.API_URL || "http://127.0.0.1:8000/api/v1";

const key = () => crypto.randomUUID();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function session(profileId) {
  const ctx = await request.newContext();
  const res = await ctx.post(`${API}/demo/session`, { data: { profile_id: profileId } });
  if (!res.ok()) throw new Error(`demo session ${profileId}: ${res.status()}`);
  const csrf = (await res.json()).csrf_token;
  const headers = { "X-CSRF-Token": csrf };
  const call = async (method, path, { data, multipart, idem } = {}) => {
    const h = { ...headers, ...(idem ? { "Idempotency-Key": key() } : {}) };
    const r = await ctx[method](`${API}${path}`, { headers: h, data, multipart });
    const text = await r.text();
    let body = null;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      body = text;
    }
    if (!r.ok()) throw new Error(`${method.toUpperCase()} ${path} -> ${r.status()} ${text.slice(0, 300)}`);
    return body;
  };
  return { ctx, call };
}

const PDF = (title) =>
  Buffer.from(`%PDF-1.4\n% ${title}\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n`);

const DOCS = {
  WORKING_CAPITAL: [["FINANCIAL_SUMMARY", "financial-summary.pdf"]],
  EQUIPMENT: [
    ["FINANCIAL_SUMMARY", "financial-summary.pdf"],
    ["EQUIPMENT_QUOTE", "equipment-quote.pdf"],
  ],
};

/** Создаёт заявку клиента: черновик, поля, документы, при submit=true — отправляет. */
async function createApplication(client, { product, fields, submit = true, docs = true }) {
  let app = await client.call("post", "/applications", { data: { product_code: product }, idem: true });
  if (fields && Object.keys(fields).length) {
    app = await client.call("patch", `/applications/${app.id}`, {
      data: { expected_version: app.version, draft_fields: fields },
    });
  }
  let version = app.version;
  if (docs) {
    for (const [kind, name] of DOCS[product]) {
      version = (await client.call("get", `/applications/${app.id}`)).version;
      const doc = await client.call("post", `/applications/${app.id}/documents`, {
        multipart: {
          kind,
          expected_version: String(version),
          file: { name, mimeType: "application/pdf", buffer: PDF(`${kind} synthetic`) },
        },
        idem: true,
      });
      version = doc.version;
    }
  }
  if (submit) {
    version = (await client.call("get", `/applications/${app.id}`)).version;
    app = await client.call("post", `/applications/${app.id}/submit`, { data: { expected_version: version }, idem: true });
  }
  return app;
}

async function waitFor(officer, id, accept, timeoutMs = 60000) {
  const started = Date.now();
  for (;;) {
    const dossier = await officer.call("get", `/bank/applications/${id}`);
    if (accept.includes(dossier.status)) return dossier;
    if (Date.now() - started > timeoutMs) throw new Error(`timeout waiting ${id}: ${dossier.status}`);
    await sleep(400);
  }
}

const approve = async (officer, id) => {
  const d = await officer.call("get", `/bank/applications/${id}`);
  return officer.call("post", `/bank/applications/${id}/decision`, {
    data: { expected_version: d.version, run_id: d.active_run_id, type: "APPROVE_OFFER", candidate_hash: d.risk_summary.candidate_hash },
    idem: true,
  });
};

const reject = async (officer, id, reasonCode, comment) => {
  const d = await officer.call("get", `/bank/applications/${id}`);
  return officer.call("post", `/bank/applications/${id}/decision`, {
    data: { expected_version: d.version, run_id: d.active_run_id, type: "REJECT", reason_code: reasonCode, comment },
    idem: true,
  });
};

const requestInfo = async (officer, id, fields, message, documentKinds = []) => {
  const d = await officer.call("get", `/bank/applications/${id}`);
  return officer.call("post", `/bank/applications/${id}/request-info`, {
    data: { expected_version: d.version, fields, document_kinds: documentKinds, message },
    idem: true,
  });
};

const accept = async (client, id) => {
  const [app, offer] = await Promise.all([client.call("get", `/applications/${id}`), client.call("get", `/applications/${id}/offer`)]);
  return client.call("post", `/applications/${id}/offer/accept`, { data: { expected_version: app.version, offer_id: offer.id }, idem: true });
};

const decline = async (client, id) => {
  const [app, offer] = await Promise.all([client.call("get", `/applications/${id}`), client.call("get", `/applications/${id}/offer`)]);
  return client.call("post", `/applications/${id}/offer/decline`, { data: { expected_version: app.version, offer_id: offer.id }, idem: true });
};

const sign = async (client, id) => {
  const [app, agreement] = await Promise.all([client.call("get", `/applications/${id}`), client.call("get", `/applications/${id}/agreement`)]);
  return client.call("post", `/applications/${id}/agreement/simulate-sign`, {
    data: { expected_version: app.version, agreement_id: agreement.id, content_hash: agreement.content_hash, consent: true },
    idem: true,
  });
};

module.exports = { API, key, sleep, session, createApplication, waitFor, approve, reject, requestInfo, accept, decline, sign };
