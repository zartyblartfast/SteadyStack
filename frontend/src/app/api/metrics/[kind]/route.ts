import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
const ALLOWED_KINDS = new Set(["summary", "bmri", "bitcoin-risk"]);

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ kind: string }> }
) {
  const { kind } = await params;

  if (!ALLOWED_KINDS.has(kind)) {
    return NextResponse.json({ detail: "Unknown metrics endpoint" }, { status: 404 });
  }

  try {
    const res = await fetch(`${BACKEND}/api/metrics/${kind}`, {
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    return NextResponse.json(
      { detail: e instanceof Error ? e.message : "Backend unreachable" },
      { status: 502 }
    );
  }
}
