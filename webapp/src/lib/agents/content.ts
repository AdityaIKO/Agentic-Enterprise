import type { Category, Product, Settings } from "../types";
import { claimsCheck } from "./marketing";

/** Content studio agent: marketing images, short videos and captions for social media, in several languages, laid out for each platform.
 *  Pure functions. Every sentence comes from fixed, verified-claim templates (no invented claims); the owner approves before anything is used.
 *  Translations are drafts: have a native speaker check them before publishing. */

export type PlatformId = "ig-feed" | "ig-story" | "ig-reel" | "fb-feed" | "fb-story" | "yt-thumb" | "yt-short" | "yt-video" | "linkedin" | "tiktok" | "x-post" | "wa-status";
export interface Platform {
  id: PlatformId; name: string; kind: "image" | "video"; w: number; h: number; ratio: string;
  safeTop: number; safeBottom: number;          // px reserved for the app's own interface (story bars, reply box, reel buttons)
  maxCaption: number; maxHashtags: number;      // 0 caption = text lives on the creative only
  secMin?: number; secMax?: number; note: string;
}

export const PLATFORMS: Platform[] = [
  { id: "ig-feed", name: "Instagram feed post", kind: "image", w: 1080, h: 1350, ratio: "4:5", safeTop: 60, safeBottom: 60, maxCaption: 2200, maxHashtags: 10, note: "Portrait 4:5 uses the most feed space." },
  { id: "ig-story", name: "Instagram story", kind: "image", w: 1080, h: 1920, ratio: "9:16", safeTop: 250, safeBottom: 340, maxCaption: 0, maxHashtags: 0, note: "Keep text out of the top and bottom bars." },
  { id: "ig-reel", name: "Instagram reel", kind: "video", w: 1080, h: 1920, ratio: "9:16", safeTop: 220, safeBottom: 420, maxCaption: 2200, maxHashtags: 5, secMin: 8, secMax: 30, note: "Vertical, hook in the first 2 seconds." },
  { id: "fb-feed", name: "Facebook feed post", kind: "image", w: 1200, h: 630, ratio: "1.91:1", safeTop: 40, safeBottom: 40, maxCaption: 500, maxHashtags: 3, note: "Landscape link-style image." },
  { id: "fb-story", name: "Facebook story", kind: "image", w: 1080, h: 1920, ratio: "9:16", safeTop: 250, safeBottom: 340, maxCaption: 0, maxHashtags: 0, note: "Same safe zones as Instagram stories." },
  { id: "yt-thumb", name: "YouTube thumbnail", kind: "image", w: 1280, h: 720, ratio: "16:9", safeTop: 40, safeBottom: 90, maxCaption: 100, maxHashtags: 3, note: "Title up to 100 characters; the duration badge covers the lower right." },
  { id: "yt-short", name: "YouTube Short", kind: "video", w: 1080, h: 1920, ratio: "9:16", safeTop: 200, safeBottom: 420, maxCaption: 100, maxHashtags: 3, secMin: 8, secMax: 60, note: "Vertical, up to 60 seconds." },
  { id: "yt-video", name: "YouTube video", kind: "video", w: 1920, h: 1080, ratio: "16:9", safeTop: 60, safeBottom: 120, maxCaption: 100, maxHashtags: 3, secMin: 20, secMax: 90, note: "Landscape 16:9, 1080p." },
  { id: "linkedin", name: "LinkedIn post", kind: "image", w: 1200, h: 627, ratio: "1.91:1", safeTop: 40, safeBottom: 40, maxCaption: 1300, maxHashtags: 5, note: "Landscape; B2B tone." },
  { id: "tiktok", name: "TikTok video", kind: "video", w: 1080, h: 1920, ratio: "9:16", safeTop: 150, safeBottom: 480, maxCaption: 2200, maxHashtags: 5, secMin: 9, secMax: 45, note: "Vertical; the right edge and bottom are covered by buttons and caption." },
  { id: "x-post", name: "X post", kind: "image", w: 1600, h: 900, ratio: "16:9", safeTop: 40, safeBottom: 40, maxCaption: 280, maxHashtags: 2, note: "280 characters." },
  { id: "wa-status", name: "WhatsApp status", kind: "image", w: 1080, h: 1920, ratio: "9:16", safeTop: 200, safeBottom: 300, maxCaption: 0, maxHashtags: 0, note: "Vertical status image." },
];
export const platformById = (id: PlatformId) => PLATFORMS.find((p) => p.id === id)!;

