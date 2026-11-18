import React, { useState } from 'react';
import { FileText, Cpu, ShieldCheck, Download, CheckCircle2, RefreshCw } from 'lucide-react';
import { loadSampleDocuments } from '../services/api';

export default function SampleDatasetCards({ onSampleLoaded }) {
  const [loadingSample, setLoadingSample] = useState(null);
  const [loadedMap, setLoadedMap] = useState({});

  const SAMPLES = [
    {
      id: 'financial',
      title: 'Q3 Financial Performance',
      category: 'Finance & Earnings',
      description: 'Consolidated revenue metrics, segment breakdown tables, and operational risk factors.',
      icon: FileText,
      badge: 'Tables & Numbers',
    },
    {
      id: 'ai_whitepaper',
      title: 'Enterprise AI Architecture',
      category: 'Technical Whitepaper',
      description: 'Dual-path hybrid search, RRF rank fusion formula, and cross-encoder abstention thresholds.',
      icon: Cpu,
      badge: 'Formulas & Specs',
    },
    {
      id: 'compliance',
      title: 'Compliance Policy Manual',
      category: 'Governance & Security',
      description: 'MFA token requirements, AES-256 encryption rules, and 72-hour breach timelines.',
      icon: ShieldCheck,
      badge: 'Rules & Protocols',
    },
  ];

  const handleLoad = async (sampleId) => {
    setLoadingSample(sampleId);
    try {
      const docs = await loadSampleDocuments(sampleId);
      setLoadedMap((prev) => ({ ...prev, [sampleId]: true }));
      if (onSampleLoaded) onSampleLoaded(docs);
    } catch (err) {
      console.error('Error loading sample dataset:', err);
    } finally {
      setLoadingSample(null);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-silver-secondary font-mono">
          Or explore curated sample datasets:
        </h4>
        <button
          onClick={() => handleLoad('all')}
          disabled={loadingSample !== null}
          className="text-xs text-signal-yellow hover:underline font-medium flex items-center gap-1 disabled:opacity-50"
        >
          {loadingSample === 'all' ? (
            <>
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Indexing all 3...</span>
            </>
          ) : (
            <span>Load All 3 Samples</span>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {SAMPLES.map((s) => {
          const Icon = s.icon;
          const isLoaded = loadedMap[s.id];
          const isLoading = loadingSample === s.id;

          return (
            <div
              key={s.id}
              className="p-4 bg-carbon-primary border border-silver-border rounded-xl flex flex-col justify-between hover:border-signal-yellow/50 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-7 h-7 rounded-lg bg-carbon-surface border border-silver-border flex items-center justify-center text-signal-yellow">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-carbon-surface text-silver-secondary">
                    {s.badge}
                  </span>
                </div>
                <h5 className="text-sm font-semibold text-silver-light mb-1">{s.title}</h5>
                <p className="text-xs text-silver-secondary line-clamp-2 mb-3">{s.description}</p>
              </div>

              <button
                onClick={() => handleLoad(s.id)}
                disabled={isLoading || isLoaded}
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
                  isLoaded
                    ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/40 cursor-default'
                    : 'bg-carbon-surface hover:bg-carbon-secondary text-silver-light border border-silver-border hover:text-signal-yellow'
                }`}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Indexing...</span>
                  </>
                ) : isLoaded ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Loaded & Ready</span>
                  </>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5" />
                    <span>Load Sample PDF</span>
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
