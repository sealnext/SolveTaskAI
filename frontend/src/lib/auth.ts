import { parseCookies } from 'nookies';

export function getAuthTokens() {
  const cookies = parseCookies();
  return {
    accessToken: cookies['next-auth.access-token'],
    refreshToken: cookies['next-auth.refresh-token'],
    csrfToken: cookies['next-auth.csrf-token'],
  };
}