export type LangId = "en" | "id" | "ar" | "tr" | "de" | "nl" | "ko" | "ja";
export const LANGS: { id: LangId; name: string; rtl?: boolean; markets: string }[] = [
  { id: "en", name: "English", markets: "all" }, { id: "id", name: "Bahasa Indonesia", markets: "Indonesia" }, { id: "ar", name: "العربية (Arabic)", rtl: true, markets: "Saudi Arabia, UAE" },
  { id: "tr", name: "Türkçe", markets: "Turkey" }, { id: "de", name: "Deutsch", markets: "Germany" }, { id: "nl", name: "Nederlands", markets: "Netherlands" },
  { id: "ko", name: "한국어", markets: "South Korea" }, { id: "ja", name: "日本語", markets: "Japan" },
];

interface Pack {
  type: Record<Category, string>; tail: string; verified: string; cta: string; ash: string; burn: string; upTo: string; grade: string; chips: Record<Category, string>; hook: string; why: string; shipping: string; tags: string[];
}
const PACKS: Record<LangId, Pack> = {
  en: { type: { coconut: "Coconut shisha charcoal", sawdust: "Sawdust charcoal", hardwood: "Hardwood lump charcoal" }, tail: "direct from Indonesia", verified: "Lab-verified batches · FOB Central Java · from 1 full container", cta: "Request a quote", ash: "Ash", burn: "Burn", upTo: "up to", grade: "Grade",
    chips: { coconut: "Low ash · long burn", sawdust: "Pressed sawdust · even burn", hardwood: "Hardwood lump · long burn" }, hook: "Sourcing charcoal?", why: "Why KrakaCoal", shipping: "FOB Central Java, full-container supply", tags: ["charcoal", "shisha", "hookah", "bbq", "indonesia", "export"] },
  id: { type: { coconut: "Arang shisha batok kelapa", sawdust: "Arang serbuk gergaji", hardwood: "Arang kayu keras" }, tail: "langsung dari Indonesia", verified: "Setiap batch diuji lab · FOB Jawa Tengah · mulai 1 kontainer penuh", cta: "Minta penawaran", ash: "Abu", burn: "Bakar", upTo: "hingga", grade: "Grade",
    chips: { coconut: "Abu rendah · bakar lama", sawdust: "Serbuk gergaji dipres · bakar merata", hardwood: "Arang kayu keras · bakar lama" }, hook: "Cari pemasok arang?", why: "Mengapa KrakaCoal", shipping: "FOB Jawa Tengah, pasokan per kontainer penuh", tags: ["arang", "shisha", "hookah", "bbq", "indonesia", "ekspor"] },
  ar: { type: { coconut: "فحم الشيشة من قشور جوز الهند", sawdust: "فحم نشارة الخشب", hardwood: "فحم الخشب الصلب" }, tail: "مباشرة من إندونيسيا", verified: "كل دفعة مفحوصة مخبريًا · تسليم FOB جاوة الوسطى · من حاوية كاملة واحدة", cta: "اطلب عرض سعر", ash: "الرماد", burn: "مدة الاحتراق", upTo: "حتى", grade: "الدرجة",
    chips: { coconut: "رماد قليل · احتراق طويل", sawdust: "نشارة مضغوطة · احتراق منتظم", hardwood: "خشب صلب · احتراق طويل" }, hook: "تبحث عن مورّد فحم؟", why: "لماذا كراكا كول", shipping: "تسليم FOB جاوة الوسطى، توريد حاويات كاملة", tags: ["فحم_شيشة", "shisha", "hookah", "فحم", "اندونيسيا", "تصدير"] },
  tr: { type: { coconut: "Hindistan cevizi kabuğu nargile kömürü", sawdust: "Talaş kömürü", hardwood: "Sert odun kömürü" }, tail: "doğrudan Endonezya'dan", verified: "Laboratuvarda test edilmiş partiler · FOB Orta Cava · 1 tam konteynerden başlayarak", cta: "Teklif isteyin", ash: "Kül", burn: "Yanma", upTo: "en fazla", grade: "Sınıf",
    chips: { coconut: "Düşük kül · uzun yanma", sawdust: "Preslenmiş talaş · düzenli yanma", hardwood: "Sert odun · uzun yanma" }, hook: "Kömür mü arıyorsunuz?", why: "Neden KrakaCoal", shipping: "FOB Orta Cava, tam konteyner tedarik", tags: ["kömür", "nargile", "shisha", "mangal", "endonezya", "ihracat"] },
  de: { type: { coconut: "Kokosnussschalen-Shisha-Kohle", sawdust: "Sägemehl-Kohle", hardwood: "Hartholzkohle (Stücke)" }, tail: "direkt aus Indonesien", verified: "Laborgeprüfte Chargen · FOB Zentraljava · ab 1 vollen Container", cta: "Angebot anfordern", ash: "Asche", burn: "Brenndauer", upTo: "bis zu", grade: "Güteklasse",
    chips: { coconut: "Wenig Asche · lange Brenndauer", sawdust: "Gepresstes Sägemehl · gleichmäßiger Abbrand", hardwood: "Hartholz · lange Brenndauer" }, hook: "Sie suchen Holzkohle?", why: "Warum KrakaCoal", shipping: "FOB Zentraljava, Lieferung ab vollem Container", tags: ["Holzkohle", "Shisha", "Hookah", "Grillen", "Indonesien", "Export"] },
  nl: { type: { coconut: "Kokosschaal-shishakool", sawdust: "Zaagselkool", hardwood: "Hardhoutskool" }, tail: "rechtstreeks uit Indonesië", verified: "Laboratoriumgetest partijen · FOB Centraal-Java · vanaf 1 volle container", cta: "Offerte aanvragen", ash: "As", burn: "Brandduur", upTo: "tot", grade: "Klasse",
    chips: { coconut: "Weinig as · lange brandduur", sawdust: "Geperst zaagsel · gelijkmatig branden", hardwood: "Hardhout · lange brandduur" }, hook: "Houtskool inkopen?", why: "Waarom KrakaCoal", shipping: "FOB Centraal-Java, levering per volle container", tags: ["houtskool", "shisha", "hookah", "bbq", "indonesie", "export"] },
  ko: { type: { coconut: "코코넛 껍질 시샤 숯", sawdust: "톱밥 숯", hardwood: "경목 덩어리 숯" }, tail: "인도네시아 직송", verified: "배치별 실험실 검증 · FOB 중부 자바 · 컨테이너 1대부터", cta: "견적 요청", ash: "회분", burn: "연소시간", upTo: "최대", grade: "등급",
    chips: { coconut: "낮은 회분 · 오래 타는 숯", sawdust: "압축 톱밥 · 고른 연소", hardwood: "경목 · 오래 타는 숯" }, hook: "숯을 찾으세요?", why: "KrakaCoal을 선택하는 이유", shipping: "FOB 중부 자바, 컨테이너 단위 공급", tags: ["숯", "시샤", "후카", "바베큐", "인도네시아", "수출"] },
  ja: { type: { coconut: "ココナッツ殻シーシャ炭", sawdust: "おがくず炭", hardwood: "硬木の塊炭" }, tail: "インドネシアから直送", verified: "ロットごとに検査済み · FOB 中部ジャワ · 1コンテナから", cta: "見積依頼", ash: "灰分", burn: "燃焼時間", upTo: "最大", grade: "等級",
    chips: { coconut: "低灰分 · 長時間燃焼", sawdust: "圧縮おがくず · 均一な燃焼", hardwood: "硬木 · 長時間燃焼" }, hook: "炭をお探しですか?", why: "KrakaCoalが選ばれる理由", shipping: "FOB 中部ジャワ、コンテナ単位で供給", tags: ["炭", "シーシャ", "水タバコ", "BBQ", "インドネシア", "輸出"] },
};
export const pack = (l: LangId) => PACKS[l];
export const SITE = "krakacoal.com";

