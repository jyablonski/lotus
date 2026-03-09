/**
 * Example API route for sync-user-records.
 * Used to demonstrate how API endpoints are added in this Next.js project.
 * No actual sync logic is implemented.
 */
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const SyncUserRecordsSchema = z.object({
  user_id: z.string(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = SyncUserRecordsSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: "Invalid request", details: z.flattenError(parsed.error) },
        { status: 400 },
      );
    }

    const { user_id } = parsed.data;
    console.log(`[sync-user-records] Request received for user_id: ${user_id}`);

    return NextResponse.json({ ok: true, user_id }, { status: 200 });
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
}
