/**
 * TanStack Query hooks for admin user management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../lib/admin-api';
import type {
  AdminUserCreate,
  AdminUserUpdate,
  AdminUserPasswordUpdate,
} from '../types/api';

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

const KEYS = {
  users: ['admin', 'users'] as const,
  user: (id: number) => ['admin', 'users', id] as const,
  roles: ['admin', 'roles'] as const,
  sucursales: ['admin', 'sucursales'] as const,
};

// ---------------------------------------------------------------------------
// List users
// ---------------------------------------------------------------------------

export function useAdminUsers() {
  return useQuery({
    queryKey: KEYS.users,
    queryFn: adminApi.listUsers,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

// ---------------------------------------------------------------------------
// Single user
// ---------------------------------------------------------------------------

export function useAdminUser(id: number) {
  return useQuery({
    queryKey: KEYS.user(id),
    queryFn: () => adminApi.getUser(id),
    enabled: id > 0,
    staleTime: 1000 * 60 * 2,
  });
}

// ---------------------------------------------------------------------------
// Create user
// ---------------------------------------------------------------------------

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AdminUserCreate) => adminApi.createUser(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: KEYS.users });
    },
  });
}

// ---------------------------------------------------------------------------
// Update user
// ---------------------------------------------------------------------------

export function useUpdateUser(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AdminUserUpdate) => adminApi.updateUser(id, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: KEYS.users });
      void queryClient.invalidateQueries({ queryKey: KEYS.user(id) });
    },
  });
}

// ---------------------------------------------------------------------------
// Reset password
// ---------------------------------------------------------------------------

export function useResetPassword(id: number) {
  return useMutation({
    mutationFn: (body: AdminUserPasswordUpdate) => adminApi.resetPassword(id, body),
  });
}

// ---------------------------------------------------------------------------
// Roles
// ---------------------------------------------------------------------------

export function useAdminRoles() {
  return useQuery({
    queryKey: KEYS.roles,
    queryFn: adminApi.listRoles,
    staleTime: 1000 * 60 * 60, // 1 hour — roles rarely change
  });
}

// ---------------------------------------------------------------------------
// Sucursales
// ---------------------------------------------------------------------------

export function useAdminSucursales() {
  return useQuery({
    queryKey: KEYS.sucursales,
    queryFn: adminApi.listSucursales,
    staleTime: 1000 * 60 * 60,
  });
}
