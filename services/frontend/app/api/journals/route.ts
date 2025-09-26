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
      }
    );

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch journals" },
      { status: 500 }
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

    // Server-side mood conversion and validation
    let moodScore: string;
    if (typeof body.user_mood === "string" && isNaN(Number(body.user_mood))) {
      // Convert mood words to numbers
      const moodMap: Record<string, number> = {
        terrible: 1,
        bad: 2,
        poor: 3,
        neutral: 5,
        good: 7,
        great: 8,
        excellent: 9,
        amazing: 10,
      };
      moodScore = (moodMap[body.user_mood.toLowerCase()] || 5).toString();
    } else {
      moodScore = body.user_mood.toString();
    }

    // Validate mood is in valid range
    const moodNum = parseInt(moodScore);
    if (moodNum < 1 || moodNum > 10) {
      return NextResponse.json(
        { error: "Invalid mood score" },
        { status: 400 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/v1/journals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: session.user.id,
        journal_text: body.journal_text,
        user_mood: moodScore,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: "Failed to create journal" },
      { status: 500 }
    );
  }
}
