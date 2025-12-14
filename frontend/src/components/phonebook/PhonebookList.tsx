/**
 * Phonebook list component with CRUD operations
 */

import { useState } from 'react';
import { usePhonebook, useDeletePhonebookEntry } from '../../hooks/usePhonebook';
import PhonebookForm from './PhonebookForm';
import type { PhonebookEntry } from '../../api/types';

export default function PhonebookList() {
  const { data: phonebookData, isLoading, error } = usePhonebook();
  const deleteEntry = useDeletePhonebookEntry();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<PhonebookEntry | null>(null);

  const handleEdit = (entry: PhonebookEntry) => {
    setEditingEntry(entry);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this entry?')) {
      try {
        await deleteEntry.mutateAsync(id);
      } catch (error) {
        alert(`Failed to delete entry: ${error}`);
      }
    }
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingEntry(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading phonebook...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading phonebook: {error.message}</p>
      </div>
    );
  }

  const entries = phonebookData?.entries || [];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          Total: {phonebookData?.total || 0} entries
        </div>
        <button
          onClick={() => setIsFormOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Entry
        </button>
      </div>

      {entries.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No phonebook entries yet.</p>
          <button
            onClick={() => setIsFormOpen(true)}
            className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            Add your first entry
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Number
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {entry.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEdit(entry)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(entry.id.toString())}
                      className="text-red-600 hover:text-red-900"
                      disabled={deleteEntry.isPending}
                    >
                      {deleteEntry.isPending ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isFormOpen && (
        <PhonebookForm entry={editingEntry} onClose={handleCloseForm} />
      )}
    </div>
  );
}
