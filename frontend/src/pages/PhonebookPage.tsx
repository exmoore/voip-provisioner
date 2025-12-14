/**
 * Phonebook management page
 */

import PhonebookList from '../components/phonebook/PhonebookList';

export default function PhonebookPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Phonebook</h2>
        <p className="text-gray-600 mt-1">Manage shared directory entries</p>
      </div>

      <PhonebookList />
    </div>
  );
}