/** Localised one-line spec from the stored product spec text (numbers are language-neutral). */
export function specLine(p: Product, lang: LangId): string {
  const k = PACKS[lang];
  let m = p.spec.match(/Ash\s*([\d.]+\s*[-–]\s*[\d.]+|[\d.]+)\s*%.*?burn\s*([\d.]+)\s*h/i);
  if (m) return `${k.ash} ${m[1].replace(/\s/g, "")}% · ${k.burn} ${m[2]} h`;
  m = p.spec.match(/(\d+)\s*[-–]\s*(\d+)\s*cm.*?([\d,]+)\s*[-–]\s*([\d,]+)\s*kcal\/kg.*?(\d+)\s*[-–]\s*(\d+)\s*h/i);
  if (m) return `${m[1]}-${m[2]} cm · ${m[3]}-${m[4]} kcal/kg · ${k.burn} ${m[5]}-${m[6]} h`;
  m = p.spec.match(/Up to\s*(\d+)\s*cm/i);
  if (m) return `${k.upTo} ${m[1]} cm · ${k.grade} ${p.name.split("Grade ").pop()}`;
  m = p.spec.match(/(\d+)\s*cm\s*pieces.*?([\d,]+)\s*[-–]\s*([\d,]+)\s*kcal\/kg.*?(\d+)\s*[-–]\s*(\d+)\s*h/i);
  if (m) return `${m[1]} cm · ${m[2]}-${m[3]} kcal/kg · ${k.burn} ${m[4]}-${m[5]} h`;
  return p.spec;
}

