import "next-auth";

declare module "next-auth" {
  interface User {
    access_token: string;
    refresh_token: string;
    full_name: string;
  }

  interface Session extends DefaultSession {
    user: User;
  }
}