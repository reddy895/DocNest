import React, { useState, useEffect } from 'react';
import {
  Files,
  Search,
  Trash2,
  Eye,
  MessageSquare,
  UploadCloud,
  FileText,
  RefreshCw,
  FileCode,
  FileSpreadsheet,
  Code2,
  X,
  Copy,
  Check,
  Edit2,
} from 'lucide-react';
import SampleDatasetCards from '../../components/documents/SampleDatasetCards';
import {
  reindexDocument,
  fetchRawDocumentText,
  updateDocumentMetadata,
} from '../../services/api';

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
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);

  // Rename state
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [localNames, setLocalNames] = useState({});

  // Raw text inspection state
  const [inspectingDoc, setInspectingDoc] = useState(null);
  const [inspectingData, setInspectingData] = useState(null);
  const [inspectingLoading, setInspectingLoading] = useState(false);
  const [copiedRaw, setCopiedRaw] = useState(false);

  const allTags = ['all', ...new Set(documents.flatMap((d) => d.tags || []))];
  const allFormats = ['all', 'pdf', 'docx', 'txt', 'md', 'csv'];

  const filteredDocs = documents.filter((doc) => {
    const docId = doc.doc_id || doc.id;
    const filename = (localNames[docId] || doc.filename || '').toLowerCase();
    const ext = filename.split('.').pop().toLowerCase();
    const matchesSearch = filename.includes(searchTerm.toLowerCase());
    const matchesTag = selectedTag === 'all' || (doc.tags && doc.tags.includes(selectedTag));
    const matchesFormat = selectedFormat === 'all' || ext === selectedFormat;
    return matchesSearch && matchesTag && matchesFormat;
  });

  const getFormatIcon = (filename = '') => {
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'csv') return <FileSpreadsheet className="h-4 w-4 text-[#A1A1A1]" />;
    if (ext === 'md') return <FileCode className="h-4 w-4 text-[#A1A1A1]" />;
    return <FileText className="h-4 w-4 text-[#A1A1A1]" />;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Recent';
    try {
      return new Date(isoString).toLocaleDateString(undefined, {
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

  const handleSaveRename = async (docId) => {
    const trimmed = renameValue.trim();
    if (!trimmed) {
      setRenamingId(null);
      return;
    }
    try {
      await updateDocumentMetadata(docId, { filename: trimmed });
      setLocalNames((prev) => ({ ...prev, [docId]: trimmed }));
    } catch (err) {
      console.error('Rename failed:', err);
    } finally {
      setRenamingId(null);
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
      setTimeout(() => setCopiedRaw(false), 1800);
    }
  };

  const confirmDelete = async (docId) => {
    if (onDeleteDocument) {
      await onDeleteDocument(docId);
    }
    setDeleteConfirmId(null);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#212121] text-[#ECECEC]">
      <div className="mx-auto max-w-5xl space-y-6 p-6 md:p-8">
        {/* Header & Search */}
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-[#ECECEC]">
              Document library
            </h1>
            <p className="mt-1 text-xs text-[#A1A1A1]">
              Manage uploaded PDF, DOCX, TXT, MD, and CSV files for grounded AI research.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#777777]" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-44 rounded-lg border border-[#3A3A3A] bg-[#303030] py-1.5 pl-8 pr-3 text-xs text-[#ECECEC] placeholder-[#777777] focus:border-[#555555] focus:outline-none sm:w-60"
              />
            </div>

            <button
              type="button"
              onClick={onOpenUpload}
              className="flex items-center gap-1.5 rounded-lg bg-[#F0F0F0] px-3.5 py-1.5 text-xs font-medium text-[#171717] transition-colors hover:bg-white"
            >
              <UploadCloud className="h-3.5 w-3.5" />
              <span>Upload</span>
            </button>
          </div>
        </div>

        {/* Compact Format & Tag Filters */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {allFormats.map((fmt) => (
            <button
              key={fmt}
              type="button"
              onClick={() => setSelectedFormat(fmt)}
              className={`rounded-full px-2.5 py-1 text-[11px] font-medium uppercase transition-colors ${
                selectedFormat === fmt
                  ? 'bg-[#ECECEC] text-[#171717]'
                  : 'border border-[#3A3A3A] bg-[#2A2A2A] text-[#A1A1A1] hover:bg-[#2F2F2F] hover:text-[#ECECEC]'
              }`}
            >
              {fmt}
            </button>
          ))}

          {allTags.length > 1 && (
            <div className="ml-2 flex flex-wrap items-center gap-1.5 border-l border-[#3A3A3A] pl-3">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => setSelectedTag(tag)}
                  className={`rounded-full px-2.5 py-1 text-[11px] capitalize transition-colors ${
                    selectedTag === tag
                      ? 'bg-[#ECECEC] text-[#171717]'
                      : 'border border-[#3A3A3A] bg-[#2A2A2A] text-[#A1A1A1] hover:bg-[#2F2F2F] hover:text-[#ECECEC]'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Empty State or Compact Rows List */}
        {filteredDocs.length === 0 ? (
          <div className="space-y-6 rounded-2xl border border-[#3A3A3A] bg-[#171717]/60 p-10">
            <div className="mx-auto max-w-md text-center">
              <Files className="mx-auto mb-3 h-8 w-8 text-[#777777]" />
              <h3 className="mb-1 text-sm font-semibold text-[#ECECEC]">
                {searchTerm ? 'No matching documents' : 'No documents uploaded yet'}
              </h3>
              <p className="mb-4 text-xs text-[#A1A1A1]">
                Upload PDF, DOCX, TXT, MD, or CSV files or try a sample dataset below.
              </p>
              <button
                type="button"
                onClick={onOpenUpload}
                className="rounded-lg bg-[#F0F0F0] px-4 py-2 text-xs font-medium text-[#171717] transition-colors hover:bg-white"
              >
                Upload documents
              </button>
            </div>

            <SampleDatasetCards onSampleLoaded={() => window.location.reload()} />
          </div>
        ) : (
          <div className="divide-y divide-[#2E2E2E] overflow-hidden rounded-2xl border border-[#3A3A3A] bg-[#171717]/40">
            {filteredDocs.map((doc) => {
              const docId = doc.doc_id || doc.id;
              const displayName = localNames[docId] || doc.filename;
              const ext = (displayName.split('.').pop() || 'doc').toUpperCase();
              const isReady =
                doc.status === 'ready' ||
                doc.status === 'indexed' ||
                doc.status === 'already_indexed';

              return (
                <div
                  key={docId}
                  className="flex flex-col gap-3 px-4 py-3.5 transition-colors hover:bg-[#2A2A2A]/50 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border border-[#3A3A3A] bg-[#2A2A2A]">
                      {getFormatIcon(displayName)}
                    </div>

                    <div className="min-w-0 flex-1">
                      {renamingId === docId ? (
                        <div className="flex items-center gap-1.5">
                          <input
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveRename(docId);
                              if (e.key === 'Escape') setRenamingId(null);
                            }}
                            autoFocus
                            className="w-full max-w-xs rounded border border-[#3A3A3A] bg-[#303030] px-2 py-0.5 text-sm text-[#ECECEC] focus:outline-none"
                          />
                          <button
                            type="button"
                            onClick={() => handleSaveRename(docId)}
                            className="rounded p-1 text-[#A1A1A1] hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
                            aria-label="Save name"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setRenamingId(null)}
                            className="rounded p-1 text-[#A1A1A1] hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
                            aria-label="Cancel rename"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <h4 className="truncate text-sm font-medium text-[#ECECEC]">
                            {displayName}
                          </h4>
                          <span className="rounded border border-[#3A3A3A] bg-[#2A2A2A] px-1.5 py-0.2 font-mono text-[10px] text-[#A1A1A1]">
                            {ext}
                          </span>
                          <span
                            className={`rounded-full px-2 py-0.2 text-[10px] font-medium ${
                              isReady
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-[#2A2A2A] text-[#A1A1A1]'
                            }`}
                          >
                            {doc.status || 'ready'}
                          </span>
                        </div>
                      )}

                      <div className="mt-0.5 flex flex-wrap items-center gap-3 text-[11px] text-[#777777]">
                        <span>{doc.page_count || 1} pages</span>
                        <span>{doc.total_chunks || 0} chunks</span>
                        <span>{formatFileSize(doc.file_size_bytes)}</span>
                        <span>{formatDate(doc.created_at || doc.upload_date)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Row Actions */}
                  <div className="flex flex-shrink-0 items-center gap-1.5">
                    {deleteConfirmId === docId ? (
                      <div className="flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-2.5 py-1">
                        <span className="text-[11px] text-rose-200">Delete?</span>
                        <button
                          type="button"
                          onClick={() => confirmDelete(docId)}
                          className="rounded bg-rose-600 px-2 py-0.5 text-[11px] font-medium text-white hover:bg-rose-700"
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-1.5 py-0.5 text-[11px] text-[#A1A1A1] hover:text-[#ECECEC]"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => onQueryDocument && onQueryDocument(docId)}
                          className="flex items-center gap-1.5 rounded-lg bg-[#F0F0F0] px-3 py-1.5 text-xs font-medium text-[#171717] transition-colors hover:bg-white"
                        >
                          <MessageSquare className="h-3.5 w-3.5" />
                          <span>Ask</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => onViewDocument && onViewDocument(doc)}
                          className="rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                          title="Preview document"
                          aria-label="Preview document"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInspectRaw(doc)}
                          className="rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                          title="Inspect extracted text"
                          aria-label="Inspect extracted text"
                        >
                          <Code2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setRenamingId(docId);
                            setRenameValue(displayName);
                          }}
                          className="rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                          title="Rename document"
                          aria-label="Rename document"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleReindex(docId)}
                          disabled={reindexingId === docId}
                          className="rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC] disabled:opacity-40"
                          title="Re-index document"
                          aria-label="Re-index document"
                        >
                          <RefreshCw className={`h-3.5 w-3.5 ${reindexingId === docId ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteConfirmId(docId)}
                          className="rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-rose-500/10 hover:text-rose-400"
                          title="Delete document"
                          aria-label="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Raw Extracted Text Inspector Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 animate-fade-in">
          <div className="flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-[#3A3A3A] bg-[#212121]">
            <div className="flex items-center justify-between border-b border-[#3A3A3A] px-4 py-3">
              <div className="flex items-center gap-2">
                <Code2 className="h-4 w-4 text-[#A1A1A1]" />
                <h3 className="text-sm font-semibold text-[#ECECEC]">
                  Extracted text & chunks: {inspectingDoc.filename}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopyRaw}
                  className="flex items-center gap-1.5 rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] px-2.5 py-1 text-xs text-[#A1A1A1] transition-colors hover:text-[#ECECEC]"
                >
                  {copiedRaw ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copiedRaw ? 'Copied' : 'Copy all'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInspectingDoc(null);
                    setInspectingData(null);
                  }}
                  className="rounded-lg p-1 text-[#A1A1A1] hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                  aria-label="Close modal"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 space-y-3 overflow-y-auto p-4 text-xs">
              {inspectingLoading ? (
                <div className="flex items-center justify-center gap-2 py-12 text-[#A1A1A1]">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Loading extracted chunks...</span>
                </div>
              ) : inspectingData?.chunks ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-[#3A3A3A] bg-[#171717] p-3 text-[11px] text-[#A1A1A1]">
                    Total indexed chunks:{' '}
                    <span className="font-semibold text-[#ECECEC]">{inspectingData.chunks.length}</span>
                  </div>
                  {inspectingData.chunks.map((chk, i) => (
                    <div key={i} className="space-y-1.5 rounded-xl border border-[#3A3A3A] bg-[#171717] p-3">
                      <div className="flex items-center justify-between border-b border-[#2E2E2E] pb-1 font-mono text-[10px] text-[#A1A1A1]">
                        <span>
                          Chunk #{chk.chunk_index} (Page {chk.page_number || 1})
                        </span>
                        {chk.section_heading && (
                          <span className="font-medium text-[#ECECEC]">{chk.section_heading}</span>
                        )}
                      </div>
                      <p className="whitespace-pre-wrap text-xs leading-relaxed text-[#ECECEC]">
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
