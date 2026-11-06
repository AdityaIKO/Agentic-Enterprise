"use client";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Product } from "@/lib/types";
import { PLATFORMS, LANGS, caption, creative, storyboard, type LangId, type PlatformId, type Platform } from "@/lib/agents/content";

function svgToImage(svg: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => { const img = new Image(); img.onload = () => res(img); img.onerror = rej; img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg); });
}
function download(name: string, blob: Blob) { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); }

async function renderPng(svg: string, w: number, h: number): Promise<Blob> {
  const img = await svgToImage(svg); const c = document.createElement("canvas"); c.width = w; c.height = h; c.getContext("2d")!.drawImage(img, 0, 0, w, h);
  return new Promise((r) => c.toBlob((b) => r(b!), "image/png"));
}

/** Renders the storyboard to a WebM file in the browser (canvas + MediaRecorder), at 720 px on the short side. */
async function renderVideo(p: Product, lang: LangId, plat: Platform, secs: number, onProgress: (x: number) => void): Promise<Blob> {
  const scenes = storyboard(p, lang, plat, secs); const total = scenes.reduce((a, s) => a + s.dur, 0);
  const k = Math.min(1, 720 / Math.min(plat.w, plat.h)); const W = Math.round(plat.w * k), H = Math.round(plat.h * k);
  const imgs = await Promise.all(scenes.map((s) => svgToImage(creative(p, lang, plat, s.scene).svg)));
  const canvas = document.createElement("canvas"); canvas.width = W; canvas.height = H; const g = canvas.getContext("2d")!;
  const mime = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"].find((m) => MediaRecorder.isTypeSupported(m)) || "video/webm";
  const rec = new MediaRecorder(canvas.captureStream(30), { mimeType: mime, videoBitsPerSecond: 2_500_000 }); const chunks: BlobPart[] = [];
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const done = new Promise<Blob>((r) => { rec.onstop = () => r(new Blob(chunks, { type: "video/webm" })); });
  rec.start(200);
  const t0 = performance.now();
  await new Promise<void>((resolve) => {
    const frame = () => {
      const t = (performance.now() - t0) / 1000; if (t >= total) { resolve(); return; }
      const i = Math.max(0, scenes.findIndex((s) => t >= s.t0 && t < s.t0 + s.dur)); const s = scenes[i]; const u = (t - s.t0) / s.dur;
      const zoom = 1 + 0.06 * u; const fade = Math.min(1, (t - s.t0) / 0.35);
      g.fillStyle = "#000"; g.fillRect(0, 0, W, H);
      if (i > 0 && fade < 1) { g.globalAlpha = 1; g.drawImage(imgs[i - 1], 0, 0, W, H); }
      g.globalAlpha = fade; g.save(); g.translate(W / 2, H / 2); g.scale(zoom, zoom); g.drawImage(imgs[i], -W / 2, -H / 2, W, H); g.restore(); g.globalAlpha = 1;
      onProgress(t / total); requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  });
  rec.stop(); return done;
}

export function ContentStudio({ products, verified }: { products: Product[]; verified: string[] }) {
  const [pid, setPid] = useState(products.find((p) => p.id === "coco-premium")?.id ?? products[0].id);
  const [langs, setLangs] = useState<LangId[]>(["en", "ar", "id"]);
  const [plats, setPlats] = useState<PlatformId[]>(["ig-feed", "ig-story", "ig-reel", "fb-feed", "yt-thumb", "linkedin"]);
  const [view, setView] = useState<LangId>("en");
  const [secs, setSecs] = useState(15);
  const [msg, setMsg] = useState("");
  const [vids, setVids] = useState<Record<string, { url?: string; pct: number }>>({});
  const r = useRouter();
  const p = products.find((x) => x.id === pid)!;
  const shown = langs.includes(view) ? view : langs[0] ?? "en";
  const selected = PLATFORMS.filter((x) => plats.includes(x.id));
  const items = useMemo(() => selected.map((pl) => ({ pl, c: creative(p, shown, pl), caps: langs.map((l) => ({ l, text: caption(p, l, pl) })) })), [p, shown, langs, plats]);
  const tog = <T,>(arr: T[], v: T, set: (x: T[]) => void) => set(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  return (
    <div>
      <div className="card">
        <div className="row"><b>Product</b>
          <select value={pid} onChange={(e) => setPid(e.target.value)}>{products.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></div>
        <div className="row" style={{ marginTop: 6 }}><b>Languages</b>{LANGS.map((l) => <label key={l.id}><input type="checkbox" checked={langs.includes(l.id)} onChange={() => tog(langs, l.id, setLangs)} /> {l.name}</label>)}</div>
        <div className="row" style={{ marginTop: 6 }}><b>Platforms</b>{PLATFORMS.map((x) => <label key={x.id}><input type="checkbox" checked={plats.includes(x.id)} onChange={() => tog(plats, x.id, setPlats)} /> {x.name}</label>)}</div>
        <p className="mute" style={{ margin: "6px 0 0" }}>Text is built only from verified claims ({verified.slice(0, 4).join("; ")}). Translations are drafts: ask a native speaker to check them. The agent does not post anything; you approve first, then publish yourself.</p>
      </div>
      <div className="row" style={{ margin: "10px 0" }}><b>Preview language</b>{langs.map((l) => <button key={l} className={"btn" + (l === shown ? "" : " alt")} onClick={() => setView(l)}>{LANGS.find((x) => x.id === l)!.name}</button>)}
        <span className="mute">Video length (s): <input className="n" type="number" min={8} max={60} value={secs} onChange={(e) => setSecs(+e.target.value)} /></span></div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 14 }}>
        {items.map(({ pl, c, caps }) => {
          const key = pl.id + shown; const v = vids[key];
          return (
            <div className="card" key={pl.id}>
              <b>{pl.name}</b> <span className="tag">{pl.w}x{pl.h} · {pl.ratio}</span> <span className="tag">{pl.kind}</span>
              <div style={{ margin: "8px 0", background: "#111", lineHeight: 0 }} dangerouslySetInnerHTML={{ __html: c.svg.replace(/width="\d+" height="\d+"/, 'width="100%" style="max-height:420px"') }} />
              <p className="mute" style={{ margin: "0 0 6px" }}>{pl.note} Safe zone: top {pl.safeTop}px, bottom {pl.safeBottom}px.</p>
              <div className="row">
                <button className="btn alt" onClick={() => download(`${p.id}-${pl.id}-${shown}.svg`, new Blob([c.svg], { type: "image/svg+xml" }))}>SVG</button>
                <button className="btn alt" onClick={async () => download(`${p.id}-${pl.id}-${shown}.png`, await renderPng(c.svg, pl.w, pl.h))}>PNG {pl.w}x{pl.h}</button>
                {pl.kind === "video" && <button className="btn" disabled={!!v && !v.url} onClick={async () => {
                  setVids((s) => ({ ...s, [key]: { pct: 0 } }));
                  const blob = await renderVideo(p, shown, pl, Math.min(pl.secMax!, Math.max(pl.secMin!, secs)), (x) => setVids((s) => ({ ...s, [key]: { pct: x } })));
                  setVids((s) => ({ ...s, [key]: { pct: 1, url: URL.createObjectURL(blob) } }));
                }}>{v && !v.url ? `Rendering ${Math.round(v.pct * 100)}%` : "Render video (WebM)"}</button>}
              </div>
              {pl.kind === "video" && <details style={{ marginTop: 6 }}><summary>Storyboard and voice-over ({shown})</summary>
                <table><tbody>{storyboard(p, shown, pl, Math.min(pl.secMax!, Math.max(pl.secMin!, secs))).map((s, i) => <tr key={i}><td>{s.t0}s +{s.dur}s</td><td>{s.text}</td></tr>)}</tbody></table></details>}
              {v?.url && <div style={{ marginTop: 6 }}><video src={v.url} controls style={{ width: "100%", maxHeight: 360 }} /><a className="btn alt" href={v.url} download={`${p.id}-${pl.id}-${shown}.webm`}>Download WebM</a></div>}
              {pl.maxCaption > 0 && caps.map(({ l, text }) => <div key={l} style={{ marginTop: 6 }}><span className="tag">{l}</span><pre style={{ whiteSpace: "pre-wrap", margin: "2px 0" }} dir={LANGS.find((x) => x.id === l)?.rtl ? "rtl" : "ltr"}>{text}</pre></div>)}
              {pl.maxCaption === 0 && <p className="mute">Text is on the picture only (no caption field).</p>}
            </div>
          );
        })}
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={async () => {
          const res = await fetch("/api/content/propose", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ productId: pid, langs, platforms: plats }) });
          const j = await res.json(); setMsg(res.ok ? `Proposed (${j.proposalId}). Approve it on the Today page. Nothing is posted by the app.` : j.error); r.refresh();
        }}>Send this pack to the owner for approval</button> <span className="mute">{msg}</span>
      </div>
    </div>
  );
}
