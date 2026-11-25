import React from 'react';
import { FileText, PanelRight, X } from 'lucide-react';
import { cn } from '../../lib/cn';

export default function ChatHeader({
  documents = [],
  selectedDocIds = [],
  onClearScope,
  rightPanelOpen = false,
  onToggleRightPanel,
  citationCount = 0,
}) {
  const scopedFilename =
    selectedDocIds.length === 1
      ? documents.find((d) => (d.doc_id || d.id) === selectedDocIds[0])?.filename || '1 document'
      : `${selectedDocIds.length} documents`;

  return (
    <header className="z-10 flex h-12 flex-shrink-0 items-center justify-between border-b border-[#2E2E2E] bg-[#212121] px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-sm font-medium text-[#ECECEC]">DocNest</span>
        <span className="text-[#777777]">/</span>
        {selectedDocIds.length === 0 ? (
          <span className="truncate rounded-md bg-[#2A2A2A] px-2 py-0.5 text-xs text-[#A1A1A1]">
            All documents ({documents.length})
          </span>
        ) : (
          <div className="flex items-center gap-1 rounded-md border border-[#3A3A3A] bg-[#2A2A2A] px-2 py-0.5 text-xs text-[#ECECEC]">
            <FileText className="h-3 w-3 flex-shrink-0 text-[#A1A1A1]" />
            <span className="max-w-[180px] truncate sm:max-w-xs">{scopedFilename}</span>
            <button
              type="button"
              onClick={onClearScope}
              className="ml-0.5 rounded p-0.5 text-[#A1A1A1] transition-colors hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
              title="Clear document filter"
              aria-label="Clear document filter"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={onToggleRightPanel}
        className={cn(
          'flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors',
          rightPanelOpen
            ? 'bg-[#2F2F2F] text-[#ECECEC]'
            : 'text-[#A1A1A1] hover:bg-[#2F2F2F] hover:text-[#ECECEC]'
        )}
        aria-expanded={rightPanelOpen}
        aria-label="Toggle sources panel"
      >
        <PanelRight className="h-4 w-4" />
        <span className="hidden sm:inline">Sources</span>
        {citationCount > 0 && (
          <span className="rounded-full bg-[#3A3A3A] px-1.5 py-0.2 text-[10px] font-medium text-[#ECECEC]">
            {citationCount}
          </span>
        )}
      </button>
    </header>
  );
}
