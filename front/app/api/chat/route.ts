import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { question, conversation_id } = await request.json()
    const token = request.headers.get("Authorization")

    if (!token) {
      return NextResponse.json({ error: "Authorization token is missing" }, { status: 401 })
    }

    // Call the backend API
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
      method: "POST",
      headers: {
        Authorization: token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, conversation_id }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ error: data.error || "Failed to process request" }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("Chat error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
