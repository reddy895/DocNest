import React, { useState } from 'react';
import {
  Layers,
  Copy,
  Check,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import CitationChip from './CitationChip';
import RetrievalStatus from './RetrievalStatus';
import { cn } from '../../lib/cn';

export default function AssistantMessage({
  message,
  isLast = false,
  isStreaming = false,
  stageKey = 'rewriting',
  onCopy,
  onRegenerate,
  onFeedback,
  onSaveNote,
  onCitationClick,
  onInspectSources,
}) {
  const [copied, setCopied] = useState(false);
  const [savedNote, setSavedNote] = useState(false);

  const hasText = Boolean(message.text && message.text.length > 0);
  const showStatus = isStreaming && isLast && !hasText;

  const handleCopy = () => {
    if (!message.text) return;
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    onCopy?.(message.id, message.text);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleSave = async () => {
    if (!onSaveNote) return;
    await onSaveNote(message);
    setSavedNote(true);
    setTimeout(() => setSavedNote(false), 2200);
  };

  return (
    <div className="group flex w-full items-start gap-3.5 animate-fade-in">
      <div className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center overflow-hidden rounded-full border border-[#3A3A3A] bg-black">
        <img src="/docnest-logo.jpg" alt="DocNest" className="h-full w-full object-cover" />
      </div>

      <div className="min-w-0 flex-1 space-y-2.5">
        {message.isError ? (
          <div className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3.5 py-2.5 text-sm text-rose-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
            <span>{message.text}</span>
          </div>
        ) : showStatus ? (
          <RetrievalStatus stageKey={stageKey} hasStartedStreaming={hasText} />
        ) : (
          <div className="text-[#ECECEC]">
            <MarkdownRenderer content={message.text} onCitationClick={onCitationClick} />
            {isStreaming && isLast && (
              <span className="ml-1 inline-block h-4 w-1.5 translate-y-0.5 animate-pulse bg-[#ECECEC]" />
            )}
          </div>
        )}

        {/* Compact Source Citation Chips */}
        {!message.isError && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            {message.citations.slice(0, 6).map((cite, idx) => (
              <CitationChip
                key={cite.source_id || idx}
                filename={cite.filename}
                pageNumber={cite.page_number || 1}
                sectionHeading={cite.section_heading}
                snippet={cite.content}
                relevanceScore={cite.relevance_score}
                onClick={() => onCitationClick?.(cite)}
              />
            ))}
          </div>
        )}

        {/* ChatGPT-style Action Bar */}
        {hasText && !(isStreaming && isLast) && !message.isError && (
          <div
            className={cn(
              'flex flex-wrap items-center gap-1 pt-0.5 transition-opacity',
              isLast ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
            )}
          >
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-md p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
              title="Copy response"
              aria-label="Copy response"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            </button>

            {onRegenerate && (
              <button
                type="button"
                onClick={() => onRegenerate(message.id)}
                className="rounded-md p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                title="Regenerate response"
                aria-label="Regenerate response"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            )}

            {onFeedback && (
              <>
                <button
                  type="button"
                  onClick={() => onFeedback(message.id, 1)}
                  className={cn(
                    'rounded-md p-1.5 transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]',
                    message.feedback_rating === 1 ? 'text-[#ECECEC]' : 'text-[#A1A1A1]'
                  )}
                  title="Good response"
                  aria-label="Good response"
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onFeedback(message.id, -1)}
                  className={cn(
                    'rounded-md p-1.5 transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]',
                    message.feedback_rating === -1 ? 'text-rose-400' : 'text-[#A1A1A1]'
                  )}
                  title="Bad response"
                  aria-label="Bad response"
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </button>
              </>
            )}

            {onSaveNote && (
              <button
                type="button"
                onClick={handleSave}
                className="rounded-md p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
                title="Save to notes"
                aria-label="Save to notes"
              >
                {savedNote ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Bookmark className="h-3.5 w-3.5" />
                )}
              </button>
            )}

            {onInspectSources && message.citations && message.citations.length > 0 && (
              <button
                type="button"
                onClick={() => onInspectSources(message)}
                className="ml-1 rounded-md px-2 py-1 text-[11px] font-medium text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
              >
                {message.citations.length} {message.citations.length === 1 ? 'source' : 'sources'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

