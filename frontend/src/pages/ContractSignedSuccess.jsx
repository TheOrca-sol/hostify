import React from 'react'
import { CheckCircle, Download, Home } from 'lucide-react'

export default function ContractSignedSuccess() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          {/* Success Icon */}
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          
          {/* Success Message */}
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Contract Signed Successfully!
          </h1>
          
          <p className="text-gray-600 mb-6">
            Your rental contract has been signed and is now legally binding. 
            You will receive a confirmation SMS shortly, and a copy of the signed contract will be available for download.
          </p>
          
          {/* Next Steps */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-blue-800 mb-2">What happens next?</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• You'll receive a confirmation SMS</li>
              <li>• The host will be notified of your signature</li>
              <li>• Your check-in details will be sent shortly</li>
              <li>• Keep this confirmation for your records</li>
            </ul>
          </div>
          
          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => window.print()}
              className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Download className="h-4 w-4 mr-2" />
              Print Confirmation
            </button>
            
            <button
              onClick={() => window.close()}
              className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Home className="h-4 w-4 mr-2" />
              Close Window
            </button>
          </div>
          
          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Thank you for choosing our service. If you have any questions, 
              please contact your host directly.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 