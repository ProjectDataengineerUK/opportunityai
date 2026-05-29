import { NextRequest, NextResponse } from "next/server";

const BACKEND = (process.env.BACKEND_URL || "http://localhost:8080").replace(/\/$/, "");

async function proxy(req: NextRequest): Promise<NextResponse> {
  const { pathname, search } = new URL(req.url);
  const target = `${BACKEND}${pathname}${search}`;

  const init: RequestInit = { method: req.method };

  if (req.method !== "GET" && req.method !== "HEAD") {
    const body = await req.text();
    init.body = body || undefined;
    init.headers = {
      "content-type": req.headers.get("content-type") ?? "application/json",
    };
  }

  const res = await fetch(target, init);
  const json = await res.json();
  return NextResponse.json(json, { status: res.status });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
