import React from 'react';
import {
  FileText,
  X,
  ExternalLink,
  Sliders,
} from 'lucide-react';

export default function ContextualResearchPanel({
  isOpen = true,
  onClose,
  activeTab = 'citations',
  setActiveTab = () => {},
  citations,
  activeCitations,
  trace,
  activeTrace,
  documents = [],
  selectedDocIds = [],
  onToggleDocScope,
  onToggleDoc,
  onSelectAllDocs,
  onClearScope,
  onCitationClick = () => {},
  highlightedCitationId = null,
}) {
  if (!isOpen) return null;

  const resolvedCitations = activeCitations || citations || [];
  const resolvedTrace = activeTrace || trace || null;
  const handleToggleDoc = onToggleDoc || onToggleDocScope || (() => {});
  const handleResetScope = onClearScope || onSelectAllDocs || (() => {});

  return (
    <aside className="z-20 flex h-full w-80 flex-shrink-0 flex-col border-l border-[#2E2E2E] bg-[#171717] text-[#ECECEC] md:w-96 animate-fade-in">
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-[#2E2E2E] px-4">
        <span className="text-xs font-semibold text-[#ECECEC]">Sources & Context</span>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
          title="Close panel"
          aria-label="Close panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2E2E2E] text-xs">
        <button
          type="button"
          onClick={() => setActiveTab('citations')}
          className={`flex-1 border-b-2 py-2.5 font-medium transition-colors ${
            activeTab === 'citations'
              ? 'border-[#ECECEC] text-[#ECECEC]'
              : 'border-transparent text-[#A1A1A1] hover:text-[#ECECEC]'
          }`}
        >
          Sources ({resolvedCitations.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 border-b-2 py-2.5 font-medium transition-colors ${
            activeTab === 'inspector'
              ? 'border-[#ECECEC] text-[#ECECEC]'
              : 'border-transparent text-[#A1A1A1] hover:text-[#ECECEC]'
          }`}
        >
          Pipeline
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('scope')}
          className={`flex-1 border-b-2 py-2.5 font-medium transition-colors ${
            activeTab === 'scope'
              ? 'border-[#ECECEC] text-[#ECECEC]'
              : 'border-transparent text-[#A1A1A1] hover:text-[#ECECEC]'
          }`}
        >
          Scope ({selectedDocIds.length || 'All'})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-3 overflow-y-auto p-4 text-xs">
        {activeTab === 'citations' && (
          <div className="space-y-3">
            {resolvedCitations.length === 0 ? (
              <div className="space-y-2 py-12 text-center text-[#A1A1A1]">
                <FileText className="mx-auto h-7 w-7 text-[#777777]" />
                <p className="font-medium text-[#ECECEC]">No active citations</p>
                <p className="text-[11px] text-[#777777]">
                  Ask a question to inspect supporting passages and page numbers.
                </p>
              </div>
            ) : (
              resolvedCitations.map((cite, index) => {
                const isHighlighted =
                  highlightedCitationId === cite.source_id || highlightedCitationId === index;
                return (
                  <div
                    key={cite.source_id || index}
                    className={`space-y-2 rounded-xl border p-3.5 transition-colors ${
                      isHighlighted
                        ? 'border-[#ECECEC] bg-[#2A2A2A]'
                        : 'border-[#3A3A3A] bg-[#212121] hover:border-[#555555]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex min-w-0 items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5 flex-shrink-0 text-[#A1A1A1]" />
                        <span className="truncate font-medium text-[#ECECEC]">
                          {cite.filename}
                        </span>
                      </div>
                      <span className="flex-shrink-0 rounded-md border border-[#3A3A3A] bg-[#2A2A2A] px-2 py-0.5 font-mono text-[10px] text-[#ECECEC]">
                        p. {cite.page_number}
                      </span>
                    </div>

                    {cite.section_heading && (
                      <div className="truncate font-mono text-[10px] text-[#A1A1A1]">
                        § {cite.section_heading}
                      </div>
                    )}

                    <p className="line-clamp-4 rounded-lg border border-[#2E2E2E] bg-[#171717] p-2.5 text-[11px] leading-relaxed text-[#A1A1A1]">
                      &ldquo;{cite.content}&rdquo;
                    </p>

                    <div className="flex items-center justify-between border-t border-[#2E2E2E] pt-2 font-mono text-[10px] text-[#A1A1A1]">
                      <div className="flex items-center gap-2">
                        <span>
                          Score:{' '}
                          <strong className="text-[#ECECEC]">
                            {((cite.relevance_score || 0) * 100).toFixed(0)}%
                          </strong>
                        </span>
                        {cite.dense_rank && <span>D: #{cite.dense_rank}</span>}
                        {cite.sparse_rank && <span>S: #{cite.sparse_rank}</span>}
                      </div>
                      <button
                        type="button"
                        onClick={() => onCitationClick(cite)}
                        className="flex items-center gap-1 font-sans text-[11px] font-medium text-[#ECECEC] hover:underline"
                      >
                        <span>Open page</span>
                        <ExternalLink className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'inspector' && (
          <div className="space-y-3 font-mono">
            {resolvedTrace ? (
              <>
                <div className="space-y-1.5 rounded-xl border border-[#3A3A3A] bg-[#212121] p-3">
                  <span className="block text-[10px] uppercase tracking-wider text-[#777777]">
                    Rewritten Query
                  </span>
                  <div className="font-sans text-[11px] text-[#ECECEC]">
                    &ldquo;{resolvedTrace.rewritten_query || 'N/A'}&rdquo;
                  </div>
                </div>

                <div className="space-y-2 rounded-xl border border-[#3A3A3A] bg-[#212121] p-3">
                  <span className="block text-[10px] uppercase tracking-wider text-[#777777]">
                    Latency
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="rounded border border-[#2E2E2E] bg-[#171717] p-2">
                      <span className="block text-[10px] text-[#777777]">Retrieval</span>
                      <span className="font-semibold text-[#ECECEC]">
                        {resolvedTrace.retrieval_ms || 0} ms
                      </span>
                    </div>
                    <div className="rounded border border-[#2E2E2E] bg-[#171717] p-2">
                      <span className="block text-[10px] text-[#777777]">Reranking</span>
                      <span className="font-semibold text-[#ECECEC]">
                        {resolvedTrace.rerank_ms || 0} ms
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5 rounded-xl border border-[#3A3A3A] bg-[#212121] p-3">
                  <span className="block text-[10px] uppercase tracking-wider text-[#777777]">
                    Retrieval Stats
                  </span>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#A1A1A1]">Strategy:</span>
                      <span className="font-semibold uppercase text-[#ECECEC]">
                        {resolvedTrace.search_mode || 'Hybrid'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A1A1A1]">Candidates:</span>
                      <span className="text-[#ECECEC]">{resolvedTrace.candidate_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A1A1A1]">Reranked:</span>
                      <span className="text-[#ECECEC]">{resolvedTrace.reranked_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A1A1A1]">Top Score:</span>
                      <span className="font-semibold text-[#ECECEC]">
                        {resolvedTrace.max_relevance_score || '0.00'}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="space-y-2 py-12 text-center font-sans text-[#A1A1A1]">
                <Sliders className="mx-auto h-7 w-7 text-[#777777]" />
                <p>No telemetry recorded yet.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'scope' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-[#2E2E2E] pb-2">
              <span className="text-xs font-semibold text-[#ECECEC]">Document scope</span>
              <button
                type="button"
                onClick={handleResetScope}
                className="text-[11px] text-[#A1A1A1] hover:text-[#ECECEC] hover:underline"
              >
                Reset to all
              </button>
            </div>

            <div className="space-y-1.5">
              {documents.map((doc) => {
                const docId = doc.doc_id || doc.id;
                const isSelected = selectedDocIds.includes(docId);
                return (
                  <button
                    key={docId}
                    type="button"
                    onClick={() => handleToggleDoc(docId)}
                    className={`flex w-full items-center justify-between rounded-lg border px-2.5 py-2 text-left transition-colors ${
                      isSelected
                        ? 'border-[#ECECEC] bg-[#2A2A2A] text-[#ECECEC]'
                        : 'border-[#3A3A3A] bg-[#212121] text-[#A1A1A1] hover:bg-[#2A2A2A]/60 hover:text-[#ECECEC]'
                    }`}
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                      <span className="truncate text-xs">{doc.filename}</span>
                    </div>
                    <span className="ml-2 font-mono text-[10px] text-[#777777]">
                      {doc.page_count || 1}p
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
