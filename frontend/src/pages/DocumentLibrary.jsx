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
  Tag,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import SampleDatasetCards from '../components/SampleDatasetCards';
import { reindexDocument } from '../services/api';

export default function DocumentLibrary({
  documents = [],
  onDeleteDocument,
  onViewDocument,
  onQueryDocument,
  onOpenUpload,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('all');
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);

  // Extract all distinct tags
  const allTags = ['all', ...new Set(documents.flatMap((d) => d.tags || []))];

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTag = selectedTag === 'all' || (doc.tags && doc.tags.includes(selectedTag));
    return matchesSearch && matchesTag;
  });

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

  const handleReindex = async (docId) => {
    setReindexingId(docId);
    try {
      await reindexDocument(docId);
      window.location.reload();
    } catch (err) {
      console.error('Reindex failed:', err);
    } finally {
      setReindexingId(null);
    }
  };

  const confirmDelete = async (docId) => {
    if (onDeleteDocument) {
      await onDeleteDocument(docId);
    }
    setDeleteConfirmId(null);
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-silver-light tracking-tight">
            Document Repository
          </h2>
          <p className="text-xs text-silver-secondary">
            Manage all layout-aware indexed PDF documents, inspect metadata, or launch chat.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-silver-secondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs w-48 sm:w-64 bg-carbon-surface border border-silver-border rounded-lg text-silver-light placeholder-silver-secondary/50 focus:border-signal-yellow focus:outline-none"
            />
          </div>

          <button
            onClick={onOpenUpload}
            className="px-3.5 py-1.5 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg shadow-carbon-sm flex items-center gap-1.5 transition"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        </div>
      </div>

      {/* Filter Tags */}
      {allTags.length > 1 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <Tag className="w-3.5 h-3.5 text-silver-secondary mr-1 shrink-0" />
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setSelectedTag(tag)}
              className={`px-2.5 py-1 rounded-md capitalize font-mono text-[11px] transition ${
                selectedTag === tag
                  ? 'bg-signal-yellow text-carbon-deep font-bold'
                  : 'bg-carbon-surface border border-silver-border text-silver-secondary hover:text-silver-light'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Empty State */}
      {filteredDocs.length === 0 ? (
        <div className="bg-carbon-surface border border-silver-border rounded-xl p-10 space-y-6">
          <div className="text-center max-w-md mx-auto">
            <Files className="w-10 h-10 text-silver-secondary mx-auto mb-3 opacity-40" />
            <h3 className="text-base font-semibold text-silver-light mb-1">
              {searchTerm ? 'No documents match your query' : 'Your repository is empty'}
            </h3>
            <p className="text-xs text-silver-secondary mb-4">
              Upload institutional PDF documents or start exploring immediately with our curated sample datasets below.
            </p>
            <button
              onClick={onOpenUpload}
              className="px-4 py-2 bg-signal-yellow text-carbon-deep font-semibold rounded-lg text-xs"
            >
              Upload PDF
            </button>
          </div>

          <SampleDatasetCards onSampleLoaded={() => window.location.reload()} />
        </div>
      ) : (
        /* Document Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => (
            <div
              key={doc.doc_id}
              className="bg-carbon-surface border border-silver-border rounded-xl p-5 flex flex-col justify-between hover:border-signal-yellow/50 transition group shadow-carbon-sm"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-9 h-9 rounded-lg bg-carbon-primary border border-silver-border flex items-center justify-center shrink-0 text-signal-yellow">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-silver-light truncate group-hover:text-signal-yellow transition">
                        {doc.filename}
                      </h4>
                      <span className="text-[10px] text-silver-secondary font-mono">
                        {formatDate(doc.upload_date)}
                      </span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase shrink-0 ${
                      doc.status === 'ready' || doc.status === 'indexed' || doc.status === 'already_indexed'
                        ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                        : 'bg-amber-950/40 text-amber-400 border-amber-800/40'
                    }`}
                  >
                    {doc.status || 'READY'}
                  </span>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-3 gap-2 p-2 rounded-lg bg-carbon-primary border border-silver-border/40 text-center font-mono text-xs mb-4">
                  <div>
                    <span className="text-[10px] text-silver-secondary block">PAGES</span>
                    <span className="text-silver-light font-bold">{doc.page_count}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-silver-secondary block">CHUNKS</span>
                    <span className="text-signal-yellow font-bold">{doc.total_chunks}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-silver-secondary block">SIZE</span>
                    <span className="text-silver-light">{formatFileSize(doc.file_size_bytes)}</span>
                  </div>
                </div>

                {/* Tags */}
                {doc.tags && doc.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {doc.tags.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-carbon-secondary text-silver-secondary"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-silver-border/50 flex items-center justify-between gap-2">
                <button
                  onClick={() => onQueryDocument && onQueryDocument(doc)}
                  className="flex-1 py-1.5 px-2 bg-signal-yellow hover:bg-signal-hover text-carbon-deep font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 transition"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Ask AI</span>
                </button>

                <button
                  onClick={() => onViewDocument && onViewDocument(doc)}
                  className="p-1.5 text-silver-secondary hover:text-silver-light hover:bg-carbon-secondary rounded-lg border border-silver-border transition"
                  title="Preview PDF"
                >
                  <Eye className="w-4 h-4" />
                </button>

                <button
                  onClick={() => handleReindex(doc.doc_id)}
                  disabled={reindexingId === doc.doc_id}
                  className="p-1.5 text-silver-secondary hover:text-signal-yellow hover:bg-carbon-secondary rounded-lg border border-silver-border transition disabled:opacity-40"
                  title="Re-index Document"
                >
                  <RefreshCw className={`w-4 h-4 ${reindexingId === doc.doc_id ? 'animate-spin' : ''}`} />
                </button>

                <button
                  onClick={() => setDeleteConfirmId(doc.doc_id)}
                  className="p-1.5 text-silver-secondary hover:text-red-400 hover:bg-red-950/30 rounded-lg border border-silver-border transition"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Delete Confirmation Modal / Popover */}
              {deleteConfirmId === doc.doc_id && (
                <div className="mt-3 p-3 bg-red-950/40 border border-red-800/80 rounded-lg space-y-2 animate-fade-in">
                  <p className="text-xs text-red-200">
                    Purge from ChromaDB, BM25, and local disk?
                  </p>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setDeleteConfirmId(null)}
                      className="px-2 py-1 text-[11px] text-silver-secondary hover:text-silver-light"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => confirmDelete(doc.doc_id)}
                      className="px-2.5 py-1 text-[11px] bg-red-600 hover:bg-red-700 text-white font-semibold rounded"
                    >
                      Confirm Delete
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
