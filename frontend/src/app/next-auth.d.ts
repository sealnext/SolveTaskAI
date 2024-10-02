import "next-auth";

declare module "next-auth" {
  interface User {
    access_token: string;
    refresh_token: string;
    csrf_token: string;
  }

  interface Session extends DefaultSession {
    user: User;
    csrf_token: string;
  }
}