/**
 * Phones management page
 */

import PhoneList from '../components/phones/PhoneList';

export default function PhonesPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Phones</h2>
        <p className="text-gray-600 mt-1">Manage VOIP phone configurations</p>
      </div>

      <PhoneList />
    </div>
  );
}
