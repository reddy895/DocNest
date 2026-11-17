import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  X,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  AlertTriangle,
} from 'lucide-react';

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | uploading | success | error
  const [statusMessage, setStatusMessage] = useState('');
  const [resultData, setResultData] = useState(null);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus('error');
      setStatusMessage('Invalid file format. Only PDF files are supported.');
      return false;
    }
    const maxBytes = 50 * 1024 * 1024; // 50MB
    if (file.size > maxBytes) {
      setUploadStatus('error');
      setStatusMessage('File exceeds 50MB size limit.');
      return false;
    }
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setUploadStatus('idle');
        setStatusMessage('');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setUploadStatus('idle');
        setStatusMessage('');
      }
    }
  };

  const executeUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setStatusMessage('Validating PDF and extracting text page-by-page...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setResultData(data);
      setUploadStatus('success');
      setStatusMessage(
        data.status === 'already_indexed'
          ? 'Identical document already indexed in repository.'
          : `Successfully indexed ${data.page_count} pages and generated ${data.total_chunks} vector chunks.`
      );

      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
    } catch (err) {
      setUploadStatus('error');
      setStatusMessage(err.message || 'An unexpected error occurred during upload.');
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setStatusMessage('');
    setResultData(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="carbon-card max-w-lg w-full p-6 shadow-carbon-lg relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-[#969DA3] hover:text-[#E0E3E5] p-1"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-lg font-bold text-[#E0E3E5] mb-1">Upload Document</h3>
        <p className="text-xs text-[#969DA3] mb-4">
          Ingest institutional PDF files for semantic indexing and grounded RAG querying.
        </p>

        {/* Dropzone */}
        {uploadStatus !== 'success' && (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragActive
                ? 'border-[#F4D21F] bg-[#F4D21F]/5'
                : 'border-[#555C61] hover:border-[#969DA3] bg-[#171A1C]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <UploadCloud className="w-10 h-10 text-[#F4D21F] mx-auto mb-3" />
            <p className="text-sm font-medium text-[#E0E3E5] mb-1">
              Drag and drop your PDF here, or browse
            </p>
            <p className="text-xs text-[#969DA3]">
              PDF format up to 50MB • Strict page-aware extraction
            </p>
          </div>
        )}

        {/* Selected File Banner */}
        {selectedFile && uploadStatus !== 'success' && (
          <div className="mt-4 p-3 bg-[#171A1C] border border-[#555C61] rounded-md flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <FileText className="w-5 h-5 text-[#F4D21F] shrink-0" />
              <div className="min-w-0">
                <div className="text-xs font-medium text-[#E0E3E5] truncate">
                  {selectedFile.name}
                </div>
                <div className="text-[11px] text-[#969DA3] font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </div>
              </div>
            </div>
            {uploadStatus === 'idle' && (
              <button
                onClick={resetForm}
                className="text-xs text-[#969DA3] hover:text-[#E0E3E5] ml-2"
              >
                Change
              </button>
            )}
          </div>
        )}

        {/* Upload Status / Progress States */}
        {uploadStatus === 'uploading' && (
          <div className="mt-4 p-4 bg-[#171A1C] border border-[#F4D21F]/40 rounded-md">
            <div className="flex items-center gap-3 mb-2">
              <Loader2 className="w-4 h-4 text-[#F4D21F] animate-spin" />
              <span className="text-xs font-medium text-[#E0E3E5]">
                Processing & Vectorizing Document...
              </span>
            </div>
            <div className="w-full bg-[#303538] h-1.5 rounded-full overflow-hidden">
              <div className="bg-[#F4D21F] h-full w-2/3 animate-pulse rounded-full"></div>
            </div>
            <p className="text-[11px] text-[#969DA3] mt-2 font-mono">{statusMessage}</p>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="mt-4 p-3 bg-rose-950/40 border border-rose-500/50 rounded-md flex items-start gap-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <span className="font-semibold block">Processing Failed</span>
              <span>{statusMessage}</span>
            </div>
          </div>
        )}

        {uploadStatus === 'success' && resultData && (
          <div className="space-y-4 py-2">
            <div className="p-4 bg-emerald-950/30 border border-emerald-500/40 rounded-md text-xs">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>Document Ingestion Complete</span>
              </div>
              <p className="text-[#BFC3C7] text-xs mb-3">{statusMessage}</p>

              <div className="grid grid-cols-2 gap-2 font-mono text-[11px] bg-[#171A1C] p-2.5 rounded border border-[#555C61]">
                <div>
                  <span className="text-[#969DA3]">Pages:</span>{' '}
                  <span className="text-[#E0E3E5]">{resultData.page_count}</span>
                </div>
                <div>
                  <span className="text-[#969DA3]">Chunks:</span>{' '}
                  <span className="text-[#E0E3E5]">{resultData.total_chunks}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  resetForm();
                  onClose();
                }}
                className="btn-primary text-xs py-1.5 px-4"
              >
                Done
              </button>
            </div>
          </div>
        )}

        {/* Modal Actions */}
        {uploadStatus !== 'success' && (
          <div className="flex justify-end gap-2 mt-5">
            <button
              onClick={onClose}
              disabled={uploadStatus === 'uploading'}
              className="btn-secondary text-xs py-1.5 px-3"
            >
              Cancel
            </button>
            <button
              onClick={executeUpload}
              disabled={!selectedFile || uploadStatus === 'uploading'}
              className="btn-primary text-xs py-1.5 px-4"
            >
              {uploadStatus === 'uploading' ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <span>Start Indexing</span>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

