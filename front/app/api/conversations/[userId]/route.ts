import { NextResponse } from "next/server"

export async function GET(request: Request, { params }: { params: { userId: string } }) {
  try {
    const { userId } = params
    const token = request.headers.get("Authorization")

    if (!token) {
      return NextResponse.json({ error: "Authorization token is missing" }, { status: 401 })
    }

    // Call the backend API
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/conversations/${userId}`, {
      headers: {
        Authorization: token,
      },
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ error: data.error || "Failed to fetch conversations" }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("Fetch conversations error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
