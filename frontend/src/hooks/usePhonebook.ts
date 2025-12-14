/**
 * React Query hooks for phonebook management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type {
  PhonebookEntry,
  PhonebookListResponse,
  CreatePhonebookEntryRequest,
  UpdatePhonebookEntryRequest,
} from '../api/types';

const PHONEBOOK_QUERY_KEY = ['phonebook'];

/**
 * Fetch all phonebook entries
 */
export function usePhonebook() {
  return useQuery<PhonebookListResponse>({
    queryKey: PHONEBOOK_QUERY_KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<PhonebookListResponse>('/phonebook');
      return data;
    },
  });
}

/**
 * Create a new phonebook entry
 */
export function useCreatePhonebookEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entry: CreatePhonebookEntryRequest) => {
      const { data } = await apiClient.post<PhonebookEntry>('/phonebook', entry);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONEBOOK_QUERY_KEY });
    },
  });
}

/**
 * Update a phonebook entry
 */
export function useUpdatePhonebookEntry(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: UpdatePhonebookEntryRequest) => {
      const { data } = await apiClient.put<PhonebookEntry>(`/phonebook/${id}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONEBOOK_QUERY_KEY });
    },
  });
}

/**
 * Delete a phonebook entry
 */
export function useDeletePhonebookEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/phonebook/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PHONEBOOK_QUERY_KEY });
    },
  });
}
