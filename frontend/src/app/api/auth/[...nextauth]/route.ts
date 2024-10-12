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
        const decodedToken = decodeJwt(user.access_token);
        token.accessTokenExpires = decodedToken.exp;
      }
      // Check if the token needs to be refreshed
      const currentTime = Math.floor(Date.now() / 1000);
      console.log("wait more " + ((token.accessTokenExpires as number) - currentTime) + " seconds");
      if ((token.accessTokenExpires as number) < currentTime) {
        try {
          const refreshedToken = await refreshAccessToken(token.refresh_token as string);
          token.access_token = refreshedToken.access_token;
          const decodedNewToken = decodeJwt(refreshedToken.access_token);
          token.accessTokenExpires = decodedNewToken.exp;
        } catch (error) {
          console.error("Error refreshing token:", error);
        }
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

function hasTokenExpired(expirationTimestamp: number) {
  const currentTime = Math.floor(Date.now() / 1000);
  return expirationTimestamp < currentTime;
}

async function refreshAccessToken(refreshToken: string) {
  try {
    console.log("================= Refreshing access token...");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Cookie': `refresh-token=${refreshToken}`
      },
    });
    
    if (!res.ok) {
      throw new Error('Failed to refresh token');
    }
    const cookies = extractCookies(res.headers.get("Set-Cookie"));
    return cookies;
  } catch (error) {
    console.error("Error refreshing token:", error);
    throw error;
  }
}

function decodeJwt(token: string) {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split('')
      .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  );
  return JSON.parse(jsonPayload);
}

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
