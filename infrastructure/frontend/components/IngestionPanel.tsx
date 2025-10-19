'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { submitReport, getDomains } from '@/lib/api-client';
import { subscribeToStatusUpdates, StatusUpdate } from '@/lib/appsync-client';
import { getStoredUser } from '@/lib/auth';

interface Domain {
  id: string;
  name: string;
  description: string;
}

export default function IngestionPanel() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [reportText, setReportText] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Load available domains
    loadDomains();
  }, []);

  useEffect(() => {
    if (!jobId) return;

    const user = getStoredUser();
    if (!user) return;

    // Subscribe to status updates
    const subscription = subscribeToStatusUpdates(
      user.userId,
      (update: StatusUpdate) => {
        if (update.jobId === jobId) {
          const message = `${update.agentName}: ${update.message}`;
          setStatusMessages((prev) => [...prev, message]);
          
          if (update.status === 'complete') {
            setSuccess(true);
            setLoading(false);
          } else if (update.status === 'error') {
            setLoading(false);
          }
        }
      },
      (error) => {
        console.error('Status subscription error:', error);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId]);

  const loadDomains = async () => {
    const response = await getDomains();
    if (response.data?.domains) {
      setDomains(response.data.domains);
      if (response.data.domains.length > 0) {
        setSelectedDomain(response.data.domains[0].id);
      }
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const maxImages = 5;
    const maxSize = 5 * 1024 * 1024; // 5MB

    const newImages: string[] = [];
    let errorMessage = '';

    Array.from(files).slice(0, maxImages - images.length).forEach((file) => {
      if (file.size > maxSize) {
        errorMessage = `Image ${file.name} exceeds 5MB limit`;
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          newImages.push(event.target.result as string);
          if (newImages.length === Math.min(files.length, maxImages - images.length)) {
            setImages((prev) => [...prev, ...newImages]);
          }
        }
      };
      reader.readAsDataURL(file);
    });

    if (errorMessage) {
      alert(errorMessage);
    }
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedDomain || !reportText.trim()) {
      alert('Please select a domain and enter report text');
      return;
    }

    setLoading(true);
    setStatusMessages([]);
    setSuccess(false);
    setJobId(null);

    const response = await submitReport(selectedDomain, reportText, images);
    
    if (response.data?.job_id) {
      setJobId(response.data.job_id);
      setStatusMessages(['Report submitted. Processing...']);
    } else {
      alert(response.error || 'Failed to submit report');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setReportText('');
    setImages([]);
    setStatusMessages([]);
    setJobId(null);
    setSuccess(false);
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col bg-white p-4 overflow-hidden">
      <h2 className="text-xl font-bold mb-4">Submit Report</h2>
      
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
        {/* Domain Selection */}
        <div className="mb-4">
          <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
            Domain
          </label>
          <select
            id="domain"
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {domains.map((domain) => (
              <option key={domain.id} value={domain.id}>
                {domain.name}
              </option>
            ))}
          </select>
        </div>

        {/* Report Text */}
        <div className="mb-4 flex-1 flex flex-col min-h-0">
          <label htmlFor="report" className="block text-sm font-medium text-gray-700 mb-1">
            Report Description
          </label>
          <textarea
            id="report"
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            disabled={loading}
            placeholder="Describe the incident or issue..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>

        {/* Image Upload */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Images (max 5, 5MB each)
          </label>
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageUpload}
            disabled={loading || images.length >= 5}
            className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          
          {images.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {images.map((img, index) => (
                <div key={index} className="relative">
                  <Image
                    src={img}
                    alt={`Upload ${index + 1}`}
                    width={64}
                    height={64}
                    className="w-16 h-16 object-cover rounded"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    disabled={loading}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status Messages */}
        {statusMessages.length > 0 && (
          <div className="mb-4 p-3 bg-gray-50 rounded-md max-h-32 overflow-y-auto custom-scrollbar">
            {statusMessages.map((msg, index) => (
              <div key={index} className="text-sm text-gray-700 mb-1">
                {msg}
              </div>
            ))}
          </div>
        )}

        {/* Success Message */}
        {success && jobId && (
          <div className="mb-4 p-3 bg-green-50 rounded-md">
            <div className="text-sm text-green-800">
              ✓ Report submitted successfully! Job ID: {jobId}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || !selectedDomain || !reportText.trim()}
            className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Submit Report'}
          </button>
          
          {(success || statusMessages.length > 0) && (
            <button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="py-2 px-4 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              New Report
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
