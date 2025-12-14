/**
 * React Query hooks for global settings management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import type { GlobalSettings, UpdateGlobalSettingsRequest } from '../api/types';

const SETTINGS_QUERY_KEY = ['settings'];

/**
 * Fetch global settings
 */
export function useSettings() {
  return useQuery<GlobalSettings>({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: async () => {
      const { data } = await apiClient.get<GlobalSettings>('/settings');
      return data;
    },
  });
}

/**
 * Update global settings
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: UpdateGlobalSettingsRequest) => {
      const { data } = await apiClient.put<GlobalSettings>('/settings', updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    },
  });
}
