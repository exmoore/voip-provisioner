/**
 * Phonebook form component for create/edit
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreatePhonebookEntry, useUpdatePhonebookEntry } from '../../hooks/usePhonebook';
import type { PhonebookEntry } from '../../api/types';

const phonebookSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  number: z.string().min(1, 'Number is required'),
});

type PhonebookFormData = z.infer<typeof phonebookSchema>;

interface PhonebookFormProps {
  entry: PhonebookEntry | null;
  onClose: () => void;
}

export default function PhonebookForm({ entry, onClose }: PhonebookFormProps) {
  const isEditing = !!entry;
  const createEntry = useCreatePhonebookEntry();
  const updateEntry = useUpdatePhonebookEntry(entry?.id.toString() || '0');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PhonebookFormData>({
    resolver: zodResolver(phonebookSchema),
    defaultValues: entry
      ? {
          name: entry.name,
          number: entry.number,
        }
      : undefined,
  });

  const onSubmit = async (data: PhonebookFormData) => {
    try {
      if (isEditing) {
        await updateEntry.mutateAsync(data);
      } else {
        await createEntry.mutateAsync(data);
      }
      onClose();
    } catch (error) {
      alert(`Failed to ${isEditing ? 'update' : 'create'} entry: ${error}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {isEditing ? 'Edit Phonebook Entry' : 'Add Phonebook Entry'}
          </h3>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              {...register('name')}
              type="text"
              placeholder="John Doe"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          {/* Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Number *
            </label>
            <input
              {...register('number')}
              type="text"
              placeholder="555-1234"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.number && (
              <p className="mt-1 text-sm text-red-600">{errors.number.message}</p>
            )}
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSubmitting
                ? isEditing
                  ? 'Updating...'
                  : 'Creating...'
                : isEditing
                ? 'Update Entry'
                : 'Create Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
