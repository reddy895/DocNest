import React from 'react';
import {
  FileText,
  Sparkles,
  X,
  ExternalLink,
  Sliders,
  Layers,
  ChevronRight,
  Database,
  Hash,
  CheckCircle2,
} from 'lucide-react';

export default function ContextualResearchPanel({
  isOpen,
  onClose,
  activeTab = 'citations',
  setActiveTab = () => {},
  citations = [],
  trace = null,
  documents = [],
  selectedDocIds = [],
  onToggleDocScope = () => {},
  onSelectAllDocs = () => {},
  onCitationClick = () => {},
  highlightedCitationId = null,
}) {
  if (!isOpen) return null;

  return (
    <aside className="w-80 md:w-96 border-l border-[#30353A] bg-[#101214] flex flex-col h-full flex-shrink-0 animate-fade-in z-20 shadow-2xl">
      {/* Header */}
      <div className="p-3.5 border-b border-[#30353A] flex items-center justify-between bg-[#17191B]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#F5C542]" />
          <span className="font-semibold text-xs text-[#F2F3F4] tracking-wide">
            Research Evidence Drawer
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-[#A2A9B0] hover:text-[#F2F3F4] rounded hover:bg-[#1A1D20] transition"
          title="Close Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#30353A] bg-[#101214] text-xs">
        <button
          onClick={() => setActiveTab('citations')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'citations'
              ? 'border-[#F5C542] text-[#F5C542] bg-[#17191B]'
              : 'border-transparent text-[#A2A9B0] hover:text-[#F2F3F4]'
          }`}
        >
          Sources ({citations.length})
        </button>
        <button
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'inspector'
              ? 'border-[#F5C542] text-[#F5C542] bg-[#17191B]'
              : 'border-transparent text-[#A2A9B0] hover:text-[#F2F3F4]'
          }`}
        >
          RAG Pipeline
        </button>
        <button
          onClick={() => setActiveTab('scope')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'scope'
              ? 'border-[#F5C542] text-[#F5C542] bg-[#17191B]'
              : 'border-transparent text-[#A2A9B0] hover:text-[#F2F3F4]'
          }`}
        >
          Doc Scope ({selectedDocIds.length || 'All'})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 text-xs">
        {activeTab === 'citations' && (
          <div className="space-y-3">
            {citations.length === 0 ? (
              <div className="text-center py-12 text-[#A2A9B0] space-y-2">
                <FileText className="w-8 h-8 text-[#A2A9B0]/30 mx-auto" />
                <p className="font-medium text-[#F2F3F4]/80">No active citations</p>
                <p className="text-[11px] text-[#A2A9B0]/60">
                  Ask a question to inspect supporting chunks, page numbers, and relevance scores.
                </p>
              </div>
            ) : (
              citations.map((cite, index) => {
                const isHighlighted = highlightedCitationId === cite.source_id || highlightedCitationId === index;
                return (
                  <div
                    key={cite.source_id || index}
                    className={`p-3.5 bg-[#17191B] border rounded-xl space-y-2.5 transition shadow-sm ${
                      isHighlighted
                        ? 'border-[#F5C542] ring-1 ring-[#F5C542]/40 bg-[#F5C542]/5'
                        : 'border-[#30353A] hover:border-[#F5C542]/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 truncate">
                        <FileText className="w-3.5 h-3.5 text-[#F5C542] flex-shrink-0" />
                        <span className="font-semibold text-[#F2F3F4] truncate">
                          {cite.filename}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#F5C542]/10 text-[#F5C542] border border-[#F5C542]/30 flex-shrink-0 font-medium">
                        Page {cite.page_number}
                      </span>
                    </div>

                    {cite.section_heading && (
                      <div className="text-[10px] font-mono text-[#A2A9B0] truncate">
                        § {cite.section_heading}
                      </div>
                    )}

                    <p className="text-[11px] text-[#A2A9B0] leading-relaxed line-clamp-4 italic bg-[#101214] p-2.5 rounded-lg border border-[#30353A]/50">
                      "{cite.content}"
                    </p>

                    <div className="flex items-center justify-between pt-1 border-t border-[#30353A]/40 text-[10px] font-mono text-[#A2A9B0]">
                      <div className="flex items-center gap-2">
                        <span>Score: <strong className="text-[#F5C542]">{(cite.relevance_score * 100).toFixed(0)}%</strong></span>
                        {cite.dense_rank && <span>D: #{cite.dense_rank}</span>}
                        {cite.sparse_rank && <span>S: #{cite.sparse_rank}</span>}
                      </div>
                      <button
                        onClick={() => onCitationClick(cite)}
                        className="flex items-center gap-1 text-[11px] text-[#F5C542] hover:text-[#FFD358] font-sans font-medium transition"
                      >
                        <span>Jump to Page</span>
                        <ExternalLink className="w-3 h-3" />
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
            {trace ? (
              <>
                <div className="p-3 bg-[#17191B] border border-[#30353A] rounded-xl space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A2A9B0] block">
                    Rewritten Question
                  </span>
                  <div className="text-[11px] text-[#F2F3F4] font-sans">
                    "{trace.rewritten_query || 'N/A'}"
                  </div>
                </div>

                <div className="p-3 bg-[#17191B] border border-[#30353A] rounded-xl space-y-2">
                  <span className="text-[10px] uppercase tracking-wider text-[#A2A9B0] block">
                    Telemetry & Latency
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2 bg-[#101214] rounded border border-[#30353A]/40">
                      <span className="text-[#A2A9B0] block text-[10px]">Retrieval:</span>
                      <span className="text-[#F5C542] font-bold">{trace.retrieval_ms || 0} ms</span>
                    </div>
                    <div className="p-2 bg-[#101214] rounded border border-[#30353A]/40">
                      <span className="text-[#A2A9B0] block text-[10px]">Reranking:</span>
                      <span className="text-[#F5C542] font-bold">{trace.rerank_ms || 0} ms</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-[#17191B] border border-[#30353A] rounded-xl space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A2A9B0] block">
                    Fusion Candidates
                  </span>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#A2A9B0]">Strategy:</span>
                      <span className="text-[#F5C542] font-bold uppercase">{trace.search_mode || 'Hybrid'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A2A9B0]">Candidates Retrieved:</span>
                      <span className="text-[#F2F3F4]">{trace.candidate_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A2A9B0]">Candidates Reranked:</span>
                      <span className="text-[#F2F3F4]">{trace.reranked_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A2A9B0]">Top Relevance Score:</span>
                      <span className="text-[#F5C542] font-bold">
                        {trace.max_relevance_score || '0.00'}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-[#A2A9B0] space-y-2 font-sans">
                <Sliders className="w-8 h-8 text-[#A2A9B0]/30 mx-auto" />
                <p>No telemetry recorded yet.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'scope' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#30353A]">
              <span className="font-semibold text-xs text-[#F2F3F4]">Document Scoping</span>
              <button
                onClick={onSelectAllDocs}
                className="text-[11px] text-[#F5C542] hover:underline"
              >
                Reset to All
              </button>
            </div>

            <div className="space-y-1.5">
              {documents.map((doc) => {
                const docId = doc.doc_id || doc.id;
                const isSelected = selectedDocIds.includes(docId);
                return (
                  <div
                    key={docId}
                    onClick={() => onToggleDocScope(docId)}
                    className={`p-2.5 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#17191B] border-[#F5C542] text-[#F2F3F4]'
                        : 'bg-[#101214] border-[#30353A] text-[#A2A9B0] hover:border-[#30353A]/80'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText className={`w-3.5 h-3.5 ${isSelected ? 'text-[#F5C542]' : ''}`} />
                      <span className="truncate text-xs">{doc.filename}</span>
                    </div>
                    <span className="text-[10px] font-mono text-[#A2A9B0]">
                      {doc.page_count}p
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
