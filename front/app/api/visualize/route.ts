import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const data = await request.json()
    const token = request.headers.get("Authorization")

    if (!token) {
      return NextResponse.json({ error: "Authorization token is missing" }, { status: 401 })
    }

    // Call the backend API
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/visualize`, {
      method: "POST",
      headers: {
        Authorization: token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })

    const responseData = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: responseData.error || "Failed to generate visualization" },
        { status: response.status },
      )
    }

    return NextResponse.json(responseData)
  } catch (error) {
    console.error("Visualization error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
