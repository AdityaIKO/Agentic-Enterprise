import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import type { Store, Proposal, AuditEntry } from "./types";
import { seedStore } from "./seed";

// File-backed JSON store: simple, deployable on any host with a persistent volume (Docker, VPS, Railway, Fly).
// For serverless (Vercel) swap load()/save() for a Postgres/KV client; the agents themselves are pure functions.
const FILE = process.env.DATA_FILE || path.join(process.cwd(), "data", "store.json");
let cache: Store | null = null;

export function load(): Store {
  if (cache) return cache;
  try {
    cache = JSON.parse(fs.readFileSync(FILE, "utf8")) as Store;
  } catch {
    cache = seedStore();
    save(cache);
  }
  return cache!;
}

export function save(s: Store) {
  cache = s;
  try {
    fs.mkdirSync(path.dirname(FILE), { recursive: true });
    fs.writeFileSync(FILE, JSON.stringify(s, null, 1));
  } catch {
    /* read-only filesystem: keep in memory only */
  }
}

export function reset(): Store {
  cache = seedStore();
  save(cache);
  return cache;
}

export function uid(prefix: string) {
  return `${prefix}-${crypto.randomBytes(3).toString("hex")}`;
}

/** Hash-chained audit log: every agent action and human decision is recorded and tamper-evident. */
export function audit(s: Store, actor: string, event: string, detail: string) {
  const prev = s.audit.length ? s.audit[s.audit.length - 1].hash : "0".repeat(64);
  const e: Omit<AuditEntry, "hash"> = { t: new Date().toISOString(), actor, event, detail, prev };
  const hash = crypto.createHash("sha256").update(JSON.stringify(e)).digest("hex");
  s.audit.push({ ...e, hash });
}

export function auditIntact(s: Store): boolean {
  let prev = "0".repeat(64);
  for (const a of s.audit) {
    const { hash, ...rest } = a;
    if (rest.prev !== prev) return false;
    if (crypto.createHash("sha256").update(JSON.stringify(rest)).digest("hex") !== hash) return false;
    prev = hash;
  }
  return true;
}

/** Agents never change business data directly: they file a proposal that a human approves (level 2). */
export function propose(s: Store, p: Omit<Proposal, "id" | "status" | "createdAt">): Proposal {
  const prop: Proposal = { ...p, id: uid("PR"), status: "pending", createdAt: new Date().toISOString() };
  s.proposals.unshift(prop);
  audit(s, p.agent, "proposal.created", `${prop.id}: ${p.title}`);
  return prop;
}
