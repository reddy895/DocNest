import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  X,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Tag,
  RefreshCw,
} from 'lucide-react';
import { uploadDocumentFile } from '../services/api';

const STAGES = [
  { id: 'validating', label: 'Validating PDF Format', pct: 20 },
  { id: 'parsing', label: 'Docling Layout Parsing', pct: 45 },
  { id: 'chunking', label: 'Structure-Aware Chunking', pct: 70 },
  { id: 'embedding', label: 'ChromaDB & BM25 Vectorization', pct: 90 },
  { id: 'ready', label: 'Ready & Indexed', pct: 100 },
];

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [tagsInput, setTagsInput] = useState('');
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | uploading | success | error
  const [currentStageIdx, setCurrentStageIdx] = useState(0);
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
    setCurrentStageIdx(0);
    setStatusMessage('Validating PDF magic bytes...');

    // Simulate stage progress animation while server computes
    const timer1 = setTimeout(() => {
      setCurrentStageIdx(1);
      setStatusMessage('Docling converting PDF layout into structured Markdown...');
    }, 600);

    const timer2 = setTimeout(() => {
      setCurrentStageIdx(2);
      setStatusMessage('Splitting semantic chunks on headings with overlap...');
    }, 1400);

    const timer3 = setTimeout(() => {
      setCurrentStageIdx(3);
      setStatusMessage('Computing nomic-embed-text vectors & updating BM25 index...');
    }, 2400);

    try {
      const data = await uploadDocumentFile(selectedFile, false);

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      setCurrentStageIdx(4);
      setResultData(data);
      setUploadStatus('success');
      setStatusMessage(
        data.status === 'already_indexed'
          ? 'Identical document already indexed in repository.'
          : `Successfully indexed ${data.page_count} pages and created ${data.total_chunks} vector chunks.`
      );

      if (onUploadSuccess) onUploadSuccess(data);
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setUploadStatus('error');
      setStatusMessage(err.message || 'Ingestion pipeline failed.');
    }
  };

  const resetModal = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setCurrentStageIdx(0);
    setStatusMessage('');
    setResultData(null);
    setTagsInput('');
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-deep/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg p-6 bg-carbon-surface border border-silver-border rounded-xl shadow-carbon-lg">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-silver-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-carbon-primary border border-silver-border flex items-center justify-center text-signal-yellow">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-silver-light">Upload PDF Document</h3>
              <p className="text-xs text-silver-secondary">Layout-aware IBM Docling & Hybrid RAG Ingestion</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 text-silver-secondary hover:text-silver-light rounded-lg hover:bg-carbon-secondary transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="py-5 space-y-4">
          {uploadStatus === 'idle' && (
            <>
              {/* Dropzone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
                  dragActive
                    ? 'border-signal-yellow bg-carbon-primary'
                    : 'border-silver-border hover:border-silver-primary bg-carbon-deep/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <FileText className="w-10 h-10 text-signal-yellow mx-auto mb-3" />
                <p className="text-sm font-semibold text-silver-light mb-1">
                  {selectedFile ? selectedFile.name : 'Click to select or drag and drop PDF'}
                </p>
                <p className="text-xs text-silver-secondary">
                  Supports research papers, earnings reports, manuals up to 50MB
                </p>
              </div>

              {/* Tags Input */}
              <div>
                <label className="block text-xs font-medium text-silver-primary mb-1">
                  Metadata Tags (Optional, comma-separated)
                </label>
                <div className="relative">
                  <Tag className="absolute left-3 top-2.5 w-4 h-4 text-silver-secondary" />
                  <input
                    type="text"
                    value={tagsInput}
                    onChange={(e) => setTagsInput(e.target.value)}
                    placeholder="finance, q3, compliance"
                    className="w-full pl-9 pr-3 py-2 text-xs bg-carbon-primary border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:border-signal-yellow focus:outline-none"
                  />
                </div>
              </div>
            </>
          )}

          {/* Uploading Stage Progress */}
          {uploadStatus === 'uploading' && (
            <div className="p-6 bg-carbon-primary border border-silver-border rounded-xl space-y-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-signal-yellow font-bold uppercase">{STAGES[currentStageIdx].label}</span>
                <span className="text-silver-secondary">{STAGES[currentStageIdx].pct}%</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-carbon-deep h-2 rounded-full overflow-hidden border border-silver-border/40">
                <div
                  className="bg-signal-yellow h-full transition-all duration-500 ease-out"
                  style={{ width: `${STAGES[currentStageIdx].pct}%` }}
                />
              </div>

              <div className="flex items-center gap-2 text-xs text-silver-secondary pt-1">
                <Loader2 className="w-4 h-4 animate-spin text-signal-yellow shrink-0" />
                <span>{statusMessage}</span>
              </div>
            </div>
          )}

          {/* Success Result */}
          {uploadStatus === 'success' && (
            <div className="p-5 bg-emerald-950/30 border border-emerald-800/60 rounded-xl space-y-3">
              <div className="flex items-center gap-2.5 text-emerald-400 font-semibold text-sm">
                <CheckCircle2 className="w-5 h-5" />
                <span>Document Ingestion Complete</span>
              </div>
              <p className="text-xs text-silver-primary">{statusMessage}</p>

              {resultData && (
                <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs font-mono bg-carbon-deep/60 p-2.5 rounded-lg border border-silver-border/40">
                  <div>
                    <span className="text-silver-secondary block text-[10px]">PAGES</span>
                    <span className="text-silver-light font-bold">{resultData.page_count}</span>
                  </div>
                  <div>
                    <span className="text-silver-secondary block text-[10px]">CHUNKS</span>
                    <span className="text-signal-yellow font-bold">{resultData.total_chunks}</span>
                  </div>
                  <div>
                    <span className="text-silver-secondary block text-[10px]">STATUS</span>
                    <span className="text-emerald-400 font-bold uppercase">{resultData.status}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {uploadStatus === 'error' && (
            <div className="p-4 bg-red-950/30 border border-red-800/60 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-red-400 font-semibold text-sm">
                <AlertCircle className="w-5 h-5" />
                <span>Ingestion Error</span>
              </div>
              <p className="text-xs text-silver-primary">{statusMessage}</p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-silver-border">
          {uploadStatus === 'idle' && (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-xs font-semibold text-silver-secondary hover:text-silver-light transition"
              >
                Cancel
              </button>
              <button
                onClick={executeUpload}
                disabled={!selectedFile}
                className="px-4 py-2 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg shadow-carbon-sm transition disabled:opacity-40"
              >
                Process & Vectorize PDF
              </button>
            </>
          )}

          {uploadStatus === 'success' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg shadow-carbon-sm transition"
            >
              Done & View Library
            </button>
          )}

          {uploadStatus === 'error' && (
            <button
              onClick={() => setUploadStatus('idle')}
              className="px-4 py-2 bg-carbon-primary border border-silver-border hover:border-signal-yellow text-silver-light text-xs font-semibold rounded-lg transition"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
