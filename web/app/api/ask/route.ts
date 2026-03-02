import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { question } = body;

    if (typeof question !== "string" || !question.trim()) {
      return NextResponse.json(
        { error: "Invalid request: question must be a non-empty string" },
        { status: 400 }
      );
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const response = await fetch(`${apiUrl}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json({ answer: data.answer });

  } catch (err) {
    console.error("API error:", err);
    return NextResponse.json(
      { error: "Failed to get answer from MMJ vault" },
      { status: 500 }
    );
  }
}
