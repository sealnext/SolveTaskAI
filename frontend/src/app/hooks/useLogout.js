'use client'

import { useRouter } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { useState } from 'react';
import { apiClient } from '@/lib/apiClient'; // Ajustează calea în funcție de structura proiectului tău

export function useLogout() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await apiClient.post('/auth/logout');

      // Dacă cererea de logout a reușit, deconectăm și sesiunea NextAuth
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