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
  FolderPlus,
} from 'lucide-react';
import { uploadDocumentFile } from '../services/api';

const ALLOWED_EXTS = ['.pdf', '.docx', '.txt', '.md', '.csv'];

const STAGES = [
  { id: 'validating', label: 'Validating Document Structure & Magic Bytes', pct: 20 },
  { id: 'parsing', label: 'Layout & Content Parsing', pct: 45 },
  { id: 'chunking', label: 'Semantic & Markdown Chunking', pct: 70 },
  { id: 'embedding', label: 'ChromaDB (nomic-embed) & BM25 Vectorization', pct: 90 },
  { id: 'ready', label: 'Ready & Grounded', pct: 100 },
];

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | uploading | success | error
  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [processedCount, setProcessedCount] = useState(0);
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

  const validateAndFilterFiles = (filesList) => {
    const valid = [];
    for (const file of filesList) {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (!ALLOWED_EXTS.includes(ext)) {
        continue;
      }
      if (file.size > 50 * 1024 * 1024) {
        continue;
      }
      valid.push(file);
    }
    return valid;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const valid = validateAndFilterFiles(e.dataTransfer.files);
      if (valid.length > 0) {
        setSelectedFiles(valid);
        setUploadStatus('idle');
        setStatusMessage('');
      } else {
        setUploadStatus('error');
        setStatusMessage('No valid files found. Supported formats: PDF, DOCX, TXT, MD, CSV (max 50MB).');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const valid = validateAndFilterFiles(e.target.files);
      if (valid.length > 0) {
        setSelectedFiles(valid);
        setUploadStatus('idle');
        setStatusMessage('');
      } else {
        setUploadStatus('error');
        setStatusMessage('No valid files selected. Supported formats: PDF, DOCX, TXT, MD, CSV.');
      }
    }
  };

  const handleStartUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploadStatus('uploading');
    setCurrentStageIdx(0);
    setProcessedCount(0);

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setStatusMessage(`Processing (${i + 1}/${selectedFiles.length}): ${file.name}`);

        // Stage animation
        setCurrentStageIdx(1);
        await new Promise((r) => setTimeout(r, 200));
        setCurrentStageIdx(2);

        await uploadDocumentFile(file, false);

        setCurrentStageIdx(3);
        await new Promise((r) => setTimeout(r, 150));
        setProcessedCount(i + 1);
      }

      setCurrentStageIdx(4);
      setUploadStatus('success');
      setStatusMessage(`Successfully processed ${selectedFiles.length} document(s).`);

      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      setUploadStatus('error');
      setStatusMessage(err.message || 'Ingestion failed.');
    }
  };

  const resetModal = () => {
    setSelectedFiles([]);
    setUploadStatus('idle');
    setCurrentStageIdx(0);
    setStatusMessage('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in font-sans">
      <div className="relative w-full max-w-lg p-6 bg-[#191C1F] border border-[#343A3F] rounded-2xl shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#343A3F]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#E5B83D]/10 rounded-lg text-[#E5B83D]">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-[#F0F1F2]">Upload Research Documents</h3>
              <p className="text-[11px] text-[#A0A6AC]">
                PDF, DOCX, TXT, MD, CSV (up to 50MB each)
              </p>
            </div>
          </div>
          <button
            onClick={resetModal}
            className="p-1.5 text-[#A0A6AC] hover:text-[#F0F1F2] rounded-lg hover:bg-[#22262A] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drag and Drop Zone */}
        {uploadStatus !== 'uploading' && uploadStatus !== 'success' && (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-3 ${
              dragActive
                ? 'border-[#E5B83D] bg-[#E5B83D]/5'
                : 'border-[#343A3F] hover:border-[#E5B83D]/60 bg-[#111315]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="w-12 h-12 rounded-full bg-[#191C1F] border border-[#343A3F] flex items-center justify-center text-[#E5B83D]">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-[#F0F1F2]">
                Drag and drop multiple files here, or <span className="text-[#E5B83D]">browse</span>
              </p>
              <p className="text-[10px] text-[#A0A6AC] font-mono">
                Preserves headings, reading order, and table layouts
              </p>
            </div>

            {selectedFiles.length > 0 && (
              <div className="mt-2 p-2.5 bg-[#191C1F] border border-[#343A3F] rounded-lg w-full text-left space-y-1">
                <span className="text-[10px] font-mono uppercase text-[#A0A6AC] block">
                  Selected Files ({selectedFiles.length}):
                </span>
                <div className="max-h-24 overflow-y-auto space-y-1 text-xs">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-[#F0F1F2]">
                      <span className="truncate">{f.name}</span>
                      <span className="text-[10px] text-[#A0A6AC] font-mono">
                        {(f.size / 1024).toFixed(0)} KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Upload Progress & Stepper */}
        {uploadStatus === 'uploading' && (
          <div className="p-4 bg-[#111315] border border-[#343A3F] rounded-xl space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-[#F0F1F2]">{statusMessage}</span>
              <Loader2 className="w-4 h-4 animate-spin text-[#E5B83D]" />
            </div>

            {/* Stepper */}
            <div className="space-y-2 text-xs">
              {STAGES.map((stage, idx) => {
                const isDone = idx < currentStageIdx;
                const isCurrent = idx === currentStageIdx;
                return (
                  <div key={stage.id} className="flex items-center gap-2.5">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                        isDone
                          ? 'bg-emerald-500 text-[#111315]'
                          : isCurrent
                          ? 'bg-[#E5B83D] text-[#111315] animate-pulse'
                          : 'bg-[#22262A] text-[#A0A6AC]'
                      }`}
                    >
                      {isDone ? '✓' : idx + 1}
                    </div>
                    <span
                      className={`text-xs ${
                        isCurrent
                          ? 'text-[#E5B83D] font-semibold'
                          : isDone
                          ? 'text-[#F0F1F2]'
                          : 'text-[#A0A6AC]/60'
                      }`}
                    >
                      {stage.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Success Alert */}
        {uploadStatus === 'success' && (
          <div className="p-4 bg-emerald-950/30 border border-emerald-500/50 rounded-xl space-y-2 text-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <p className="text-xs font-semibold text-emerald-300">{statusMessage}</p>
            <p className="text-[11px] text-[#A0A6AC]">
              Documents are indexed and available in your research library and chat workspace.
            </p>
          </div>
        )}

        {/* Error Alert */}
        {uploadStatus === 'error' && (
          <div className="p-3.5 bg-rose-950/30 border border-rose-500/50 rounded-xl flex items-start gap-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-2">
          {uploadStatus === 'success' ? (
            <button
              onClick={resetModal}
              className="px-4 py-2 bg-[#E5B83D] hover:bg-[#F2C64B] text-[#111315] font-semibold text-xs rounded-lg transition"
            >
              Done & Return
            </button>
          ) : (
            <>
              <button
                onClick={resetModal}
                disabled={uploadStatus === 'uploading'}
                className="px-3 py-1.5 text-xs text-[#A0A6AC] hover:text-[#F0F1F2] rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleStartUpload}
                disabled={selectedFiles.length === 0 || uploadStatus === 'uploading'}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#E5B83D] hover:bg-[#F2C64B] disabled:opacity-40 text-[#111315] font-semibold text-xs rounded-lg shadow-sm transition"
              >
                {uploadStatus === 'uploading' ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Start Ingestion ({selectedFiles.length})</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