export function headline(p: Product, lang: LangId): string {
  const k = PACKS[lang]; const t = k.type[p.category];
  return `${t} ${k.tail}`;
}

/** Caption for one platform and language. Built only from verified-claim templates; trimmed to the platform's limit. */
export function caption(p: Product, lang: LangId, plat: Platform): string {
  const k = PACKS[lang];
  const tags = k.tags.slice(0, plat.maxHashtags).map((x) => "#" + x.replace(/\s/g, "")).join(" ");
  const lines = [headline(p, lang), specLine(p, lang), k.verified, `${k.cta}: ${SITE}`];
  let text = plat.maxCaption === 0 ? "" : lines.join("\n") + (tags ? "\n\n" + tags : "");
  if (plat.id === "x-post") text = `${headline(p, lang)} · ${specLine(p, lang)} · ${k.cta}: ${SITE} ${tags}`;
  if (plat.id === "yt-thumb" || plat.id === "yt-short" || plat.id === "yt-video") text = `${headline(p, lang)} | ${k.cta}`;
  if (text.length > plat.maxCaption && plat.maxCaption > 0) text = text.slice(0, plat.maxCaption - 1).trimEnd() + "…";
  return text;
}

export function captionCheck(text: string, s: Settings) { return claimsCheck(text, s); }

