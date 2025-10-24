import axios from '@/lib/axios';

export interface User {
  id: string;
  user_name: string;
  email: string;
  verified: boolean;
  role: string;
  preferences: string[];
  created_at: string;
}

export interface UserListResponse {
  total: number;
  page: number;
  page_size: number;
  users: User[];
}

export interface UserStats {
  total_users: number;
  verified_users: number;
  unverified_users: number;
  admin_users: number;
  recent_users: number;
}

export interface UserUpdateData {
  user_name?: string;
  email?: string;
  verified?: boolean;
  role?: string;
  preferences?: string[];
}

export interface UserCreateData {
  email: string;
  password: string;
  user_name?: string;
  role?: string;
  verified?: boolean;
  preferences?: string[];
}

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
  verified?: boolean;
}

export interface BulkActionResponse {
  success: boolean;
  action: string;
  updated_count: number;
  total_requested: number;
}

export const adminApi = {
  // Get list of users with filters
  getUsers: async (params?: UserListParams): Promise<UserListResponse> => {
    const response = await axios.get('/api/v1/admin/users', { params });
    return response.data;
  },

  // Get single user by ID
  getUser: async (userId: string): Promise<User> => {
    const response = await axios.get(`/api/v1/admin/users/${userId}`);
    return response.data;
  },

  // Update user
  updateUser: async (userId: string, data: UserUpdateData): Promise<User> => {
    const response = await axios.patch(`/api/v1/admin/users/${userId}`, data);
    return response.data;
  },

  // Delete user
  deleteUser: async (userId: string): Promise<void> => {
    await axios.delete(`/api/v1/admin/users/${userId}`);
  },

  // Get user statistics
  getStats: async (): Promise<UserStats> => {
    const response = await axios.get('/api/v1/admin/stats');
    return response.data;
  },

  // Bulk action on multiple users
  bulkAction: async (userIds: string[], action: string): Promise<BulkActionResponse> => {
    const response = await axios.post(`/api/v1/admin/users/bulk-action?action=${action}`, userIds);
    return response.data;
  },

  // Create user
  createUser: async (data: UserCreateData): Promise<User> => {
    const response = await axios.post('/api/v1/admin/users', data);
    return response.data;
  },
};
