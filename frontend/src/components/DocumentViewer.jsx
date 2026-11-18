import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Copy,
  Check,
  BookOpen,
  Hash,
} from 'lucide-react';

export default function DocumentViewer({
  document,
  initialPage = 1,
  highlightText = '',
  sectionHeading = '',
  relevanceScore = null,
  onClose,
}) {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setCurrentPage(initialPage);
  }, [initialPage]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onClose) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!document) return null;

  const pdfUrl = `/api/documents/${document.doc_id}/file#page=${currentPage}`;

  const handleCopy = () => {
    if (highlightText) {
      navigator.clipboard.writeText(highlightText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-carbon-deep/85 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-6xl h-[92vh] flex flex-col bg-carbon-surface border border-silver-border rounded-xl shadow-carbon-lg overflow-hidden">
        {/* Header Bar */}
        <div className="h-14 bg-carbon-deep border-b border-silver-border px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-carbon-primary border border-silver-border flex items-center justify-center shrink-0 text-signal-yellow">
              <FileText className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-silver-light truncate">
                {document.filename}
              </h3>
              <p className="text-[11px] text-silver-secondary font-mono">
                {document.page_count} Pages • {document.total_chunks || 0} Vector Chunks
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Page Jumping Controls */}
            <div className="flex items-center gap-1 bg-carbon-primary border border-silver-border px-2.5 py-1 rounded-lg text-xs font-mono">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="text-silver-secondary hover:text-silver-light disabled:opacity-30 p-0.5"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-silver-light px-1 font-bold">
                Page {currentPage} of {document.page_count}
              </span>
              <button
                disabled={currentPage >= document.page_count}
                onClick={() => setCurrentPage((p) => Math.min(document.page_count, p + 1))}
                className="text-silver-secondary hover:text-silver-light disabled:opacity-30 p-0.5"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <a
              href={`/api/documents/${document.doc_id}/file`}
              target="_blank"
              rel="noopener noreferrer"
              download={document.filename}
              className="p-1.5 text-silver-secondary hover:text-silver-light hover:bg-carbon-secondary rounded-lg border border-silver-border transition"
              title="Download PDF"
            >
              <Download className="w-4 h-4" />
            </a>

            <button
              onClick={onClose}
              className="p-1.5 text-silver-secondary hover:text-silver-light hover:bg-carbon-secondary rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Side-by-Side Split Body */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden bg-carbon-primary">
          {/* Left Canvas: Embedded PDF */}
          <div className="flex-1 h-1/2 md:h-full bg-carbon-deep relative border-b md:border-b-0 md:border-r border-silver-border">
            <iframe
              src={pdfUrl}
              title={document.filename}
              className="w-full h-full border-none"
            />
          </div>

          {/* Right Panel: Cited Passage & Evidence Inspector */}
          <div className="w-full md:w-96 h-1/2 md:h-full bg-carbon-surface flex flex-col shrink-0 overflow-y-auto p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-silver-border">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-signal-yellow" />
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-silver-light">
                  Cited Source Evidence
                </h4>
              </div>
              {relevanceScore !== null && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-800/40 font-bold">
                  {Math.round(relevanceScore * 100)}% Match
                </span>
              )}
            </div>

            {sectionHeading && (
              <div className="p-2.5 rounded-lg bg-carbon-primary border border-silver-border/60 flex items-center gap-2 text-xs font-mono text-silver-light">
                <Hash className="w-3.5 h-3.5 text-signal-yellow shrink-0" />
                <span className="truncate">{sectionHeading}</span>
              </div>
            )}

            {highlightText ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-silver-secondary font-mono">
                  <span>Exact Cited Segment (p. {currentPage}):</span>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 text-silver-secondary hover:text-silver-light transition"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                <div className="p-4 rounded-xl bg-carbon-primary border-l-4 border-signal-yellow text-silver-light text-xs font-sans leading-relaxed shadow-carbon-sm whitespace-pre-wrap">
                  {highlightText}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-silver-secondary italic bg-carbon-primary rounded-xl border border-dashed border-silver-border">
                Viewing page {currentPage}. Highlighted excerpt will appear here when opened from an answer citation.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