// ------------------------------------------------------------------ layout and SVG creative
const isCjk = (c: string) => /[　-ヿ㐀-鿿가-힯]/.test(c);
/** Rough text width in px (Latin 0.55 em, CJK 1.0 em, Arabic 0.5 em). */
export function textWidth(t: string, size: number): number { let w = 0; for (const c of t) w += (isCjk(c) ? 1.0 : /[؀-ۿ]/.test(c) ? 0.5 : 0.55) * size; return w; }
export function wrap(t: string, size: number, maxW: number): string[] {
  const words = t.split(/(\s+)/).filter((x) => x.length); const lines: string[] = []; let cur = "";
  const hasSpaces = /\s/.test(t);
  const toks = hasSpaces ? words : Array.from(t);
  for (const w of toks) {
    const trial = cur + w;
    if (textWidth(trial.trim(), size) <= maxW || !cur) cur = trial; else { lines.push(cur.trim()); cur = w.trimStart(); }
  }
  if (cur.trim()) lines.push(cur.trim());
  return lines;
}
const esc = (t: string) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export interface Box { x: number; y: number; w: number; h: number; role: string }
export interface Creative { svg: string; boxes: Box[]; w: number; h: number }

const PAL: Record<Category, { a: string; b: string; ember: string }> = {
  coconut: { a: "#1b130e", b: "#3a2314", ember: "#ff8a1f" }, sawdust: { a: "#14181d", b: "#27303b", ember: "#ffb02e" }, hardwood: { a: "#160f0f", b: "#3a1d17", ember: "#ff5a36" },
};

function coals(cat: Category, x: number, y: number, size: number, ember: string): string {
  // vector illustration: a pile of charcoal pieces with an ember glow
  const out: string[] = [`<defs><radialGradient id="glow" cx="50%" cy="60%" r="60%"><stop offset="0" stop-color="${ember}" stop-opacity="0.55"/><stop offset="1" stop-color="${ember}" stop-opacity="0"/></radialGradient>` +
    `<linearGradient id="coal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4b4b4f"/><stop offset="0.5" stop-color="#1d1d20"/><stop offset="1" stop-color="#0b0b0c"/></linearGradient></defs>`];
  out.push(`<ellipse cx="${x + size / 2}" cy="${y + size * 0.62}" rx="${size * 0.62}" ry="${size * 0.46}" fill="url(#glow)"/>`);
  const n = cat === "hardwood" ? 7 : 9; const u = size / 5;
  for (let i = 0; i < n; i++) {
    const row = i < 3 ? 2 : i < 6 ? 1 : 0; const col = i < 3 ? i : i < 6 ? i - 3 : i - 6;
    const cx = x + size * 0.12 + col * u * 1.45 + (row % 2) * u * 0.7; const cy = y + size * 0.38 + row * u * 1.05 - (i % 2) * u * 0.1; const s = u * (1.25 + (i % 3) * 0.12); const r = (i * 17) % 14 - 7;
    if (cat === "coconut") out.push(`<g transform="rotate(${r} ${cx + s / 2} ${cy + s / 2})"><rect x="${cx}" y="${cy}" width="${s}" height="${s}" rx="${s * 0.06}" fill="url(#coal)" stroke="#6a6a70" stroke-width="2"/><path d="M${cx + 4} ${cy + 4} L${cx + s - 4} ${cy + 4}" stroke="#8a8a90" stroke-width="3" opacity="0.5"/><rect x="${cx + s * 0.3}" y="${cy + s * 0.3}" width="${s * 0.4}" height="${s * 0.4}" fill="${ember}" opacity="0.18"/></g>`);
    else if (cat === "sawdust") out.push(`<g transform="rotate(${r} ${cx + s / 2} ${cy + s / 2})"><polygon points="${hex(cx + s / 2, cy + s / 2, s * 0.55)}" fill="url(#coal)" stroke="#6a6a70" stroke-width="2"/><circle cx="${cx + s / 2}" cy="${cy + s / 2}" r="${s * 0.12}" fill="#0b0b0c" stroke="${ember}" stroke-opacity="0.5" stroke-width="2"/></g>`);
    else out.push(`<polygon points="${cx},${cy + s * 0.5} ${cx + s * 0.35},${cy} ${cx + s * 0.9},${cy + s * 0.15} ${cx + s},${cy + s * 0.7} ${cx + s * 0.5},${cy + s}" transform="rotate(${r * 2} ${cx + s / 2} ${cy + s / 2})" fill="url(#coal)" stroke="#6a6a70" stroke-width="2"/>`);
  }
  return out.join("");
}
function hex(cx: number, cy: number, r: number): string { return [0, 1, 2, 3, 4, 5].map((i) => `${(cx + r * Math.cos(Math.PI / 3 * i)).toFixed(1)},${(cy + r * Math.sin(Math.PI / 3 * i)).toFixed(1)}`).join(" "); }

