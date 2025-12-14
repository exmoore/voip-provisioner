/**
 * React Query hooks for phone management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type {
  Phone,
  PhoneListResponse,
  CreatePhoneRequest,
  UpdatePhoneRequest,
  PhoneConfigResponse,
} from '../api/types';

const PHONES_QUERY_KEY = ['phones'];

/**
 * Fetch all phones
 */
export function usePhones() {
  return useQuery<PhoneListResponse>({
    queryKey: PHONES_QUERY_KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<PhoneListResponse>('/phones');
      return data;
    },
  });
}

/**
 * Fetch a single phone by MAC address
 */
export function usePhone(mac: string) {
  return useQuery<Phone>({
    queryKey: [...PHONES_QUERY_KEY, mac],
    queryFn: async () => {
      const { data } = await apiClient.get<Phone>(`/phones/${mac}`);
      return data;
    },
    enabled: !!mac,
  });
}

/**
 * Create a new phone
 */
export function useCreatePhone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (phone: CreatePhoneRequest) => {
      const { data } = await apiClient.post<Phone>('/phones', phone);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONES_QUERY_KEY });
    },
  });
}

/**
 * Update an existing phone
 */
export function useUpdatePhone(mac: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: UpdatePhoneRequest) => {
      const { data } = await apiClient.put<Phone>(`/phones/${mac}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: [...PHONES_QUERY_KEY, mac] });
    },
  });
}

/**
 * Delete a phone
 */
export function useDeletePhone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (mac: string) => {
      await apiClient.delete(`/phones/${mac}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONES_QUERY_KEY });
    },
  });
}

/**
 * Preview phone configuration
 */
export function usePhoneConfig(mac: string) {
  return useQuery<PhoneConfigResponse>({
    queryKey: [...PHONES_QUERY_KEY, mac, 'config'],
    queryFn: async () => {
      const { data } = await apiClient.get<PhoneConfigResponse>(`/phones/${mac}/config`);
      return data;
    },
    enabled: !!mac,
  });
}
