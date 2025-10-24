import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAtom, useSetAtom } from 'jotai';
import { authApi } from '@/api/auth';
import {
  accessTokenAtom,
  refreshTokenAtom,
  userAtom,
  logoutAtom,
  isAuthenticatedAtom
} from '@/store/auth';
import { useAtomValue } from 'jotai';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useAtom(accessTokenAtom);
  const [, setRefreshToken] = useAtom(refreshTokenAtom);
  const [user, setUser] = useAtom(userAtom);
  const logout = useSetAtom(logoutAtom);
  const isAuthenticated = useAtomValue(isAuthenticatedAtom);

  // Get current user query
  const { data: currentUser, isLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!accessToken && !user,
    retry: false,
  });

  // Update user atom when query succeeds
  if (currentUser && !user) {
    setUser(currentUser);
  }

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      logout();
      queryClient.clear();
    },
  });

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoginLoading: loginMutation.isPending,
    isRegisterLoading: registerMutation.isPending,
  };
};

