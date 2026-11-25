import React from 'react';
import { FileText, GitCompareArrows, Search, Lightbulb } from 'lucide-react';

const SUGGESTIONS = [
  {
    label: 'Summarize my documents.',
    prompt: 'Summarize my uploaded documents with the key takeaways and conclusions.',
    icon: FileText,
  },
  {
    label: 'Compare two research papers.',
    prompt: 'Compare the research papers in my library and highlight agreements, contradictions, and differences.',
    icon: GitCompareArrows,
  },
  {
    label: 'Find important information.',
    prompt: 'Find the most important findings, metrics, and evidence across my uploaded documents.',
    icon: Search,
  },
  {
    label: 'Explain a complex topic.',
    prompt: 'Explain the most complex topic in my documents in simple, accessible language.',
    icon: Lightbulb,
  },
];

export default function WelcomeScreen({ onPrompt }) {
  return (
    <div className="mx-auto flex h-full w-full max-w-[800px] flex-col items-center justify-center px-4 py-10 animate-fade-in">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-[#ECECEC] sm:text-[28px]">
          What can I help you understand?
        </h1>
        <p className="mt-2 text-sm text-[#A1A1A1]">
          Explore your documents, uncover insights, and research with AI.
        </p>
      </div>

      <div className="grid w-full max-w-xl grid-cols-1 gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map(({ label, prompt, icon: Icon }) => (
          <button
            key={label}
            type="button"
            onClick={() => onPrompt?.(prompt)}
            className="group flex items-center gap-3 rounded-2xl border border-[#3A3A3A] bg-[#2A2A2A]/70 px-4 py-3 text-left transition-colors hover:bg-[#2F2F2F]"
          >
            <Icon className="h-4 w-4 flex-shrink-0 text-[#A1A1A1] transition-colors group-hover:text-[#ECECEC]" />
            <span className="text-[13px] font-medium text-[#ECECEC]">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
