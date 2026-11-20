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
  Code2,
  X,
  Copy,
  Check,
} from 'lucide-react';
import SampleDatasetCards from '../components/SampleDatasetCards';
import { reindexDocument, fetchCollections, fetchRawDocumentText } from '../services/api';

export default function DocumentLibrary({
  documents = [],
  onDeleteDocument,
  onViewDocument,
  onQueryDocument,
  onOpenUpload,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('all');
  const [selectedFormat, setSelectedFormat] = useState('all');
  const [selectedCollection, setSelectedCollection] = useState('all');
  const [collections, setCollections] = useState([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);

  // Raw text inspection state
  const [inspectingDoc, setInspectingDoc] = useState(null);
  const [inspectingData, setInspectingData] = useState(null);
  const [inspectingLoading, setInspectingLoading] = useState(false);
  const [copiedRaw, setCopiedRaw] = useState(false);

  useEffect(() => {
    fetchCollections()
      .then((data) => setCollections(data || []))
      .catch(() => setCollections([]));
  }, []);

  // Extract all distinct tags
  const allTags = ['all', ...new Set(documents.flatMap((d) => d.tags || []))];
  const allFormats = ['all', 'pdf', 'docx', 'txt', 'md', 'csv'];

  const filteredDocs = documents.filter((doc) => {
    const filename = (doc.filename || '').toLowerCase();
    const ext = filename.split('.').pop().toLowerCase();
    const matchesSearch = filename.includes(searchTerm.toLowerCase());
    const matchesTag = selectedTag === 'all' || (doc.tags && doc.tags.includes(selectedTag));
    const matchesFormat = selectedFormat === 'all' || ext === selectedFormat;
    return matchesSearch && matchesTag && matchesFormat;
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
        return { label: ext.toUpperCase() || 'DOC', bg: 'bg-[#22262B] text-[#A2A9B0] border-[#30353A]' };
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
        return <FileText className="w-5 h-5 text-[#F5C542]" />;
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

  const handleInspectRaw = async (doc) => {
    const docId = doc.doc_id || doc.id;
    setInspectingDoc(doc);
    setInspectingLoading(true);
    try {
      const data = await fetchRawDocumentText(docId);
      setInspectingData(data);
    } catch (err) {
      console.error('Failed to fetch raw text:', err);
      setInspectingData({ error: 'Failed to inspect extracted text.' });
    } finally {
      setInspectingLoading(false);
    }
  };

  const handleCopyRaw = () => {
    if (inspectingData?.raw_text) {
      navigator.clipboard.writeText(inspectingData.raw_text);
      setCopiedRaw(true);
      setTimeout(() => setCopiedRaw(false), 2000);
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
          <h2 className="text-xl font-bold text-[#F2F3F4] tracking-tight">
            Document Repository
          </h2>
          <p className="text-xs text-[#A2A9B0]">
            Manage multi-format research documents (PDF, DOCX, TXT, MD, CSV) indexed in ChromaDB and BM25.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#A2A9B0] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs w-48 sm:w-64 bg-[#17191B] border border-[#30353A] rounded-xl text-[#F2F3F4] placeholder-[#A2A9B0]/60 focus:border-[#F5C542] focus:outline-none"
            />
          </div>

          <button
            onClick={onOpenUpload}
            className="px-3.5 py-1.5 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] text-xs font-semibold rounded-xl shadow-sm flex items-center gap-1.5 transition"
          >
            <UploadCloud className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Upload Documents</span>
          </button>
        </div>
      </div>

      {/* Filter Badges & Formats */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {/* Format Filters */}
        <div className="flex items-center gap-1.5 mr-3">
          <span className="text-[11px] font-mono text-[#A2A9B0] uppercase mr-1">Format:</span>
          {allFormats.map((fmt) => (
            <button
              key={fmt}
              onClick={() => setSelectedFormat(fmt)}
              className={`px-2 py-0.5 rounded-lg uppercase font-mono text-[10px] transition ${
                selectedFormat === fmt
                  ? 'bg-[#F5C542] text-[#101214] font-bold shadow-sm'
                  : 'bg-[#17191B] border border-[#30353A] text-[#A2A9B0] hover:text-[#F2F3F4]'
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>

        {allTags.length > 1 && (
          <div className="flex items-center gap-1.5 border-l border-[#30353A] pl-3 mr-3">
            <Tag className="w-3 h-3 text-[#A2A9B0] mr-0.5 shrink-0" />
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag)}
                className={`px-2 py-0.5 rounded-lg capitalize font-mono text-[10px] transition ${
                  selectedTag === tag
                    ? 'bg-[#F5C542] text-[#101214] font-bold'
                    : 'bg-[#17191B] border border-[#30353A] text-[#A2A9B0] hover:text-[#F2F3F4]'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Empty State */}
      {filteredDocs.length === 0 ? (
        <div className="bg-[#17191B] border border-[#30353A] rounded-2xl p-10 space-y-6">
          <div className="text-center max-w-md mx-auto">
            <Files className="w-10 h-10 text-[#A2A9B0] mx-auto mb-3 opacity-40" />
            <h3 className="text-base font-semibold text-[#F2F3F4] mb-1">
              {searchTerm ? 'No documents match your query' : 'Your repository is empty'}
            </h3>
            <p className="text-xs text-[#A2A9B0] mb-4">
              Upload PDF, DOCX, TXT, MD, or CSV files or start exploring immediately with our curated sample datasets below.
            </p>
            <button
              onClick={onOpenUpload}
              className="px-4 py-2 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] font-bold rounded-xl text-xs transition"
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
                className="bg-[#17191B] border border-[#30353A] rounded-2xl p-5 flex flex-col justify-between hover:border-[#F5C542]/50 transition group shadow-sm"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-[#22262B] border border-[#30353A] flex items-center justify-center shrink-0">
                        {icon}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <h4 className="text-sm font-semibold text-[#F2F3F4] truncate group-hover:text-[#F5C542] transition">
                            {doc.filename}
                          </h4>
                          <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${badge.bg}`}>
                            {badge.label}
                          </span>
                        </div>
                        <span className="text-[10px] text-[#A2A9B0] font-mono">
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
                  <div className="grid grid-cols-3 gap-2 p-2 rounded-xl bg-[#22262B] border border-[#30353A]/60 text-center font-mono text-xs mb-4">
                    <div>
                      <span className="text-[10px] text-[#A2A9B0] block">PAGES</span>
                      <span className="text-[#F2F3F4] font-bold">{doc.page_count || 1}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#A2A9B0] block">CHUNKS</span>
                      <span className="text-[#F5C542] font-bold">{doc.total_chunks || 0}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[#A2A9B0] block">SIZE</span>
                      <span className="text-[#F2F3F4]">{formatFileSize(doc.file_size_bytes)}</span>
                    </div>
                  </div>

                  {/* Tags */}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {doc.tags.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-[#22262B] text-[#A2A9B0]"
                        >
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="pt-3 border-t border-[#30353A]/50 flex items-center justify-between gap-2">
                  <button
                    onClick={() => onQueryDocument && onQueryDocument(docId)}
                    className="flex-1 py-1.5 px-2 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 transition"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Ask AI</span>
                  </button>

                  <button
                    onClick={() => onViewDocument && onViewDocument(doc)}
                    className="p-1.5 text-[#A2A9B0] hover:text-[#F2F3F4] hover:bg-[#22262B] rounded-xl border border-[#30353A] transition"
                    title="Preview Document"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => handleInspectRaw(doc)}
                    className="p-1.5 text-[#A2A9B0] hover:text-[#F5C542] hover:bg-[#22262B] rounded-xl border border-[#30353A] transition"
                    title="Inspect Extracted Text & Chunks"
                  >
                    <Code2 className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => handleReindex(docId)}
                    disabled={reindexingId === docId}
                    className="p-1.5 text-[#A2A9B0] hover:text-[#F5C542] hover:bg-[#22262B] rounded-xl border border-[#30353A] transition disabled:opacity-40"
                    title="Re-index Document"
                  >
                    <RefreshCw className={`w-4 h-4 ${reindexingId === docId ? 'animate-spin' : ''}`} />
                  </button>

                  <button
                    onClick={() => setDeleteConfirmId(docId)}
                    className="p-1.5 text-[#A2A9B0] hover:text-rose-400 hover:bg-rose-950/30 rounded-xl border border-[#30353A] transition"
                    title="Delete Document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Delete Confirmation Modal / Popover */}
                {deleteConfirmId === docId && (
                  <div className="mt-3 p-3 bg-rose-950/40 border border-rose-800/80 rounded-xl space-y-2 animate-fade-in">
                    <p className="text-xs text-rose-200">
                      Purge from ChromaDB, BM25, and local disk?
                    </p>
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setDeleteConfirmId(null)}
                        className="px-2 py-1 text-[11px] text-[#A2A9B0] hover:text-[#F2F3F4]"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => confirmDelete(docId)}
                        className="px-2.5 py-1 text-[11px] bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg"
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

      {/* Raw Extracted Text Inspector Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#17191B] border border-[#30353A] rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-[#30353A] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="w-5 h-5 text-[#F5C542]" />
                <h3 className="text-sm font-bold text-[#F2F3F4]">
                  Extracted Raw Text & Chunks: {inspectingDoc.filename}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyRaw}
                  className="px-2.5 py-1 bg-[#22262B] hover:bg-[#30353A] text-xs font-mono text-[#A2A9B0] hover:text-[#F2F3F4] rounded-lg border border-[#30353A] flex items-center gap-1.5 transition"
                >
                  {copiedRaw ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedRaw ? 'Copied' : 'Copy All'}</span>
                </button>
                <button
                  onClick={() => {
                    setInspectingDoc(null);
                    setInspectingData(null);
                  }}
                  className="p-1 text-[#A2A9B0] hover:text-[#F2F3F4] rounded-lg hover:bg-[#22262B] transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-4 overflow-y-auto flex-1 space-y-4 font-mono text-xs">
              {inspectingLoading ? (
                <div className="py-12 text-center text-[#A2A9B0] flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-[#F5C542]" />
                  <span>Loading extracted chunks and structure...</span>
                </div>
              ) : inspectingData?.chunks ? (
                <div className="space-y-3">
                  <div className="p-3 bg-[#101214] rounded-xl border border-[#30353A] text-[11px] text-[#A2A9B0]">
                    Total Indexed Chunks: <span className="text-[#F5C542] font-bold">{inspectingData.chunks.length}</span>
                  </div>
                  {inspectingData.chunks.map((chk, i) => (
                    <div key={i} className="p-3 bg-[#101214] rounded-xl border border-[#30353A] space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] text-[#A2A9B0] border-b border-[#30353A]/40 pb-1">
                        <span>Chunk #{chk.chunk_index} (Page {chk.page_number || 1})</span>
                        {chk.section_heading && <span className="text-[#F5C542] font-semibold">{chk.section_heading}</span>}
                      </div>
                      <p className="text-[11px] text-[#F2F3F4] font-sans whitespace-pre-wrap leading-relaxed">
                        {chk.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-rose-400">
                  {inspectingData?.error || 'No extracted chunks found for this document.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
