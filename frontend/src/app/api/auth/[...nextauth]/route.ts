import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { NextAuthOptions } from "next-auth";

// Function to convert an object to URL-encoded form data
function toFormData(obj) {
  const formBody = [];
  for (const property in obj) {
    const encodedKey = encodeURIComponent(property);
    const encodedValue = encodeURIComponent(obj[property]);
    formBody.push(`${encodedKey}=${encodedValue}`);
  }
  return formBody.join("&");
}

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
          console.log("Missing credentials");
          return null;
        }

        try {
          console.log("Attempting to connect to backend...");
          const res = await fetch("http://localhost:8000/auth/login", {
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

          console.log("Response status:", res.status);
          const data = await res.json();
          console.log("Response data:", data);

          if (res.ok && data) {
            return {
              id: data.user_id || data.username,
              name: data.username,
              email: data.username,
              access_token: data.access_token,
              refresh_token: data.refresh_token,
              csrf_token: data.csrf_token,
            };
          } else {
            console.error('Authorization failed:', data);
            return null;
          }
        } catch (error) {
          console.error('Error during authorization:', error);
          return null;
        }
      }
    })
  ],
  pages: {
    signIn: '/login'
  },
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.access_token = user.access_token;
        token.refresh_token = user.refresh_token;
        token.csrf_token = user.csrf_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.user = {
        ...session.user,
        // session data to be accessed by the client
      };
      return session;
    }
  },
  secret: process.env.NEXTAUTH_SECRET,
  jwt: {
    encryption: true,
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST }