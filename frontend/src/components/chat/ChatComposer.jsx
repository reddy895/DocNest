import React, { useRef, useState } from 'react';
import {
  Paperclip,
  Cpu,
  ChevronDown,
  Layers,
  Send,
  Square,
  X,
} from 'lucide-react';
import { cn } from '../../lib/cn';

const MODEL_OPTIONS = [
  { id: 'llama3.2', name: 'Llama 3.2 (3B)', badge: 'Default' },
  { id: 'llama3.1:8b', name: 'Llama 3.1 (8B)', badge: '8B' },
  { id: 'mistral:7b', name: 'Mistral (7B)', badge: 'Fast' },
  { id: 'qwen2.5:7b', name: 'Qwen 2.5 (7B)', badge: 'Math/Code' },
  { id: 'deepseek-r1:8b', name: 'DeepSeek R1 (8B)', badge: 'Reasoning' },
];

const SEARCH_MODES = [
  { id: 'hybrid', name: 'Hybrid (RRF)', desc: 'Dense + Sparse BM25' },
  { id: 'vector', name: 'Semantic Vector', desc: 'Dense ChromaDB' },
  { id: 'bm25', name: 'Keyword BM25', desc: 'Exact Sparse Match' },
];

export default function ChatComposer({
  value,
  onChange,
  onSubmit,
  isLoading = false,
  onStop,
  attachments = [],
  onAddAttachments,
  onRemoveAttachment,
  selectedModel = 'llama3.2',
  onSelectModel,
  searchMode = 'hybrid',
  onSelectSearchMode,
  placeholder = 'Ask anything about your documents...',
  hint = 'Grounded in local ChromaDB vectors with Ollama Llama 3.2. Every factual claim contains page-level citations.',
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [showSearchMenu, setShowSearchMenu] = useState(false);
  const textareaRef = useRef(null);
  const attachmentInputRef = useRef(null);

  const resizeTextarea = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  const handleValueChange = (event) => {
    onChange?.(event.target.value);
    resizeTextarea();
  };

  const handleFiles = (files) => {
    const list = Array.from(files || []);
    if (list.length > 0) onAddAttachments?.(list);
  };

  const canSend = Boolean(value?.trim()) || attachments.length > 0;

  return (
    <div className="mx-auto w-full max-w-3xl">
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
          'relative flex flex-col rounded-2xl border bg-surface-raised transition-colors',
          isDragging ? 'border-brand bg-brand/5' : 'border-border focus-within:border-brand/70'
        )}
      >
        {isDragging && (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-2xl bg-surface-raised/95 text-sm font-medium text-brand backdrop-blur-sm">
            <Paperclip className="h-5 w-5 animate-bounce" />
            <span>Drop PDF or documents here to attach</span>
          </div>
        )}

        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 border-b border-border px-3 pb-1 pt-2.5">
            {attachments.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-2 rounded-lg border border-border bg-surface px-2.5 py-1 text-xs text-foreground"
              >
                <Paperclip className="h-3.5 w-3.5 text-brand" />
                <span className="max-w-[150px] truncate font-mono text-[11px]">{file.name}</span>
                <span className="text-[10px] text-muted-dim">({(file.size / 1024).toFixed(0)} KB)</span>
                <button
                  type="button"
                  onClick={() => onRemoveAttachment?.(index)}
                  className="rounded p-0.5 text-muted-dim transition-colors hover:text-rose-300"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2 p-2.5">
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
            className="flex-shrink-0 rounded-xl p-2 text-muted-dim transition-colors hover:bg-surface hover:text-brand"
            aria-label="Attach documents"
            title="Attach documents"
          >
            <Paperclip className="h-4 w-4" />
          </button>

          <div className="relative flex-shrink-0">
            <button
              type="button"
              onClick={() => {
                setShowModelMenu((open) => !open);
                setShowSearchMenu(false);
              }}
              className="flex items-center gap-1.5 rounded-xl border border-border bg-surface px-2.5 py-1.5 text-xs font-mono text-foreground transition-colors hover:bg-[#22262B]"
              title="Select AI model"
              aria-haspopup="menu"
              aria-expanded={showModelMenu}
            >
              <Cpu className="h-3.5 w-3.5 text-brand" />
              <span className="hidden text-[11px] font-medium sm:inline">{selectedModel}</span>
              <ChevronDown className="h-3 w-3 text-muted-dim" />
            </button>

            {showModelMenu && (
              <div className="absolute bottom-full left-0 z-30 mb-2 w-52 rounded-xl border border-border bg-surface-raised p-1 shadow-2xl" role="menu">
                <div className="border-b border-border/50 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-dim">
                  Ollama &amp; Local LLM
                </div>
                {MODEL_OPTIONS.map((model) => (
                  <button
                    key={model.id}
                    type="button"
                    role="menuitemradio"
                    aria-checked={selectedModel === model.id}
                    onClick={() => {
                      onSelectModel?.(model.id);
                      setShowModelMenu(false);
                    }}
                    className={cn(
                      'flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs transition-colors',
                      selectedModel === model.id
                        ? 'bg-brand/15 font-semibold text-brand'
                        : 'text-foreground hover:bg-surface'
                    )}
                  >
                    <span className="truncate">{model.name}</span>
                    <span className="rounded border border-border bg-background px-1.5 py-0.5 text-[9px] text-muted-dim">
                      {model.badge}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative flex-shrink-0">
            <button
              type="button"
              onClick={() => {
                setShowSearchMenu((open) => !open);
                setShowModelMenu(false);
              }}
              className="flex items-center gap-1.5 rounded-xl border border-border bg-surface px-2.5 py-1.5 text-xs font-mono text-foreground transition-colors hover:bg-[#22262B]"
              title="Select retrieval mode"
              aria-haspopup="menu"
              aria-expanded={showSearchMenu}
            >
              <Layers className="h-3.5 w-3.5 text-brand" />
              <span className="hidden text-[11px] font-medium capitalize sm:inline">{searchMode}</span>
              <ChevronDown className="h-3 w-3 text-muted-dim" />
            </button>

            {showSearchMenu && (
              <div className="absolute bottom-full left-0 z-30 mb-2 w-48 rounded-xl border border-border bg-surface-raised p-1 shadow-2xl" role="menu">
                <div className="border-b border-border/50 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-dim">
                  Retrieval Strategy
                </div>
                {SEARCH_MODES.map((mode) => (
                  <button
                    key={mode.id}
                    type="button"
                    role="menuitemradio"
                    aria-checked={searchMode === mode.id}
                    onClick={() => {
                      onSelectSearchMode?.(mode.id);
                      setShowSearchMenu(false);
                    }}
                    className={cn(
                      'flex w-full flex-col rounded-lg px-2.5 py-1.5 text-left text-xs transition-colors',
                      searchMode === mode.id
                        ? 'bg-brand/15 font-semibold text-brand'
                        : 'text-foreground hover:bg-surface'
                    )}
                  >
                    <span className="font-medium">{mode.name}</span>
                    <span className="text-[10px] text-muted-dim">{mode.desc}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleValueChange}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (canSend && !isLoading) onSubmit?.();
              }
            }}
            placeholder={`${placeholder} (Enter to send, Shift+Enter for newline)`}
            rows={1}
            className="max-h-52 w-full resize-none border-none bg-transparent px-2 py-1.5 text-sm leading-relaxed text-foreground placeholder:text-muted-dim/70 focus:outline-none"
            aria-label="Message DocNest"
          />

          <div className="flex flex-shrink-0 items-center gap-2 pb-0.5 pr-1">
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="rounded-xl border border-border bg-surface p-2.5 text-rose-300 transition-colors hover:bg-[#22262B]"
                title="Stop generation"
                aria-label="Stop generation"
              >
                <Square className="h-4 w-4 fill-rose-300" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!canSend}
                className="rounded-xl bg-brand p-2.5 font-bold text-brand-foreground shadow-carbon-sm transition-colors hover:bg-brand-hover disabled:opacity-40"
                title="Send message"
                aria-label="Send message"
              >
                <Send className="h-4 w-4" strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>
      </form>
      {hint && (
        <p className="mt-2 text-center font-mono text-[10px] text-muted-dim/70">{hint}</p>
      )}
    </div>
  );
}
