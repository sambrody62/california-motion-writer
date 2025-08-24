import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { profileAPI } from '../../services/api';
import { UserIcon, HomeIcon, PhoneIcon } from '@heroicons/react/20/solid';

interface ProfileFormData {
  is_petitioner: boolean;
  county: string;
  case_number: string;
  party_name: string;
  other_party_name: string;
  party_address: string;
  party_phone: string;
  other_party_attorney: string;
  children_info: Array<{
    name: string;
    date_of_birth: string;
    lives_with: string;
  }>;
}

const CALIFORNIA_COUNTIES = [
  'Alameda', 'Alpine', 'Amador', 'Butte', 'Calaveras', 'Colusa', 'Contra Costa',
  'Del Norte', 'El Dorado', 'Fresno', 'Glenn', 'Humboldt', 'Imperial', 'Inyo',
  'Kern', 'Kings', 'Lake', 'Lassen', 'Los Angeles', 'Madera', 'Marin', 'Mariposa',
  'Mendocino', 'Merced', 'Modoc', 'Mono', 'Monterey', 'Napa', 'Nevada', 'Orange',
  'Placer', 'Plumas', 'Riverside', 'Sacramento', 'San Benito', 'San Bernardino',
  'San Diego', 'San Francisco', 'San Joaquin', 'San Luis Obispo', 'San Mateo',
  'Santa Barbara', 'Santa Clara', 'Santa Cruz', 'Shasta', 'Sierra', 'Siskiyou',
  'Solano', 'Sonoma', 'Stanislaus', 'Sutter', 'Tehama', 'Trinity', 'Tulare',
  'Tuolumne', 'Ventura', 'Yolo', 'Yuba'
];

export const ProfileSetup: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [children, setChildren] = useState<any[]>([]);
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<ProfileFormData>();

  useEffect(() => {
    // Load existing profile if available
    profileAPI.getProfile()
      .then(response => {
        const profile = response.data;
        Object.keys(profile).forEach(key => {
          setValue(key as any, profile[key]);
        });
        if (profile.children_info) {
          setChildren(profile.children_info);
        }
      })
      .catch(() => {
        // No profile yet
      })
      .finally(() => {
        setLoading(false);
      });
  }, [setValue]);

  const onSubmit = async (data: ProfileFormData) => {
    try {
      setError('');
      data.children_info = children;
      
      // Try to update first, if that fails, create
      try {
        await profileAPI.updateProfile(data);
      } catch {
        await profileAPI.createProfile(data);
      }
      
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save profile');
    }
  };

  const addChild = () => {
    setChildren([...children, { name: '', date_of_birth: '', lives_with: 'Petitioner' }]);
  };

  const removeChild = (index: number) => {
    setChildren(children.filter((_, i) => i !== index));
  };

  const updateChild = (index: number, field: string, value: string) => {
    const updated = [...children];
    updated[index][field] = value;
    setChildren(updated);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Profile Information
            </h3>
            <p className="mt-1 text-sm text-gray-600">
              This information will be used to auto-fill your court documents.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-6">
              {/* Party Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Are you the Petitioner or Respondent?
                </label>
                <div className="mt-2 space-x-4">
                  <label className="inline-flex items-center">
                    <input
                      {...register('is_petitioner')}
                      type="radio"
                      value="true"
                      className="form-radio h-4 w-4 text-indigo-600"
                    />
                    <span className="ml-2">Petitioner</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      {...register('is_petitioner')}
                      type="radio"
                      value="false"
                      className="form-radio h-4 w-4 text-indigo-600"
                    />
                    <span className="ml-2">Respondent</span>
                  </label>
                </div>
              </div>

              {/* County */}
              <div>
                <label htmlFor="county" className="block text-sm font-medium text-gray-700">
                  County
                </label>
                <select
                  {...register('county', { required: 'County is required' })}
                  id="county"
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="">Select a county</option>
                  {CALIFORNIA_COUNTIES.map(county => (
                    <option key={county} value={county}>{county}</option>
                  ))}
                </select>
                {errors.county && (
                  <p className="mt-1 text-sm text-red-600">{errors.county.message}</p>
                )}
              </div>

              {/* Case Number */}
              <div>
                <label htmlFor="case_number" className="block text-sm font-medium text-gray-700">
                  Case Number
                </label>
                <input
                  {...register('case_number')}
                  type="text"
                  id="case_number"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., FL-2024-001234"
                />
              </div>

              {/* Party Names */}
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="party_name" className="block text-sm font-medium text-gray-700">
                    Your Full Name
                  </label>
                  <input
                    {...register('party_name', { required: 'Your name is required' })}
                    type="text"
                    id="party_name"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                  {errors.party_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.party_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="other_party_name" className="block text-sm font-medium text-gray-700">
                    Other Party's Full Name
                  </label>
                  <input
                    {...register('other_party_name', { required: 'Other party name is required' })}
                    type="text"
                    id="other_party_name"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                  {errors.other_party_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.other_party_name.message}</p>
                  )}
                </div>
              </div>

              {/* Contact Information */}
              <div>
                <label htmlFor="party_address" className="block text-sm font-medium text-gray-700">
                  Your Address
                </label>
                <textarea
                  {...register('party_address', { required: 'Address is required' })}
                  id="party_address"
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
                {errors.party_address && (
                  <p className="mt-1 text-sm text-red-600">{errors.party_address.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="party_phone" className="block text-sm font-medium text-gray-700">
                  Your Phone Number
                </label>
                <input
                  {...register('party_phone', { required: 'Phone number is required' })}
                  type="tel"
                  id="party_phone"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="(555) 123-4567"
                />
                {errors.party_phone && (
                  <p className="mt-1 text-sm text-red-600">{errors.party_phone.message}</p>
                )}
              </div>

              {/* Other Party Attorney */}
              <div>
                <label htmlFor="other_party_attorney" className="block text-sm font-medium text-gray-700">
                  Other Party's Attorney (if any)
                </label>
                <input
                  {...register('other_party_attorney')}
                  type="text"
                  id="other_party_attorney"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Attorney name and bar number"
                />
              </div>

              {/* Children Information */}
              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="block text-sm font-medium text-gray-700">
                    Children Information
                  </label>
                  <button
                    type="button"
                    onClick={addChild}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Add Child
                  </button>
                </div>

                {children.map((child, index) => (
                  <div key={index} className="mb-4 p-4 border border-gray-200 rounded-md">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Child's Name
                        </label>
                        <input
                          type="text"
                          value={child.name}
                          onChange={(e) => updateChild(index, 'name', e.target.value)}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Date of Birth
                        </label>
                        <input
                          type="date"
                          value={child.date_of_birth}
                          onChange={(e) => updateChild(index, 'date_of_birth', e.target.value)}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Lives With
                        </label>
                        <select
                          value={child.lives_with}
                          onChange={(e) => updateChild(index, 'lives_with', e.target.value)}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        >
                          <option value="Petitioner">Petitioner</option>
                          <option value="Respondent">Respondent</option>
                          <option value="Both">Both (shared custody)</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeChild(index)}
                      className="mt-2 text-sm text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Skip for now
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};