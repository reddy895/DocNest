import React, { useRef, useState, useEffect } from 'react';
import {
  Paperclip,
  SlidersHorizontal,
  ArrowUp,
  Square,
  X,
  Check,
  Loader2,
} from 'lucide-react';
import ModelSelector from './ModelSelector';
import { cn } from '../../lib/cn';

const SEARCH_MODES = [
  { id: 'hybrid', name: 'Hybrid', desc: 'Vector + Keyword' },
  { id: 'vector', name: 'Semantic', desc: 'Dense Vector' },
  { id: 'bm25', name: 'Keyword', desc: 'Exact BM25' },
];

export default function ChatComposer({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  isUploading = false,
  onStop,
  attachments = [],
  onAddAttachments,
  onRemoveAttachment,
  selectedModel = 'llama3.2',
  onSelectModel,
  searchMode = 'hybrid',
  onSelectSearchMode,
  placeholder = 'Ask anything about your documents',
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [showSearchMenu, setShowSearchMenu] = useState(false);
  const textareaRef = useRef(null);
  const attachmentInputRef = useRef(null);
  const searchMenuRef = useRef(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  useEffect(() => {
    if (!showSearchMenu) return;
    const handleClickOutside = (event) => {
      if (searchMenuRef.current && !searchMenuRef.current.contains(event.target)) {
        setShowSearchMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSearchMenu]);

  const handleFiles = (files) => {
    const list = Array.from(files || []);
    if (list.length > 0) onAddAttachments?.(list);
  };

  const canSend = (Boolean(value?.trim()) || attachments.length > 0) && !isUploading;
  const activeModeLabel = SEARCH_MODES.find((m) => m.id === searchMode)?.name || 'Hybrid';

  return (
    <div className="mx-auto w-full max-w-[800px]">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (canSend && !isLoading) onSubmit?.();
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={cn(
          'relative flex flex-col rounded-3xl border bg-[#303030] transition-colors',
          isDragging ? 'border-[#ECECEC] bg-[#363636]' : 'border-[#3A3A3A] focus-within:border-[#525252]'
        )}
      >
        {isDragging && (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-3xl bg-[#303030]/95 text-sm font-medium text-[#ECECEC]">
            <Paperclip className="h-4 w-4" />
            <span>Drop documents here to attach</span>
          </div>
        )}

        {/* Attachment Preview Chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 px-4 pt-3 pb-1">
            {attachments.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-2 rounded-xl border border-[#3A3A3A] bg-[#212121] px-2.5 py-1.5 text-xs text-[#ECECEC]"
              >
                {isUploading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-[#A1A1A1]" />
                ) : (
                  <Paperclip className="h-3.5 w-3.5 text-[#A1A1A1]" />
                )}
                <span className="max-w-[160px] truncate">{file.name}</span>
                <span className="text-[10px] text-[#777777]">
                  {(file.size / 1024).toFixed(0)} KB
                </span>
                {!isUploading && (
                  <button
                    type="button"
                    onClick={() => onRemoveAttachment?.(index)}
                    className="rounded p-0.5 text-[#777777] transition-colors hover:text-[#ECECEC]"
                    aria-label={`Remove ${file.name}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Multiline Textarea */}
        <div className="px-4 pt-3 pb-1">
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(event) => onChange?.(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (canSend && !isLoading) onSubmit?.();
              }
            }}
            placeholder={placeholder}
            className="max-h-[200px] w-full resize-none bg-transparent text-[15px] leading-relaxed text-[#ECECEC] placeholder-[#777777] focus:outline-none"
            aria-label="Message input"
          />
        </div>

        {/* Bottom Controls Toolbar */}
        <div className="flex items-center justify-between px-3 pb-2.5 pt-1">
          <div className="flex items-center gap-1">
            <input
              type="file"
              multiple
              ref={attachmentInputRef}
              onChange={(event) => {
                handleFiles(event.target.files);
                event.target.value = '';
              }}
              className="hidden"
              aria-hidden="true"
              tabIndex={-1}
            />

            <button
              type="button"
              onClick={() => attachmentInputRef.current?.click()}
              className="flex h-8 w-8 items-center justify-center rounded-full text-[#A1A1A1] transition-colors hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
              aria-label="Attach documents"
              title="Attach documents"
            >
              <Paperclip className="h-4 w-4" />
            </button>

            <ModelSelector selectedModel={selectedModel} onSelectModel={onSelectModel} />

            {/* Retrieval Mode Selector */}
            <div ref={searchMenuRef} className="relative flex-shrink-0">
              <button
                type="button"
                onClick={() => setShowSearchMenu((prev) => !prev)}
                className="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-medium text-[#A1A1A1] transition-colors hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
                title="Retrieval mode"
                aria-haspopup="listbox"
                aria-expanded={showSearchMenu}
              >
                <SlidersHorizontal className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{activeModeLabel}</span>
              </button>

              {showSearchMenu && (
                <div
                  className="absolute bottom-11 left-0 z-30 w-48 rounded-xl border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 shadow-carbon-lg animate-fade-in"
                  role="listbox"
                >
                  <div className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-[#777777]">
                    Retrieval Mode
                  </div>
                  {SEARCH_MODES.map((mode) => {
                    const active = searchMode === mode.id;
                    return (
                      <button
                        key={mode.id}
                        type="button"
                        onClick={() => {
                          onSelectSearchMode?.(mode.id);
                          setShowSearchMenu(false);
                        }}
                        className={cn(
                          'flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors',
                          active
                            ? 'bg-[#3A3A3A] text-[#ECECEC] font-medium'
                            : 'text-[#ECECEC]/85 hover:bg-[#333333]'
                        )}
                      >
                        <div>
                          <div className="text-xs">{mode.name}</div>
                          <div className="text-[10px] text-[#777777]">{mode.desc}</div>
                        </div>
                        {active && <Check className="h-3.5 w-3.5 text-[#ECECEC]" />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center">
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F0F0F0] text-[#171717] transition-colors hover:bg-white"
                aria-label="Stop generating"
                title="Stop generating"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!canSend}
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full transition-colors',
                  canSend
                    ? 'bg-[#F0F0F0] text-[#171717] hover:bg-white'
                    : 'cursor-not-allowed bg-[#3A3A3A] text-[#777777]'
                )}
                aria-label="Send message"
                title="Send message"
              >
                <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>
      </form>

      <p className="mt-2 text-center text-[11px] text-[#777777]">
        DocNest can make mistakes. Verify important information with the original sources.
      </p>
    </div>
  );
}