export type Scene = "hook" | "product" | "why" | "cta" | "poster";

/** One creative (SVG) for a platform and language. Layout adapts to the shape (portrait, landscape, square), keeps text inside the safe zones and mirrors for right-to-left languages. */
export function creative(p: Product, lang: LangId, plat: Platform, scene: Scene = "poster"): Creative {
  const k = PACKS[lang]; const rtl = !!LANGS.find((l) => l.id === lang)?.rtl; const pal = PAL[p.category];
  const W = plat.w, H = plat.h; const portrait = H > W * 1.2, land = W > H * 1.3;
  const top = plat.safeTop, bot = H - plat.safeBottom; const pad = Math.round(Math.min(W, H) * 0.07);
  const anchor = rtl ? "end" : "start"; const tx = rtl ? W - pad : pad; const tw = (land ? W * 0.55 : W) - 2 * pad;
  const boxes: Box[] = []; const parts: string[] = [];
  const font = `font-family="Noto Sans, Noto Sans Arabic, Noto Sans CJK JP, Noto Sans KR, Arial, sans-serif"`;
  const dir = rtl ? ` direction="rtl"` : "";
  parts.push(`<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${pal.a}"/><stop offset="1" stop-color="${pal.b}"/></linearGradient></defs><rect width="${W}" height="${H}" fill="url(#bg)"/>`);
  for (let i = 0; i < 14; i++) parts.push(`<polygon points="${hex((i * 337) % W, (i * 211) % H, 40 + (i % 4) * 22)}" fill="${pal.ember}" opacity="0.05"/>`);
  // product illustration
  const art = portrait ? Math.min(W * 0.78, (bot - top) * 0.34) : land ? Math.min(H * 0.72, W * 0.34) : W * 0.46;
  const ax = land ? (rtl ? pad : W - pad - art) : (W - art) / 2; const ay = land ? (H - art) / 2 : portrait ? bot - art - (bot - top) * 0.2 : H - pad - art - 40;
  parts.push(coals(p.category, ax, ay, art, pal.ember));
  boxes.push({ x: ax, y: ay, w: art, h: art, role: "art" });
  // text blocks
  let y = land ? Math.max(top, (H - H * 0.62) / 2) : top + (portrait ? (bot - top) * 0.03 : 0);
  const fsH = Math.round(Math.min(W * (land ? 0.062 : 0.085), H * 0.07)); const fsS = Math.round(fsH * 0.42); const fsC = Math.round(fsH * 0.5);
  const headText = scene === "hook" ? k.hook : scene === "why" ? k.why : headline(p, lang);
  const hl = wrap(headText, fsH, tw).slice(0, 3);
  parts.push(`<rect x="${tx - (rtl ? 120 : 0)}" y="${y - fsS * 1.6}" width="120" height="8" fill="${pal.ember}"/>`);
  hl.forEach((l, i) => parts.push(`<text x="${tx}" y="${y + fsH * (i + 0.85)}" font-size="${fsH}" font-weight="800" fill="#ffffff" text-anchor="${anchor}"${dir} ${font}>${esc(l)}</text>`));
  boxes.push({ x: land ? pad : pad, y, w: tw, h: fsH * 1.1 * hl.length, role: "headline" }); y += fsH * 1.15 * hl.length + fsS * 0.6;
  const sub = scene === "cta" ? `${k.shipping}` : specLine(p, lang);
  wrap(sub, fsS * 1.25, tw).slice(0, 2).forEach((l, i) => { parts.push(`<text x="${tx}" y="${y + fsS * 1.2 * (i + 1)}" font-size="${Math.round(fsS * 1.25)}" font-weight="600" fill="${pal.ember}" text-anchor="${anchor}"${dir} ${font}>${esc(l)}</text>`); });
  boxes.push({ x: pad, y, w: tw, h: fsS * 3, role: "spec" }); y += fsS * 3.2;
  const chips = scene === "poster" || scene === "product" ? [k.chips[p.category], k.verified.split(" · ").slice(0, 2).join(" · ")] : [k.verified.split(" · ").slice(0, 2).join(" · ")];
  chips.forEach((c) => { wrap(c, fsS, tw).slice(0, 2).forEach((l) => { parts.push(`<text x="${tx}" y="${y + fsS}" font-size="${fsS}" fill="#e8e0d8" text-anchor="${anchor}"${dir} ${font}>${esc(l)}</text>`); y += fsS * 1.3; }); y += fsS * 0.4; });
  boxes.push({ x: pad, y: y - fsS * 2, w: tw, h: fsS * 2, role: "chips" });
  // CTA button + site, anchored low but inside the safe zone
  const ctaW = Math.min(tw, textWidth(k.cta, fsC) + fsC * 2.4); const ctaH = fsC * 2.1; const ctaY = Math.min(bot - ctaH - fsS * 2.2, Math.max(y + fsS, land ? H * 0.74 : bot - ctaH - fsS * 2.4));
  const ctaX = rtl ? W - pad - ctaW : pad;
  parts.push(`<rect x="${ctaX}" y="${ctaY}" width="${ctaW}" height="${ctaH}" rx="${ctaH / 2}" fill="${pal.ember}"/><text x="${ctaX + ctaW / 2}" y="${ctaY + ctaH * 0.66}" font-size="${fsC}" font-weight="800" fill="#1a1109" text-anchor="middle"${dir} ${font}>${esc(k.cta)}</text>`);
  boxes.push({ x: ctaX, y: ctaY, w: ctaW, h: ctaH, role: "cta" });
  const siteY = ctaY + ctaH + fsS * 1.5;
  parts.push(`<text x="${tx}" y="${siteY}" font-size="${fsS}" font-weight="700" fill="#ffffff" opacity="0.85" text-anchor="${anchor}" ${font}>KrakaCoal · ${SITE}</text>`);
  boxes.push({ x: pad, y: siteY - fsS, w: tw, h: fsS * 1.4, role: "site" });
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"${rtl ? ' direction="rtl"' : ""}>${parts.join("")}</svg>`;
  return { svg, boxes, w: W, h: H };
}

