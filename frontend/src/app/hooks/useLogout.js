'use client'

import { useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { useState } from 'react';
import ApiClient from '@/lib/apiClient';

export function useLogout() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { post } = ApiClient();

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await post('/auth/logout');
      await signOut({ redirect: false });
      router.push('/login');
    } catch (err) {
      setError(err.message || 'Logout failed');
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return { logout, isLoading, error };
}