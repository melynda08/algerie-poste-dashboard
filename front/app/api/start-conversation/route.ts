import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const token = request.headers.get("Authorization")

    if (!token) {
      return NextResponse.json({ error: "Authorization token is missing" }, { status: 401 })
    }

    // Call the backend API
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/start_conversation`, {
      method: "POST",
      headers: {
        Authorization: token,
        "Content-Type": "application/json",
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ error: data.error || "Failed to start conversation" }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("Start conversation error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
