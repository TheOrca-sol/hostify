import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { toast } from '../components/Toaster';

const GuestVerification = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [step, setStep] = useState('loading'); // loading, info, upload, form, success, error
  const [linkInfo, setLinkInfo] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    cin_or_passport: '',
    birthdate: '',
    nationality: '',
    address: '',
    document_type: ''
  });
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    verifyToken();
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await api.getVerificationInfo(token);
      
      if (response.success) {
        setLinkInfo(response);
        // If guest already verified, show success
        if (response.guest_status === 'verified') {
          setStep('success');
          toast.info('You have already completed verification');
        } else {
          setStep('info');
        }
      } else {
        setStep('error');
        toast.error(response.error || 'Invalid verification link');
      }
    } catch (error) {
      setStep('error');
      toast.error('Failed to verify link');
      console.error('Error verifying token:', error);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const requiredFields = ['full_name', 'cin_or_passport', 'birthdate', 'nationality'];
    
    requiredFields.forEach(field => {
      if (!formData[field]) {
        newErrors[field] = `${field.replace('_', ' ')} is required`;
      }
    });

    // Validate CIN format (if Moroccan ID)
    if (formData.document_type === 'CIN' && formData.cin_or_passport) {
      const cinRegex = /^[A-Z]{1,2}[0-9]{5,6}$/;
      if (!cinRegex.test(formData.cin_or_passport)) {
        newErrors.cin_or_passport = 'Invalid CIN format';
      }
    }

    // Validate birthdate (must be in the past)
    if (formData.birthdate) {
      const birthDate = new Date(formData.birthdate);
      if (birthDate > new Date()) {
        newErrors.birthdate = 'Birthdate cannot be in the future';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload only JPG, JPEG, or PNG files');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response = await api.uploadGuestDocument(token, file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success) {
        // Check if OCR detected poor image quality
        if (response.data.error_message) {
          toast.error(response.data.error_message);
          // Show helpful tips for better photo
          toast.error('Tips: Ensure good lighting, avoid glare, and keep the document flat and in focus', {
            duration: 8000
          });
          return;
        }
        
        setExtractedData(response.data);
        setFormData({
          full_name: response.data.full_name || '',
          cin_or_passport: response.data.cin_or_passport || '',
          birthdate: response.data.birthdate || '',
          nationality: response.data.nationality || '',
          address: response.data.address || '',
          document_type: response.data.document_type || ''
        });
        setStep('form');
        
        // Check if any fields were extracted successfully
        const hasData = response.data.full_name || response.data.cin_or_passport || 
                       response.data.birthdate || response.data.nationality;
        
        if (hasData) {
          toast.success('ID document processed successfully');
        } else {
          toast.warning('Document processed but some information may need manual entry');
        }
      } else {
        toast.error(response.error || 'Failed to process document');
      }
    } catch (error) {
      toast.error('Failed to upload document');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      toast.error('Please fix the errors before submitting');
      return;
    }

    try {
      setSubmitting(true);
      const response = await api.submitGuestVerification(token, formData);
      
      if (response.success) {
        setStep('success');
        toast.success('Verification completed successfully!');
        await api.generateContractAndScheduleSms(linkInfo.guest_id);
      } else {
        toast.error(response.error || 'Failed to submit verification');
      }
    } catch (error) {
      toast.error('Failed to submit verification');
      console.error('Submit error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (step === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying link...</p>
        </div>
      </div>
    );
  }

  if (step === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="bg-red-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid Link</h1>
          <p className="text-gray-600 mb-6">This verification link is invalid, expired, or has already been used.</p>
          <p className="text-sm text-gray-500">Please contact your host for a new verification link.</p>
        </div>
      </div>
    );
  }

  if (step === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="bg-green-100 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Verification Complete!</h1>
          <p className="text-gray-600 mb-6">Your identity has been successfully verified. Your host will receive the information.</p>
          <p className="text-sm text-gray-500">You can now close this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Guest ID Verification</h1>
          {linkInfo?.guest_name && (
            <p className="text-gray-600">Welcome, {linkInfo.guest_name}</p>
          )}
          <p className="text-sm text-gray-500 mt-2">
            Please upload your ID document to complete the verification process
          </p>
        </div>

        {/* Info Step */}
        {step === 'info' && (
          <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
            <div className="text-center mb-6">
              <div className="bg-blue-100 p-3 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Upload Your ID Document</h2>
              <p className="text-gray-600 mb-6">
                We'll scan your ID and extract the information automatically
              </p>
            </div>

            <div className="space-y-4 mb-6">
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Moroccan CIN or Passport accepted
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Your data is encrypted and secure
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Takes less than 2 minutes
              </div>
            </div>

            <button
              onClick={() => setStep('upload')}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Continue
            </button>
          </div>
        )}

        {/* Upload Step */}
        {step === 'upload' && (
          <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">Upload ID Document</h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
                disabled={uploading}
              />
              <label
                htmlFor="file-upload"
                className={`cursor-pointer ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {!uploading ? (
                  <>
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-blue-600">Click to upload</span>
                      <span className="text-gray-500"> or drag and drop</span>
                      <p className="text-xs text-gray-400 mt-1">PNG, JPG, JPEG up to 10MB</p>
                    </div>
                  </>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                    <div className="text-sm text-gray-600">Processing document...</div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </label>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => setStep('info')}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400 transition-colors"
                disabled={uploading}
              >
                Back
              </button>
            </div>
          </div>
        )}

        {/* Form Step */}
        {step === 'form' && (
          <div className="bg-white rounded-lg p-8 shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">Verify Your Information</h2>
            <p className="text-sm text-gray-600 mb-6 text-center">
              Please review and correct any information below
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => {
                    setFormData({...formData, full_name: e.target.value});
                    setErrors({...errors, full_name: ''});
                  }}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.full_name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.full_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  value={formData.document_type}
                  onChange={(e) => {
                    setFormData({...formData, document_type: e.target.value});
                    setErrors({...errors, document_type: ''});
                  }}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.document_type ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                >
                  <option value="">Select document type</option>
                  <option value="CIN">Moroccan CIN</option>
                  <option value="Passport">Passport</option>
                </select>
                {errors.document_type && (
                  <p className="mt-1 text-sm text-red-600">{errors.document_type}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CIN or Passport Number *
                </label>
                <input
                  type="text"
                  value={formData.cin_or_passport}
                  onChange={(e) => {
                    setFormData({...formData, cin_or_passport: e.target.value});
                    setErrors({...errors, cin_or_passport: ''});
                  }}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.cin_or_passport ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.cin_or_passport && (
                  <p className="mt-1 text-sm text-red-600">{errors.cin_or_passport}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Birthdate *
                </label>
                <input
                  type="date"
                  value={formData.birthdate}
                  onChange={(e) => {
                    setFormData({...formData, birthdate: e.target.value});
                    setErrors({...errors, birthdate: ''});
                  }}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.birthdate ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.birthdate && (
                  <p className="mt-1 text-sm text-red-600">{errors.birthdate}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nationality *
                </label>
                <input
                  type="text"
                  value={formData.nationality}
                  onChange={(e) => {
                    setFormData({...formData, nationality: e.target.value});
                    setErrors({...errors, nationality: ''});
                  }}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.nationality ? 'border-red-300' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.nationality && (
                  <p className="mt-1 text-sm text-red-600">{errors.nationality}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="mt-8 flex space-x-3">
              <button
                onClick={() => setStep('upload')}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400 transition-colors"
                disabled={submitting}
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                disabled={submitting}
              >
                {submitting ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </div>
                ) : (
                  'Complete Verification'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GuestVerification; 