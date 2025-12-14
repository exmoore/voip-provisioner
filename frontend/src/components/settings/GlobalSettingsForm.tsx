/**
 * Global settings form component
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';

const settingsSchema = z.object({
  pbx_server: z.string().min(1, 'PBX server is required'),
  pbx_port: z.number().min(1, 'PBX port must be greater than 0'),
  transport: z.string().min(1, 'Transport is required'),
  codecs: z.string().min(1, 'Codecs are required'), // Will be split into array on submit
  ntp_server: z.string().min(1, 'NTP server is required'),
  timezone: z.string().min(1, 'Timezone is required'),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export default function GlobalSettingsForm() {
  const { data: settings, isLoading, error } = useSettings();
  const updateSettings = useUpdateSettings();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    values: settings
      ? {
          pbx_server: settings.pbx_server,
          pbx_port: settings.pbx_port,
          transport: settings.transport,
          codecs: settings.codecs.join(','),
          ntp_server: settings.ntp_server,
          timezone: settings.timezone,
        }
      : undefined,
  });

  const onSubmit = async (data: SettingsFormData) => {
    try {
      // Convert codecs string to array
      const codecsArray = data.codecs
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean);

      await updateSettings.mutateAsync({
        ...data,
        codecs: codecsArray,
      });
      alert('Settings updated successfully');
    } catch (error) {
      alert(`Failed to update settings: ${error}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading settings: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
        {/* PBX Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 border-b pb-2">
            PBX Settings
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* PBX Server */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PBX Server *
              </label>
              <input
                {...register('pbx_server')}
                type="text"
                placeholder="pbx.example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.pbx_server && (
                <p className="mt-1 text-sm text-red-600">{errors.pbx_server.message}</p>
              )}
            </div>

            {/* PBX Port */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PBX Port *
              </label>
              <input
                {...register('pbx_port', { valueAsNumber: true })}
                type="number"
                placeholder="5060"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.pbx_port && (
                <p className="mt-1 text-sm text-red-600">{errors.pbx_port.message}</p>
              )}
            </div>
          </div>

          {/* Transport */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Transport *
            </label>
            <select
              {...register('transport')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="udp">UDP</option>
              <option value="tcp">TCP</option>
              <option value="tls">TLS</option>
            </select>
            {errors.transport && (
              <p className="mt-1 text-sm text-red-600">{errors.transport.message}</p>
            )}
          </div>

          {/* Codecs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Codecs *
            </label>
            <input
              {...register('codecs')}
              type="text"
              placeholder="ulaw,alaw,g722"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.codecs && (
              <p className="mt-1 text-sm text-red-600">{errors.codecs.message}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Comma-separated list of codecs
            </p>
          </div>
        </div>

        {/* Phone Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 border-b pb-2">
            Phone Settings
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* NTP Server */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                NTP Server *
              </label>
              <input
                {...register('ntp_server')}
                type="text"
                placeholder="pool.ntp.org"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.ntp_server && (
                <p className="mt-1 text-sm text-red-600">{errors.ntp_server.message}</p>
              )}
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timezone *
              </label>
              <input
                {...register('timezone')}
                type="text"
                placeholder="America/New_York"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.timezone && (
                <p className="mt-1 text-sm text-red-600">{errors.timezone.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}
