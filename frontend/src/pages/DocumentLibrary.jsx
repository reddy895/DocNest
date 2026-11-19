import React, { useState, useEffect } from 'react';
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
  Folder,
  FileCode,
  FileSpreadsheet,
  FileCheck,
} from 'lucide-react';
import SampleDatasetCards from '../components/SampleDatasetCards';
import { reindexDocument, fetchCollections } from '../services/api';

export default function DocumentLibrary({
  documents = [],
  onDeleteDocument,
  onViewDocument,
  onQueryDocument,
  onOpenUpload,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('all');
  const [selectedCollection, setSelectedCollection] = useState('all');
  const [collections, setCollections] = useState([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);

  useEffect(() => {
    fetchCollections()
      .then((data) => setCollections(data || []))
      .catch(() => setCollections([]));
  }, []);

  // Extract all distinct tags
  const allTags = ['all', ...new Set(documents.flatMap((d) => d.tags || []))];

  const filteredDocs = documents.filter((doc) => {
    const filename = (doc.filename || '').toLowerCase();
    const matchesSearch = filename.includes(searchTerm.toLowerCase());
    const matchesTag = selectedTag === 'all' || (doc.tags && doc.tags.includes(selectedTag));
    return matchesSearch && matchesTag;
  });

  const getFormatBadge = (filename = '') => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf':
        return { label: 'PDF', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
      case 'docx':
        return { label: 'DOCX', bg: 'bg-sky-500/10 text-sky-400 border-sky-500/30' };
      case 'csv':
        return { label: 'CSV', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
      case 'md':
        return { label: 'MD', bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30' };
      case 'txt':
        return { label: 'TXT', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      default:
        return { label: ext.toUpperCase() || 'DOC', bg: 'bg-[#22262A] text-[#A0A6AC] border-[#343A3F]' };
    }
  };

  const getFormatIcon = (filename = '') => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5 text-amber-400" />;
      case 'md':
        return <FileCode className="w-5 h-5 text-purple-400" />;
      default:
        return <FileText className="w-5 h-5 text-[#E5B83D]" />;
    }
  };

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
          <h2 className="text-xl font-bold text-[#F0F1F2] tracking-tight">
            Document Repository
          </h2>
          <p className="text-xs text-[#A0A6AC]">
            Manage multi-format research documents (PDF, DOCX, TXT, MD, CSV) indexed in ChromaDB and BM25.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#A0A6AC] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs w-48 sm:w-64 bg-[#191C1F] border border-[#343A3F] rounded-lg text-[#F0F1F2] placeholder-[#A0A6AC]/60 focus:border-[#E5B83D] focus:outline-none"
            />
          </div>

          <button
            onClick={onOpenUpload}
            className="px-3.5 py-1.5 bg-[#E5B83D] hover:bg-[#F2C64B] text-[#111315] text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 transition"
          >
            <UploadCloud className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Upload Documents</span>
          </button>
        </div>
      </div>

      {/* Filter Tags & Collections */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {allTags.length > 1 && (
          <div className="flex items-center gap-1.5 mr-3">
            <Tag className="w-3.5 h-3.5 text-[#A0A6AC] mr-0.5 shrink-0" />
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag)}
                className={`px-2.5 py-1 rounded-md capitalize font-mono text-[11px] transition ${
                  selectedTag === tag
                    ? 'bg-[#E5B83D] text-[#111315] font-bold'
                    : 'bg-[#191C1F] border border-[#343A3F] text-[#A0A6AC] hover:text-[#F0F1F2]'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}

        {collections.length > 0 && (
          <div className="flex items-center gap-1.5 border-l border-[#343A3F] pl-3">
            <Folder className="w-3.5 h-3.5 text-[#A0A6AC] mr-0.5 shrink-0" />
            <button
              onClick={() => setSelectedCollection('all')}
              className={`px-2.5 py-1 rounded-md text-[11px] transition ${
                selectedCollection === 'all'
                  ? 'bg-[#22262A] text-[#F0F1F2] border border-[#343A3F]'
                  : 'text-[#A0A6AC] hover:text-[#F0F1F2]'
              }`}
            >
              All Binders
            </button>
            {collections.map((col) => (
              <button
                key={col.id}
                onClick={() => setSelectedCollection(col.id)}
                className={`px-2.5 py-1 rounded-md text-[11px] transition flex items-center gap-1 ${
                  selectedCollection === col.id
                    ? 'bg-[#E5B83D] text-[#111315] font-bold'
                    : 'bg-[#191C1F] border border-[#343A3F] text-[#A0A6AC] hover:text-[#F0F1F2]'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: col.color || '#E5B83D' }} />
                <span>{col.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Empty State */}
      {filteredDocs.length === 0 ? (
        <div className="bg-[#191C1F] border border-[#343A3F] rounded-xl p-10 space-y-6">
          <div className="text-center max-w-md mx-auto">
            <Files className="w-10 h-10 text-[#A0A6AC] mx-auto mb-3 opacity-40" />
            <h3 className="text-base font-semibold text-[#F0F1F2] mb-1">
              {searchTerm ? 'No documents match your query' : 'Your repository is empty'}
            </h3>
            <p className="text-xs text-[#A0A6AC] mb-4">
              Upload PDF, DOCX, TXT, MD, or CSV files or start exploring immediately with our curated sample datasets below.
            </p>
            <button
              onClick={onOpenUpload}
              className="px-4 py-2 bg-[#E5B83D] hover:bg-[#F2C64B] text-[#111315] font-semibold rounded-lg text-xs transition"
            >
              Upload Documents
            </button>
          </div>

          <SampleDatasetCards onSampleLoaded={() => window.location.reload()} />
        </div>
      ) : (
        /* Document Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => {
            const docId = doc.doc_id || doc.id;
            const badge = getFormatBadge(doc.filename);
            const icon = getFormatIcon(doc.filename);

            return (
              <div
                key={docId}
                className="bg-[#191C1F] border border-[#343A3F] rounded-xl p-5 flex flex-col justify-between hover:border-[#E5B83D]/50 transition group shadow-sm"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-[#22262A] border border-[#343A3F] flex items-center justify-center shrink-0">
                        {icon}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <h4 className="text-sm font-semibold text-[#F0F1F2] truncate group-hover:text-[#E5B83D] transition">
                            {doc.filename}
                          </h4>
                          <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${badge.bg}`}>
                            {badge.label}
                          </span>
                        </div>
                        <span className="text-[10px] text-[#A0A6AC] font-mono">
                          {formatDate(doc.created_at || doc.upload_date)}
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
                  <div className="grid grid-cols-3 gap-2 p-2 rounded-lg bg-[#22262A] border border-[#343A3F]/60 text-center font-mono text-xs mb-4">
                    <div>
                      <span className="text-[10px] text-[#A0A6AC] block">PAGES</span>
                      <span className="text-[#F0F1F2] font-bold">{doc.page_count || 1}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#A0A6AC] block">CHUNKS</span>
                      <span className="text-[#E5B83D] font-bold">{doc.total_chunks || 0}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#A0A6AC] block">SIZE</span>
                      <span className="text-[#F0F1F2]">{formatFileSize(doc.file_size_bytes)}</span>
                    </div>
                  </div>

                  {/* Tags */}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {doc.tags.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#22262A] text-[#A0A6AC]"
                        >
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="pt-3 border-t border-[#343A3F]/50 flex items-center justify-between gap-2">
                  <button
                    onClick={() => onQueryDocument && onQueryDocument(docId)}
                    className="flex-1 py-1.5 px-2 bg-[#E5B83D] hover:bg-[#F2C64B] text-[#111315] font-semibold text-xs rounded-lg flex items-center justify-center gap-1.5 transition"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Ask AI</span>
                  </button>

                  <button
                    onClick={() => onViewDocument && onViewDocument(doc)}
                    className="p-1.5 text-[#A0A6AC] hover:text-[#F0F1F2] hover:bg-[#22262A] rounded-lg border border-[#343A3F] transition"
                    title="Preview Document"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => handleReindex(docId)}
                    disabled={reindexingId === docId}
                    className="p-1.5 text-[#A0A6AC] hover:text-[#E5B83D] hover:bg-[#22262A] rounded-lg border border-[#343A3F] transition disabled:opacity-40"
                    title="Re-index Document"
                  >
                    <RefreshCw className={`w-4 h-4 ${reindexingId === docId ? 'animate-spin' : ''}`} />
                  </button>

                  <button
                    onClick={() => setDeleteConfirmId(docId)}
                    className="p-1.5 text-[#A0A6AC] hover:text-rose-400 hover:bg-rose-950/30 rounded-lg border border-[#343A3F] transition"
                    title="Delete Document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Delete Confirmation Modal / Popover */}
                {deleteConfirmId === docId && (
                  <div className="mt-3 p-3 bg-rose-950/40 border border-rose-800/80 rounded-lg space-y-2 animate-fade-in">
                    <p className="text-xs text-rose-200">
                      Purge from ChromaDB, BM25, and local disk?
                    </p>
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setDeleteConfirmId(null)}
                        className="px-2 py-1 text-[11px] text-[#A0A6AC] hover:text-[#F0F1F2]"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => confirmDelete(docId)}
                        className="px-2.5 py-1 text-[11px] bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded"
                      >
                        Confirm Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
