import React from 'react';
import { Loader2, Search, Sparkles } from 'lucide-react';
import ThinkingIndicator from './ThinkingIndicator';

const STAGE_CONFIG = {
  rewriting: {
    label: 'Thinking...',
    type: 'thinking',
  },
  retrieving: {
    label: 'Searching your documents...',
    type: 'search',
  },
  reranking: {
    label: 'Analyzing retrieved information...',
    type: 'analyze',
  },
  generating: {
    label: 'Preparing your answer...',
    type: 'generate',
  },
};

export default function RetrievalStatus({ stageKey = 'rewriting', hasStartedStreaming = false }) {
  if (hasStartedStreaming) return null;

  const config = STAGE_CONFIG[stageKey] || STAGE_CONFIG.rewriting;

  if (config.type === 'thinking') {
    return <ThinkingIndicator label={config.label} />;
  }

  return (
    <div
      className="inline-flex items-center gap-2 py-1 text-[13px] font-medium text-[#A1A1A1] animate-fade-in"
      role="status"
      aria-live="polite"
    >
      {config.type === 'search' && <Search className="h-3.5 w-3.5 animate-pulse text-[#A1A1A1]" />}
      {config.type === 'analyze' && <Loader2 className="h-3.5 w-3.5 animate-spin text-[#A1A1A1]" />}
      {config.type === 'generate' && <Sparkles className="h-3.5 w-3.5 animate-pulse text-[#A1A1A1]" />}
      <span>{config.label}</span>
    </div>
  );
}
