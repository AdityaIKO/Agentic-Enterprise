import { NextRequest, NextResponse } from "next/server";

// Optional HTTP Basic auth: set APP_PASSWORD (user "admin"). Leave empty for local use.
export function middleware(req: NextRequest) {
  const pw = process.env.APP_PASSWORD;
  if (!pw || req.nextUrl.pathname === "/api/health") return NextResponse.next();
  const h = req.headers.get("authorization") || "";
  if (h.startsWith("Basic ")) {
    const [u, p] = atob(h.slice(6)).split(":");
    if (u === "admin" && p === pw) return NextResponse.next();
  }
  return new NextResponse("Authentication required", { status: 401, headers: { "WWW-Authenticate": 'Basic realm="Kraka Ops"' } });
}
export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