// ------------------------------------------------------------------ video storyboard
export interface SceneSpec { scene: Scene; t0: number; dur: number; text: string; voice: string; visual: string }
export function storyboard(p: Product, lang: LangId, plat: Platform, seconds?: number): SceneSpec[] {
  if (plat.kind !== "video") return [];
  const k = PACKS[lang]; const total = Math.min(plat.secMax!, Math.max(plat.secMin!, seconds ?? (plat.id === "yt-video" ? 30 : 15)));
  const plan: [Scene, number, string, string][] = [
    ["hook", 0.2, k.hook, "Opening hook, ember glow on the charcoal pile"], ["product", 0.3, headline(p, lang), "Product with the spec line"],
    ["why", 0.3, `${k.why}: ${k.verified.split(" · ")[0]}`, "Verified batches and the FOB / full-container terms"], ["cta", 0.2, `${k.cta}: ${SITE}`, "Call to action and website"],
  ];
  let t = 0; const out: SceneSpec[] = [];
  plan.forEach(([sc, share, text, visual], i) => { const d = i === plan.length - 1 ? +(total - t).toFixed(2) : +(total * share).toFixed(2); out.push({ scene: sc, t0: +t.toFixed(2), dur: d, text, voice: text, visual }); t += d; });
  return out;
}
