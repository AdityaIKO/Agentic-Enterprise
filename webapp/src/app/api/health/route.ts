import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";
export function GET() { return NextResponse.json({ ok: true, llm: Boolean(process.env.ANTHROPIC_API_KEY) }); }
