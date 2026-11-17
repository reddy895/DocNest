import React, { useState } from 'react';
import {
  Cpu,
  HardDrive,
  Database,
  Layers,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Sliders,
  Info,
} from 'lucide-react';

export default function Settings({ systemStatus, onRefreshStatus }) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefreshStatus) {
      await onRefreshStatus();
    }
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';
  const availableModels = systemStatus?.components?.ollama?.available_models || [];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[#E0E3E5] tracking-tight">System Settings & Status</h2>
          <p className="text-xs text-[#969DA3]">
            Inspect live runtime infrastructure, AI models, and vector database status.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-secondary text-xs py-1.5 px-3"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ollama LLM Runtime Card */}
        <div className="carbon-card p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#555C61]/50">
            <div className="flex items-center gap-2.5">
              <Cpu className="w-5 h-5 text-[#F4D21F]" />
              <h3 className="font-semibold text-sm text-[#E0E3E5]">Ollama LLM Engine</h3>
            </div>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                isOllamaConnected
                  ? 'border-emerald-500/40 text-emerald-400 bg-emerald-950/20'
                  : 'border-amber-500/40 text-amber-400 bg-amber-950/20'
              }`}
            >
              {isOllamaConnected ? 'ONLINE' : 'UNREACHABLE'}
            </span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Configured Model:</span>
              <span className="text-[#E0E3E5] font-semibold">
                {systemStatus?.components?.ollama?.configured_model || 'llama3.2'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Base Endpoint:</span>
              <span className="text-[#E0E3E5]">
                {systemStatus?.components?.ollama?.base_url || 'http://localhost:11434'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Target Available:</span>
              <span className={systemStatus?.components?.ollama?.model_available ? 'text-emerald-400' : 'text-amber-400'}>
                {systemStatus?.components?.ollama?.model_available ? 'Verified Installed' : 'Not Pulled'}
              </span>
            </div>
          </div>

          <div className="pt-2">
            <span className="text-[11px] text-[#969DA3] block mb-1.5 font-mono">Installed Models:</span>
            <div className="flex flex-wrap gap-1.5">
              {availableModels.length > 0 ? (
                availableModels.map((m, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono bg-[#171A1C] border border-[#555C61] px-2 py-0.5 rounded text-[#BFC3C7]"
                  >
                    {m}
                  </span>
                ))
              ) : (
                <span className="text-[11px] text-[#969DA3] italic">No models reported</span>
              )}
            </div>
          </div>
        </div>

        {/* ChromaDB Vector Store Card */}
        <div className="carbon-card p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#555C61]/50">
            <div className="flex items-center gap-2.5">
              <Database className="w-5 h-5 text-[#F4D21F]" />
              <h3 className="font-semibold text-sm text-[#E0E3E5]">ChromaDB Vector Store</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/40 text-emerald-400 bg-emerald-950/20">
              PERSISTENT
            </span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Collection Name:</span>
              <span className="text-[#E0E3E5]">docnest_collection</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Total Indexed Chunks:</span>
              <span className="text-[#F4D21F] font-bold">
                {systemStatus?.total_chunks || 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Distance Metric:</span>
              <span className="text-[#E0E3E5]">Cosine Similarity</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Storage Directory:</span>
              <span className="text-[#E0E3E5] truncate max-w-[180px]">
                {systemStatus?.components?.storage?.chroma_dir || 'backend/chroma_db'}
              </span>
            </div>
          </div>
        </div>

        {/* Embedding Generator Card */}
        <div className="carbon-card p-5 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-[#555C61]/50">
            <Layers className="w-5 h-5 text-[#F4D21F]" />
            <h3 className="font-semibold text-sm text-[#E0E3E5]">Sentence Transformers</h3>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Model:</span>
              <span className="text-[#E0E3E5] font-semibold">all-MiniLM-L6-v2</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Embedding Dimension:</span>
              <span className="text-[#E0E3E5]">384 vectors</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Normalization:</span>
              <span className="text-emerald-400">L2 Normalized (Unit Length)</span>
            </div>
          </div>
        </div>

        {/* RAG Engine Parameters */}
        <div className="carbon-card p-5 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-[#555C61]/50">
            <Sliders className="w-5 h-5 text-[#F4D21F]" />
            <h3 className="font-semibold text-sm text-[#E0E3E5]">RAG Parameters</h3>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Chunk Size:</span>
              <span className="text-[#E0E3E5]">500 characters</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Overlap:</span>
              <span className="text-[#E0E3E5]">60 characters</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Default Top-K:</span>
              <span className="text-[#E0E3E5]">4 passages</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#969DA3]">Similarity Threshold:</span>
              <span className="text-[#E0E3E5]">0.25</span>
            </div>
          </div>
        </div>
      </div>

      {/* Application Details */}
      <div className="carbon-card p-5">
        <div className="flex items-center gap-2 mb-2 text-[#E0E3E5] font-semibold text-sm">
          <Info className="w-4 h-4 text-[#F4D21F]" />
          <span>About DocNest</span>
        </div>
        <p className="text-xs text-[#969DA3] leading-relaxed">
          DocNest v1.0.0 is an enterprise document intelligence and question-answering platform.
          All vector indexing and language model inference run locally on this machine with strict
          factual grounding guardrails.
        </p>
      </div>
    </div>
  );
}
