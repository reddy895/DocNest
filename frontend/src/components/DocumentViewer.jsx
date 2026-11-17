import React, { useState } from 'react';
import {
  X,
  FileText,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Maximize2,
} from 'lucide-react';

export default function DocumentViewer({ document, initialPage = 1, onClose }) {
  const [currentPage, setCurrentPage] = useState(initialPage);

  if (!document) return null;

  const pdfUrl = `/api/documents/${document.doc_id}/file#page=${currentPage}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/85 backdrop-blur-sm">
      <div className="carbon-card w-full max-w-5xl h-[92vh] flex flex-col shadow-carbon-lg overflow-hidden border border-[#555C61]">
        {/* Viewer Header */}
        <div className="h-14 bg-[#171A1C] border-b border-[#555C61] px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded bg-[#202326] border border-[#555C61] flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4 text-[#F4D21F]" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-[#E0E3E5] truncate">
                {document.filename}
              </h3>
              <p className="text-[11px] text-[#969DA3] font-mono">
                {document.page_count} Pages • {document.total_chunks} Vector Chunks
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Page Jumping Controls */}
            <div className="flex items-center gap-1 bg-[#202326] border border-[#555C61] px-2 py-1 rounded text-xs font-mono">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="text-[#969DA3] hover:text-[#E0E3E5] disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-[#E0E3E5] px-1">
                Page {currentPage} of {document.page_count}
              </span>
              <button
                disabled={currentPage >= document.page_count}
                onClick={() => setCurrentPage((p) => Math.min(document.page_count, p + 1))}
                className="text-[#969DA3] hover:text-[#E0E3E5] disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <a
              href={`/api/documents/${document.doc_id}/file`}
              target="_blank"
              rel="noopener noreferrer"
              download={document.filename}
              className="btn-secondary text-xs py-1 px-2.5"
              title="Download PDF"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download</span>
            </a>

            <button
              onClick={onClose}
              className="p-1.5 rounded text-[#969DA3] hover:text-[#E0E3E5] hover:bg-[#202326]"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Embedded PDF Canvas */}
        <div className="flex-1 bg-[#202326] relative">
          <iframe
            src={pdfUrl}
            title={document.filename}
            className="w-full h-full border-none"
          />
        </div>
      </div>
    </div>
  );
}

