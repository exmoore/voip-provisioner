/**
 * Phone list component with CRUD operations
 */

import { useState } from 'react';
import { usePhones, useDeletePhone } from '../../hooks/usePhones';
import PhoneForm from './PhoneForm';
import type { Phone } from '../../api/types';

export default function PhoneList() {
  const { data: phonesData, isLoading, error } = usePhones();
  const deletePhone = useDeletePhone();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingPhone, setEditingPhone] = useState<Phone | null>(null);

  const handleEdit = (phone: Phone) => {
    setEditingPhone(phone);
    setIsFormOpen(true);
  };

  const handleDelete = async (mac: string) => {
    if (window.confirm('Are you sure you want to delete this phone?')) {
      try {
        await deletePhone.mutateAsync(mac);
      } catch (error) {
        alert(`Failed to delete phone: ${error}`);
      }
    }
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingPhone(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading phones...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading phones: {error.message}</p>
      </div>
    );
  }

  const phones = phonesData?.phones || [];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          Total: {phonesData?.total || 0} phones
        </div>
        <button
          onClick={() => setIsFormOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Phone
        </button>
      </div>

      {phones.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No phones configured yet.</p>
          <button
            onClick={() => setIsFormOpen(true)}
            className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            Add your first phone
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Extension
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Display Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MAC Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Label
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {phones.map((phone) => (
                <tr key={phone.mac} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {phone.extension}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {phone.display_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                    {phone.mac}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {phone.model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-800 text-xs">
                      {phone.vendor || 'Unknown'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {phone.label || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEdit(phone)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(phone.mac)}
                      className="text-red-600 hover:text-red-900"
                      disabled={deletePhone.isPending}
                    >
                      {deletePhone.isPending ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isFormOpen && (
        <PhoneForm
          phone={editingPhone}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}
