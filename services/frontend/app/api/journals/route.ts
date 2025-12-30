import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";

export async function GET(request: NextRequest) {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Get query parameters from the request
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "10";
    const offset = searchParams.get("offset") || "0";

    // Make request to your Go backend
    const response = await fetch(
      `${BACKEND_URL}/v1/journals?user_id=${session.user.id}&limit=${limit}&offset=${offset}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();

    // Define the backend response type (what Go returns)
    interface BackendJournal {
      journalId: string;
      userId: string;
      journalText: string;
      userMood: string; // Backend returns as string
      createdAt: string;
    }

    // Transform the data: convert userMood from string to number
    const transformedData = {
      ...data,
      journals:
        (data.journals as BackendJournal[])?.map((journal) => ({
          ...journal,
          userMood: parseInt(journal.userMood), // Convert string to number
        })) || [],
    };

    return NextResponse.json(transformedData);
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch journals" },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await auth();

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { journal_text, mood_score } = body;

    if (!journal_text) {
      return NextResponse.json(
        { error: "journal_text is required" },
        { status: 400 },
      );
    }

    const response = await fetch(`${BACKEND_URL}/v1/journals`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: session.user.id,
        journal_text: journal_text,
        user_mood: mood_score?.toString() || undefined,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error:", errorText);
      throw new Error(`Backend responded with ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to create journal" },
      { status: 500 },
    );
  }
}
