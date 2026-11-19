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
}) {
  if (!isOpen) return null;

  return (
    <aside className="w-80 md:w-96 border-l border-[#343A3F] bg-[#111315] flex flex-col h-full flex-shrink-0 animate-fade-in z-20">
      {/* Header */}
      <div className="p-3.5 border-b border-[#343A3F] flex items-center justify-between bg-[#191C1F]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#E5B83D]" />
          <span className="font-semibold text-xs text-[#F0F1F2]">
            Research Evidence Drawer
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-[#A0A6AC] hover:text-[#F0F1F2] rounded hover:bg-[#22262A] transition"
          title="Close Drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#343A3F] bg-[#111315] text-xs">
        <button
          onClick={() => setActiveTab('citations')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'citations'
              ? 'border-[#E5B83D] text-[#E5B83D] bg-[#191C1F]'
              : 'border-transparent text-[#A0A6AC] hover:text-[#F0F1F2]'
          }`}
        >
          Sources ({citations.length})
        </button>
        <button
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'inspector'
              ? 'border-[#E5B83D] text-[#E5B83D] bg-[#191C1F]'
              : 'border-transparent text-[#A0A6AC] hover:text-[#F0F1F2]'
          }`}
        >
          RAG Pipeline
        </button>
        <button
          onClick={() => setActiveTab('scope')}
          className={`flex-1 py-2 font-medium transition border-b-2 ${
            activeTab === 'scope'
              ? 'border-[#E5B83D] text-[#E5B83D] bg-[#191C1F]'
              : 'border-transparent text-[#A0A6AC] hover:text-[#F0F1F2]'
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
              <div className="text-center py-12 text-[#A0A6AC] space-y-2">
                <FileText className="w-8 h-8 text-[#A0A6AC]/30 mx-auto" />
                <p className="font-medium text-[#F0F1F2]/80">No active citations</p>
                <p className="text-[11px] text-[#A0A6AC]/60">
                  Ask a question to inspect supporting chunks, page numbers, and relevance scores.
                </p>
              </div>
            ) : (
              citations.map((cite, index) => (
                <div
                  key={index}
                  className="p-3 bg-[#191C1F] border border-[#343A3F] rounded-xl space-y-2 hover:border-[#E5B83D]/60 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 truncate">
                      <FileText className="w-3.5 h-3.5 text-[#E5B83D] flex-shrink-0" />
                      <span className="font-semibold text-[#F0F1F2] truncate">
                        {cite.filename}
                      </span>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#E5B83D]/10 text-[#E5B83D] border border-[#E5B83D]/30 flex-shrink-0">
                      p. {cite.page_number}
                    </span>
                  </div>

                  <p className="text-[11px] text-[#A0A6AC] leading-relaxed line-clamp-4 italic bg-[#111315] p-2 rounded border border-[#343A3F]/50">
                    "{cite.content}"
                  </p>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-[#A0A6AC] font-mono">
                      Score: {(cite.relevance_score * 100).toFixed(0)}%
                    </span>
                    <button
                      onClick={() => onCitationClick(cite)}
                      className="flex items-center gap-1 text-[11px] text-[#E5B83D] hover:underline"
                    >
                      <span>Jump to Page</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'inspector' && (
          <div className="space-y-3 font-mono">
            {trace ? (
              <>
                <div className="p-3 bg-[#191C1F] border border-[#343A3F] rounded-xl space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A0A6AC] block">
                    Rewritten Question
                  </span>
                  <div className="text-[11px] text-[#F0F1F2]">
                    "{trace.rewritten_query || 'N/A'}"
                  </div>
                </div>

                <div className="p-3 bg-[#191C1F] border border-[#343A3F] rounded-xl space-y-2">
                  <span className="text-[10px] uppercase tracking-wider text-[#A0A6AC] block">
                    Telemetry & Latency
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2 bg-[#111315] rounded border border-[#343A3F]/40">
                      <span className="text-[#A0A6AC] block text-[10px]">Retrieval:</span>
                      <span className="text-[#E5B83D] font-bold">{trace.retrieval_ms || 0} ms</span>
                    </div>
                    <div className="p-2 bg-[#111315] rounded border border-[#343A3F]/40">
                      <span className="text-[#A0A6AC] block text-[10px]">Reranking:</span>
                      <span className="text-[#E5B83D] font-bold">{trace.rerank_ms || 0} ms</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-[#191C1F] border border-[#343A3F] rounded-xl space-y-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-[#A0A6AC] block">
                    Fusion Candidates
                  </span>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-[#A0A6AC]">Candidates Retrieved:</span>
                      <span className="text-[#F0F1F2]">{trace.candidate_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A0A6AC]">Candidates Reranked:</span>
                      <span className="text-[#F0F1F2]">{trace.reranked_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#A0A6AC]">Top Relevance Score:</span>
                      <span className="text-[#E5B83D] font-bold">
                        {trace.max_relevance_score || '0.00'}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-[#A0A6AC] space-y-2">
                <Sliders className="w-8 h-8 text-[#A0A6AC]/30 mx-auto" />
                <p>No telemetry recorded yet.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'scope' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#343A3F]">
              <span className="font-semibold text-xs text-[#F0F1F2]">Document Scoping</span>
              <button
                onClick={onSelectAllDocs}
                className="text-[11px] text-[#E5B83D] hover:underline"
              >
                Reset to All
              </button>
            </div>

            <div className="space-y-1.5">
              {documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.doc_id);
                return (
                  <div
                    key={doc.doc_id}
                    onClick={() => onToggleDocScope(doc.doc_id)}
                    className={`p-2.5 rounded-lg border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#191C1F] border-[#E5B83D] text-[#F0F1F2]'
                        : 'bg-[#111315] border-[#343A3F] text-[#A0A6AC] hover:border-[#343A3F]/80'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText className={`w-3.5 h-3.5 ${isSelected ? 'text-[#E5B83D]' : ''}`} />
                      <span className="truncate text-xs">{doc.filename}</span>
                    </div>
                    <span className="text-[10px] font-mono text-[#A0A6AC]">
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
