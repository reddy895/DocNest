import React, { useState } from 'react';
import {
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Hash,
  Sparkles,
} from 'lucide-react';

export default function CitationCard({ citation, index, onOpenPage, onSelect }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const relevancePct = Math.round((citation.relevance_score || 0.5) * 100);

  const getScoreBadge = (score) => {
    if (score >= 80) {
      return 'bg-emerald-950/40 text-emerald-400 border-emerald-800/50';
    } else if (score >= 50) {
      return 'bg-signal-yellow/10 text-signal-yellow border-signal-yellow/40';
    }
    return 'bg-carbon-primary text-silver-secondary border-silver-border';
  };

  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      onClick={() => onSelect && onSelect(citation)}
      className="bg-carbon-surface border border-silver-border rounded-xl overflow-hidden text-xs shadow-carbon-sm transition hover:border-signal-yellow/60 cursor-pointer"
    >
      {/* Citation Header */}
      <div className="p-3 flex items-center justify-between gap-2 bg-carbon-deep">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono font-bold text-carbon-deep bg-signal-yellow px-1.5 py-0.5 rounded text-[10px]">
            [{index + 1}]
          </span>
          <span className="text-silver-light font-semibold truncate" title={citation.filename}>
            {citation.filename}
          </span>
          <span className="text-silver-secondary font-mono text-[11px] shrink-0">
            p. {citation.page_number}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Confidence Badge */}
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${getScoreBadge(
              relevancePct
            )}`}
          >
            {relevancePct}% Match
          </span>

          {onOpenPage && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onOpenPage(citation.filename, citation.page_number);
              }}
              className="text-silver-secondary hover:text-signal-yellow p-1 rounded hover:bg-carbon-surface transition"
              title="Open cited page in Document Viewer"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={handleCopy}
            className="text-silver-secondary hover:text-silver-light p-1 rounded hover:bg-carbon-surface transition"
            title="Copy text excerpt"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="text-silver-secondary hover:text-silver-light p-1 rounded hover:bg-carbon-surface"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Heading Tag */}
      {citation.section_heading && (
        <div className="px-3 py-1 bg-carbon-secondary/50 border-t border-silver-border/30 text-[10px] font-mono text-silver-secondary flex items-center gap-1">
          <Hash className="w-3 h-3 text-signal-yellow" />
          <span className="truncate">{citation.section_heading}</span>
        </div>
      )}

      {/* Passage Excerpt */}
      <div className="p-3 text-silver-light font-mono text-[11px] leading-relaxed border-t border-silver-border/40 bg-carbon-primary/60">
        {isExpanded ? (
          <div className="whitespace-pre-wrap">{citation.content}</div>
        ) : (
          <div className="line-clamp-3">{citation.content}</div>
        )}
      </div>
    </div>
  );
}
