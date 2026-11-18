import React from 'react';
import {
  Activity,
  Layers,
  Search,
  Cpu,
  Clock,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Hash,
} from 'lucide-react';

export default function RetrievalInspector({
  trace,
  citations = [],
  selectedCitation,
  onSelectCitation,
  onClose,
}) {
  if (!trace && citations.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-silver-secondary italic font-mono">
        Ask a question in chat to inspect real-time retrieval metrics and RRF fusion ranks.
      </div>
    );
  }

  const minThreshold = 0.30;

  return (
    <div className="flex flex-col h-full bg-carbon-deep text-xs font-mono overflow-y-auto">
      {/* Top Header */}
      <div className="p-3.5 border-b border-silver-border flex items-center justify-between shrink-0 bg-carbon-surface">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-signal-yellow" />
          <span className="font-bold text-silver-light">Retrieval Inspector</span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-silver-secondary hover:text-silver-light text-sm"
          >
            ✕
          </button>
        )}
      </div>

      <div className="p-4 space-y-5">
        {/* Step 1: Latency Waterfall Breakdown */}
        {trace && (
          <div className="space-y-2">
            <span className="text-[10px] uppercase font-bold text-silver-secondary block tracking-wider">
              1. Pipeline Latency Breakdown:
            </span>
            <div className="p-3 rounded-xl bg-carbon-surface border border-silver-border space-y-2">
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-silver-secondary flex items-center gap-1.5">
                  <Clock className="w-3 h-3 text-silver-secondary" /> Query Rewriting:
                </span>
                <span className="text-silver-light font-bold">{trace.query_rewriting_ms || 0} ms</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-silver-secondary flex items-center gap-1.5">
                  <Search className="w-3 h-3 text-silver-secondary" /> Hybrid Retrieval (BM25+Dense):
                </span>
                <span className="text-silver-light font-bold">{trace.retrieval_ms || 0} ms</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-silver-secondary flex items-center gap-1.5">
                  <Layers className="w-3 h-3 text-silver-secondary" /> Cross-Encoder Reranking:
                </span>
                <span className="text-silver-light font-bold">{trace.rerank_ms || 0} ms</span>
              </div>
              {trace.ttft_ms && (
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-silver-secondary flex items-center gap-1.5">
                    <Cpu className="w-3 h-3 text-silver-secondary" /> Time to First Token (TTFT):
                  </span>
                  <span className="text-silver-light font-bold">{trace.ttft_ms} ms</span>
                </div>
              )}
              <div className="pt-2 border-t border-silver-border/60 flex justify-between items-center text-xs">
                <span className="text-silver-light font-semibold">Total Turn Time:</span>
                <span className="text-signal-yellow font-bold text-sm">
                  {trace.total_ms || 0} ms
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Query Rewriting Audit */}
        {trace?.rewritten_query && (
          <div className="space-y-1.5">
            <span className="text-[10px] uppercase font-bold text-silver-secondary block tracking-wider">
              2. Query Rewriting Resolution:
            </span>
            <div className="p-2.5 rounded-lg bg-carbon-surface border border-silver-border text-silver-light text-[11px] leading-relaxed">
              "{trace.rewritten_query}"
            </div>
          </div>
        )}

        {/* Step 3: Candidate Scoring & Rank Fusion */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-silver-secondary block tracking-wider">
              3. Candidates ({citations.length} Reranked):
            </span>
            <span className="text-[10px] text-emerald-400 font-bold">
              Min Threshold: {minThreshold}
            </span>
          </div>

          <div className="space-y-2">
            {citations.map((c, idx) => {
              const isSelected = selectedCitation?.source_id === c.source_id;
              const passedThreshold = (c.relevance_score || 0) >= minThreshold;

              return (
                <div
                  key={c.source_id || idx}
                  onClick={() => onSelectCitation && onSelectCitation(c)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    isSelected
                      ? 'bg-carbon-surface border-signal-yellow shadow-signal-glow'
                      : 'bg-carbon-surface/80 border-silver-border/80 hover:border-silver-primary'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-silver-light truncate text-xs">
                      #{idx + 1} {c.filename}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                        passedThreshold
                          ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/40'
                          : 'bg-red-950/40 text-red-400 border-red-800/40'
                      }`}
                    >
                      {Math.round((c.relevance_score || 0.5) * 100)}%
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[10px] text-silver-secondary mb-2">
                    <span>Page {c.page_number}</span>
                    {c.dense_rank && <span>Dense #{c.dense_rank}</span>}
                    {c.sparse_rank && <span>BM25 #{c.sparse_rank}</span>}
                    {c.rrf_score && <span>RRF: {c.rrf_score}</span>}
                  </div>

                  <p className="text-[11px] text-silver-primary line-clamp-2 font-sans bg-carbon-primary p-2 rounded border border-silver-border/30">
                    {c.content}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
