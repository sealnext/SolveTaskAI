import { useQueryClient } from '@tanstack/react-query';

import { useMutation } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import type { Login } from 'src/lib/schema';

export function useLogout() {
	const queryClient = useQueryClient();
	const navigate = useNavigate();

	return useMutation({
		mutationFn: () => fetch('/api/auth/logout', { method: 'POST' }),
		/* User should always be logged out (even if the request fails) */
		onSettled: () => {
			queryClient.setQueryData(['auth', 'status'], false);
			navigate({ to: '/login' });
		},
	});
}

export function useLogin() {
	const queryClient = useQueryClient();
	const navigate = useNavigate();

	return useMutation({
		mutationFn: (login: Login) =>
			fetch('/api/auth/login', { method: 'POST', body: JSON.stringify(login) }),
		onSuccess: () => {
			queryClient.setQueryData(['auth', 'status'], true);
			navigate({ to: '/' });
		},
		onError: () => {
			queryClient.setQueryData(['auth', 'status'], false);
		},
	});
}

export function useSignup() {
	const queryClient = useQueryClient();
	const navigate = useNavigate();

	return useMutation({
		mutationFn: (login: Login) =>
			fetch('/api/auth/signup', { method: 'POST', body: JSON.stringify(login) }),
		onSuccess: () => {
			queryClient.setQueryData(['auth', 'status'], true);
			navigate({ to: '/' });
		},
		onError: () => {
			queryClient.setQueryData(['auth', 'status'], false);
		},
	});
}
