import { axiosInstance } from '@/lib/axios';
import type { User } from '@/store/auth';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface VerifyEmailData {
  email: string;
  code: string;
}

export interface VerifyEmailResponse {
  success: boolean;
  message: string;
  remaining_attempts?: number | null;
}

export interface ResendVerificationData {
  email: string;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await axiosInstance.post('/api/v1/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await axiosInstance.post('/api/v1/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await axiosInstance.post('/api/v1/auth/logout');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await axiosInstance.get('/api/v1/auth/me');
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await axiosInstance.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  verifyEmail: async (data: VerifyEmailData): Promise<VerifyEmailResponse> => {
    const response = await axiosInstance.post('/api/v1/auth/verify-email', data);
    return response.data;
  },

  resendVerification: async (data: ResendVerificationData): Promise<ResendVerificationResponse> => {
    const response = await axiosInstance.post('/api/v1/auth/resend-verification', data);
    return response.data;
  },
};

