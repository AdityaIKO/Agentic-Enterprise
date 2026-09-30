import { NextResponse } from "next/server";
import { load, save } from "@/lib/store";
import { decide } from "@/lib/governance";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { decision } = (await req.json()) as { decision: "approved" | "rejected" };
  const s = load();
  try {
    const p = decide(s, id, decision);
    save(s);
    return NextResponse.json({ ok: true, proposal: p });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 400 });
  }
}
