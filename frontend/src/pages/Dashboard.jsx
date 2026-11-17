import React from 'react';
import {
  FileText,
  Layers,
  Cpu,
  UploadCloud,
  MessageSquare,
  ArrowRight,
  Clock,
  CheckCircle2,
  HardDrive,
} from 'lucide-react';

export default function Dashboard({
  documents = [],
  totalChunks = 0,
  systemStatus,
  onNavigate,
  onOpenUpload,
}) {
  const recentDocs = documents.slice(0, 5);
  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="carbon-card p-6 md:p-8 relative overflow-hidden">
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-[#171A1C] border border-[#555C61] text-[11px] font-mono text-[#F4D21F] mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F4D21F] animate-pulse"></span>
            PRODUCTION RAG PLATFORM
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-[#E0E3E5] mb-2 tracking-tight">
            DocNest Intelligence Console
          </h2>
          <p className="text-[#969DA3] text-sm md:text-base leading-relaxed mb-6">
            Upload institutional and research documents, perform page-aware semantic queries,
            and inspect fully grounded answers powered by local Llama 3.2.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('chat')}
              className="btn-primary text-sm"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Open Chat Workspace</span>
            </button>
            <button
              onClick={onOpenUpload}
              className="btn-secondary text-sm"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload New PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="carbon-card p-5">
          <div className="flex items-center justify-between text-[#969DA3] mb-3">
            <span className="text-xs uppercase font-mono tracking-wider">Documents</span>
            <FileText className="w-4 h-4 text-[#F4D21F]" />
          </div>
          <div className="text-3xl font-bold text-[#E0E3E5] tracking-tight mb-1">
            {documents.length}
          </div>
          <div className="text-xs text-[#969DA3]">Indexed PDF files</div>
        </div>

        {/* Metric 2 */}
        <div className="carbon-card p-5">
          <div className="flex items-center justify-between text-[#969DA3] mb-3">
            <span className="text-xs uppercase font-mono tracking-wider">Vector Chunks</span>
            <Layers className="w-4 h-4 text-[#F4D21F]" />
          </div>
          <div className="text-3xl font-bold text-[#E0E3E5] tracking-tight mb-1">
            {totalChunks}
          </div>
          <div className="text-xs text-[#969DA3]">ChromaDB vector embeddings</div>
        </div>

        {/* Metric 3 */}
        <div className="carbon-card p-5">
          <div className="flex items-center justify-between text-[#969DA3] mb-3">
            <span className="text-xs uppercase font-mono tracking-wider">LLM Engine</span>
            <Cpu className="w-4 h-4 text-[#F4D21F]" />
          </div>
          <div className="text-lg font-bold text-[#E0E3E5] truncate mb-1">
            {systemStatus?.components?.ollama?.configured_model || 'llama3.2'}
          </div>
          <div className="text-xs flex items-center gap-1.5 text-[#969DA3]">
            <span
              className={`w-2 h-2 rounded-full ${
                isOllamaConnected ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span>{isOllamaConnected ? 'Ollama Online' : 'Connecting...'}</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="carbon-card p-5">
          <div className="flex items-center justify-between text-[#969DA3] mb-3">
            <span className="text-xs uppercase font-mono tracking-wider">Embedding Model</span>
            <HardDrive className="w-4 h-4 text-[#F4D21F]" />
          </div>
          <div className="text-sm font-bold text-[#E0E3E5] truncate mb-1">
            all-MiniLM-L6-v2
          </div>
          <div className="text-xs text-[#969DA3]">384-dim normalized cosine</div>
        </div>
      </div>

      {/* Recent Documents Table & Quick Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents */}
        <div className="lg:col-span-2 carbon-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-[#E0E3E5] text-base">Recent Documents</h3>
              <p className="text-xs text-[#969DA3]">Recently ingested PDF documents and status</p>
            </div>
            <button
              onClick={() => onNavigate('library')}
              className="text-xs text-[#F4D21F] hover:text-[#FFDF45] inline-flex items-center gap-1 font-medium"
            >
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {recentDocs.length === 0 ? (
            <div className="border border-dashed border-[#555C61] rounded-lg p-8 text-center bg-[#171A1C]">
              <UploadCloud className="w-8 h-8 text-[#969DA3] mx-auto mb-2 opacity-50" />
              <p className="text-sm text-[#BFC3C7] font-medium mb-1">No documents uploaded yet</p>
              <p className="text-xs text-[#969DA3] mb-4">
                Upload your first PDF document to start querying it with local AI.
              </p>
              <button onClick={onOpenUpload} className="btn-primary text-xs py-1.5 px-3">
                Upload PDF
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#555C61]/50">
              {recentDocs.map((doc) => (
                <div
                  key={doc.doc_id}
                  className="py-3 flex items-center justify-between gap-4 hover:bg-[#202326] px-2 rounded transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded bg-[#171A1C] border border-[#555C61] flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4 text-[#F4D21F]" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-[#E0E3E5] truncate">
                        {doc.filename}
                      </div>
                      <div className="text-xs text-[#969DA3] flex items-center gap-2 font-mono">
                        <span>{doc.page_count} pages</span>
                        <span>•</span>
                        <span>{doc.total_chunks} chunks</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.file_size_bytes)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#171A1C] border border-emerald-500/40 text-emerald-400">
                      INDEXED
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Start & System Specifications */}
        <div className="carbon-card p-6 space-y-4">
          <h3 className="font-semibold text-[#E0E3E5] text-base">RAG Pipeline Parameters</h3>
          <p className="text-xs text-[#969DA3]">Configured retrieval hyperparameters</p>

          <div className="space-y-3 pt-2 text-xs font-mono">
            <div className="flex justify-between py-1.5 border-b border-[#555C61]/40">
              <span className="text-[#969DA3]">Chunk Size</span>
              <span className="text-[#E0E3E5]">500 chars</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#555C61]/40">
              <span className="text-[#969DA3]">Chunk Overlap</span>
              <span className="text-[#E0E3E5]">60 chars</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#555C61]/40">
              <span className="text-[#969DA3]">Top-K Retrieval</span>
              <span className="text-[#E0E3E5]">4 passages</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#555C61]/40">
              <span className="text-[#969DA3]">Min Relevance Score</span>
              <span className="text-[#E0E3E5]">0.25 (Cosine)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#555C61]/40">
              <span className="text-[#969DA3]">Temperature</span>
              <span className="text-[#E0E3E5]">0.1 (Strict Grounding)</span>
            </div>
          </div>

          <div className="pt-4 border-t border-[#555C61]">
            <button
              onClick={() => onNavigate('chat')}
              className="w-full btn-primary text-xs py-2"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Launch AI Question Answering</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
