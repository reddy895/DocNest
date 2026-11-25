import React from 'react';

export default function ThinkingIndicator({ label = 'Thinking...' }) {
  return (
    <div className="inline-flex items-center gap-2.5 py-1 text-sm text-[#A1A1A1] animate-fade-in" role="status" aria-live="polite">
      <span className="flex items-center gap-1" aria-hidden="true">
        <span className="h-1.5 w-1.5 rounded-full bg-[#A1A1A1] animate-bounce [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#A1A1A1] animate-bounce [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#A1A1A1] animate-bounce" />
      </span>
      <span className="text-[13px] font-medium text-[#A1A1A1]">{label}</span>
    </div>
  );
}
