import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";

export async function GET(request) {
    const secret = process.env.NEXTAUTH_SECRET;

    // Get the JWT token from the request
    const token = await getToken({ req: request, secret });
    console.log("Token:", token);
    if (token) {
        console.log("Decoded token:", token);
        return NextResponse.json(token);
    } else {
        return NextResponse.json({ message: "Token not found or invalid" }, { status: 401 });
    }
}