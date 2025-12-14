/**
 * Global settings management page
 */

import GlobalSettingsForm from '../components/settings/GlobalSettingsForm';

export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Global Settings</h2>
        <p className="text-gray-600 mt-1">Configure default phone settings</p>
      </div>

      <GlobalSettingsForm />
    </div>
  );
}
