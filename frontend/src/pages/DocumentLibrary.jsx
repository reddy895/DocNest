import React, { useState } from 'react';
import {
  Files,
  Search,
  Trash2,
  Eye,
  MessageSquare,
  UploadCloud,
  FileText,
  AlertTriangle,
  Calendar,
  Layers,
} from 'lucide-react';

export default function DocumentLibrary({
  documents = [],
  onDeleteDocument,
  onViewDocument,
  onQueryDocument,
  onOpenUpload,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Recent';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return 'Recent';
    }
  };

  const handleDeleteClick = (docId) => {
    setDeleteConfirmId(docId);
  };

  const confirmDelete = async (docId) => {
    if (onDeleteDocument) {
      await onDeleteDocument(docId);
    }
    setDeleteConfirmId(null);
  };

  return (
    <div className="space-y-6">
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#E0E3E5] tracking-tight">
            Document Repository
          </h2>
          <p className="text-xs text-[#969DA3]">
            Manage all indexed PDF documents, inspect metadata, or remove documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#969DA3] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="carbon-input pl-9 pr-3 py-1.5 text-xs w-48 sm:w-64"
            />
          </div>

          <button onClick={onOpenUpload} className="btn-primary text-xs py-1.5 px-3">
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        </div>
      </div>

      {/* Documents Grid / Table */}
      {filteredDocs.length === 0 ? (
        <div className="carbon-card p-12 text-center">
          <Files className="w-10 h-10 text-[#969DA3] mx-auto mb-3 opacity-40" />
          <h3 className="text-base font-semibold text-[#E0E3E5] mb-1">
            {searchTerm ? 'No documents match your search' : 'No documents in repository'}
          </h3>
          <p className="text-xs text-[#969DA3] max-w-sm mx-auto mb-4">
            {searchTerm
              ? 'Try modifying your search keywords.'
              : 'Upload institutional PDFs to build your grounded knowledge base.'}
          </p>
          {!searchTerm && (
            <button onClick={onOpenUpload} className="btn-primary text-xs py-2 px-4">
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => (
            <div
              key={doc.doc_id}
              className="carbon-card p-5 flex flex-col justify-between hover:border-[#F4D21F]/60 transition-colors"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="w-9 h-9 rounded bg-[#171A1C] border border-[#555C61] flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-[#F4D21F]" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#171A1C] border border-emerald-500/40 text-emerald-400">
                    INDEXED
                  </span>
                </div>

                <h3 className="font-semibold text-sm text-[#E0E3E5] truncate mb-1" title={doc.filename}>
                  {doc.filename}
                </h3>

                {doc.is_scanned && (
                  <div className="flex items-center gap-1.5 text-[11px] text-amber-400 mb-2">
                    <AlertTriangle className="w-3 h-3 shrink-0" />
                    <span>Low text density (Scanned PDF)</span>
                  </div>
                )}

                <div className="space-y-1.5 py-3 border-y border-[#555C61]/40 text-xs font-mono text-[#969DA3]">
                  <div className="flex justify-between">
                    <span>Pages:</span>
                    <span className="text-[#E0E3E5]">{doc.page_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Chunks:</span>
                    <span className="text-[#E0E3E5]">{doc.total_chunks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>File Size:</span>
                    <span className="text-[#E0E3E5]">{formatFileSize(doc.file_size_bytes)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uploaded:</span>
                    <span className="text-[#E0E3E5]">{formatDate(doc.upload_date)}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between gap-2 pt-4 mt-2">
                <button
                  onClick={() => onQueryDocument && onQueryDocument(doc.doc_id)}
                  className="btn-primary text-xs py-1.5 px-3 flex-1"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Ask AI</span>
                </button>

                <button
                  onClick={() => onViewDocument && onViewDocument(doc)}
                  className="btn-secondary text-xs p-1.5 text-[#BFC3C7] hover:text-[#E0E3E5]"
                  title="Preview PDF"
                >
                  <Eye className="w-4 h-4" />
                </button>

                <button
                  onClick={() => handleDeleteClick(doc.doc_id)}
                  className="btn-secondary text-xs p-1.5 text-rose-400 hover:text-rose-300 hover:border-rose-500/50"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Delete Confirmation Overlay */}
              {deleteConfirmId === doc.doc_id && (
                <div className="mt-3 p-3 bg-[#171A1C] border border-rose-500/50 rounded text-xs space-y-2">
                  <p className="text-[#E0E3E5] font-medium">Delete this document and all vectors?</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => confirmDelete(doc.doc_id)}
                      className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded font-medium"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={() => setDeleteConfirmId(null)}
                      className="px-2.5 py-1 bg-[#303538] hover:bg-[#3d4347] text-[#BFC3C7] rounded"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
