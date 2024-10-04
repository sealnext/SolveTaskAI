import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { NextAuthOptions } from "next-auth";


export const authOptions: NextAuthOptions = {
  
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: "Username", type: "text", placeholder: "jsmith" },
        password: { label: "Password", type: "password" }
      },
      
      async authorize(credentials, req) {
        if (!credentials?.username || !credentials?.password) {
          throw new Error("Please enter both the username and password.");
        }

        try {
          console.log("Attempting to connect to backend...");
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
            method: 'POST',
            body: new URLSearchParams({
              username: credentials.username,
              password: credentials.password,
            }),
            headers: { 
              "Content-Type": "application/x-www-form-urlencoded",
            },
            credentials: 'include',
          });

          const cookies = extractCookies(res.headers.get("Set-Cookie"));

          if (res.ok) {
            const data = await res.json();
            return {
              email: credentials.username,
              full_name: data.full_name,
              access_token: cookies.access_token,
              refresh_token: cookies.refresh_token,
            };
          } else {
            throw new Error("Incorrect username or password.");
          }
        } catch (error) {
          throw new Error(error.message);
        }
      }
    })
  ],
  pages: {
    signIn: '/login',
  },
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.access_token = user.access_token;
        token.refresh_token = user.refresh_token;
        token.full_name = user.full_name;
      }
      return token;
    },
    async session({ session, token }) {
      session.user = {
        ...session.user,
        full_name: token.full_name as string,
      };
      return session;
    }
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST }

function extractCookies(setCookieHeader: string) {
  const cookies: Record<string, string> = {};
  
  if (setCookieHeader) {
    const cookiesArray = setCookieHeader.split(', ');

    cookiesArray.forEach(cookieString => {
      const [cookieKeyValue] = cookieString.split(';');
      const [key, value] = cookieKeyValue.split('=');
      cookies[key] = value;
    });
  }

  return cookies;
}