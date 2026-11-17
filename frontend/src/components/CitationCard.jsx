import React, { useState } from 'react';
import {
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Percent,
} from 'lucide-react';

export default function CitationCard({ citation, index, onOpenPage }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const relevancePercentage = Math.round((citation.relevance_score || 0) * 100);

  return (
    <div className="bg-[#202326] border border-[#555C61] rounded-md overflow-hidden text-xs">
      {/* Citation Header Bar */}
      <div className="p-2.5 flex items-center justify-between gap-2 bg-[#171A1C]">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono font-bold text-[#F4D21F] bg-[#292D30] border border-[#555C61] px-1.5 py-0.5 rounded text-[10px]">
            Source {index + 1}
          </span>
          <span className="text-[#E0E3E5] font-medium truncate" title={citation.filename}>
            {citation.filename}
          </span>
          <span className="text-[#969DA3] font-mono text-[11px] shrink-0">
            (Page {citation.page_number})
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#202326] border border-[#F4D21F]/40 text-[#F4D21F]"
            title={`Relevance Score: ${citation.relevance_score}`}
          >
            {relevancePercentage}% match
          </span>

          {onOpenPage && (
            <button
              onClick={() => onOpenPage(citation.filename, citation.page_number)}
              className="text-[#969DA3] hover:text-[#F4D21F] p-1 rounded hover:bg-[#202326] transition-colors"
              title="Open cited page in Document Viewer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[#969DA3] hover:text-[#E0E3E5] p-1 rounded hover:bg-[#202326]"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Passage Excerpt */}
      <div className="p-3 text-[#BFC3C7] font-mono text-[11px] leading-relaxed border-t border-[#555C61]/40 bg-[#202326]">
        {isExpanded ? (
          <div className="whitespace-pre-wrap">{citation.content}</div>
        ) : (
          <div className="line-clamp-2">{citation.content}</div>
        )}
      </div>
    </div>
  );
}
