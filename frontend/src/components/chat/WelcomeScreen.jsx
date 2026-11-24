import React from 'react';
import {
  Sparkles,
  FileText,
  Lightbulb,
  GitCompareArrows,
  Search,
  ListFilter,
  ArrowUpRight,
} from 'lucide-react';

const SUGGESTIONS = [
  {
    label: 'Summarize my documents',
    description: 'Synthesize the core takeaways and conclusions across your library.',
    prompt: 'Summarize my uploaded documents with the key takeaways and conclusions.',
    icon: FileText,
  },
  {
    label: 'Explain a complex topic',
    description: 'Turn dense material into a clear, accessible explanation.',
    prompt: 'Explain the most complex topic in my documents in simple, accessible language.',
    icon: Lightbulb,
  },
  {
    label: 'Compare research papers',
    description: 'Surface agreements, contradictions, and methodological differences.',
    prompt: 'Compare the research papers in my library and highlight agreements, contradictions, and differences.',
    icon: GitCompareArrows,
  },
  {
    label: 'Find important findings',
    description: 'Locate the strongest evidence and highest-signal results.',
    prompt: 'Find the most important findings and evidence across my uploaded documents.',
    icon: Search,
  },
  {
    label: 'Extract key information',
    description: 'Pull out dates, metrics, entities, and action items with citations.',
    prompt: 'Extract the key information from my documents, including dates, metrics, and action items, with citations.',
    icon: ListFilter,
    wide: true,
  },
];

export default function WelcomeScreen({ onPrompt, documentCount = 0 }) {
  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col items-center justify-center py-10 animate-fade-in">
      <div className="mb-8 flex flex-col items-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-brand/20 bg-brand/10 text-brand shadow-carbon-sm">
          <Sparkles className="h-6 w-6" />
        </div>
        <h1 className="max-w-2xl text-balance text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Your documents. Your knowledge. One intelligent workspace.
        </h1>
        <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted">
          Explore your documents, ask better questions, and turn information into insights.
        </p>
        {documentCount > 0 && (
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-muted-dim">
            {documentCount} {documentCount === 1 ? 'document' : 'documents'} indexed
          </p>
        )}
      </div>

      <div className="grid w-full grid-cols-1 gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map(({ label, description, prompt, icon: Icon, wide }) => (
          <button
            key={label}
            type="button"
            onClick={() => onPrompt?.(prompt)}
            className={`group flex items-start gap-3 rounded-xl border border-border bg-surface-raised p-3.5 text-left transition-all duration-150 hover:border-brand/40 hover:bg-surface focus-visible:border-brand ${
              wide ? 'sm:col-span-2' : ''
            }`}
          >
            <span className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-border-subtle bg-surface text-muted-dim transition-colors group-hover:border-brand/30 group-hover:text-brand">
              <Icon className="h-4 w-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-foreground transition-colors group-hover:text-brand">
                  {label}
                </span>
                <ArrowUpRight className="h-3.5 w-3.5 flex-shrink-0 text-muted-dim opacity-0 transition-opacity group-hover:opacity-100" />
              </span>
              <span className="mt-0.5 block text-[11px] leading-relaxed text-muted-dim">{description}</span>
            </span>
          </button>
        ))}
      </div>

      <p className="mt-6 font-mono text-[10px] uppercase tracking-wider text-muted-dim">
        Select a prompt to start, or ask your own question below
      </p>
    </div>
  );
}
