import React, { useRef, useState } from 'react'
import SignaturePad from 'react-signature-canvas'
import { Trash2, PenTool, Download } from 'lucide-react'

const SignatureCapture = ({
  value = null,
  onChange,
  width = 400,
  height = 200,
  showDownload = false,
  label = "Digital Signature",
  placeholder = "Please sign here",
  required = false,
  className = ""
}) => {
  const signaturePadRef = useRef()
  const [hasSignature, setHasSignature] = useState(!!value)

  const handleClear = () => {
    if (signaturePadRef.current) {
      signaturePadRef.current.clear()
      setHasSignature(false)
      if (onChange) {
        onChange(null)
      }
    }
  }

  const handleEnd = () => {
    if (signaturePadRef.current) {
      const isEmpty = signaturePadRef.current.isEmpty()
      setHasSignature(!isEmpty)
      
      if (onChange) {
        if (isEmpty) {
          onChange(null)
        } else {
          const signatureData = signaturePadRef.current.toDataURL('image/png')
          onChange(signatureData)
        }
      }
    }
  }

  const handleDownload = () => {
    if (signaturePadRef.current && !signaturePadRef.current.isEmpty()) {
      const dataURL = signaturePadRef.current.toDataURL('image/png')
      const link = document.createElement('a')
      link.download = 'signature.png'
      link.href = dataURL
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  // Load existing signature if provided
  React.useEffect(() => {
    if (value && signaturePadRef.current) {
      signaturePadRef.current.fromDataURL(value)
      setHasSignature(true)
    }
  }, [value])

  return (
    <div className={`space-y-4 ${className}`}>
      {label && (
        <div className="flex items-center space-x-2">
          <PenTool className="w-5 h-5 text-gray-600" />
          <label className="block text-sm font-medium text-gray-700">
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        </div>
      )}
      
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 bg-gray-50">
        <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
          <div className="relative">
            <SignaturePad
              ref={signaturePadRef}
              onEnd={handleEnd}
              canvasProps={{
                width: width,
                height: height,
                className: 'w-full h-full cursor-crosshair'
              }}
              backgroundColor="rgba(255, 255, 255, 1)"
              penColor="black"
            />
            
            {/* Placeholder text when empty */}
            {!hasSignature && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <p className="text-gray-400 text-sm">{placeholder}</p>
              </div>
            )}
          </div>
        </div>
        
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleClear}
              type="button"
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear
            </button>
            
            {showDownload && hasSignature && (
              <button
                onClick={handleDownload}
                type="button"
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <Download className="w-4 h-4 mr-2" />
                Download
              </button>
            )}
          </div>
          
          {hasSignature && (
            <div className="flex items-center text-sm text-green-600">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Signature captured
            </div>
          )}
        </div>
      </div>
      
      {required && !hasSignature && (
        <p className="text-sm text-red-600">Please provide your signature to continue.</p>
      )}
    </div>
  )
}

export default SignatureCapture 