import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

function highlightLine(line) {
  // Lightweight token highlighting for readability without heavy bundle bloat
  const trimmed = line.trim();
  if (trimmed.startsWith('//') || trimmed.startsWith('#')) {
    return <span className="text-[#777777] italic">{line}</span>;
  }

  const tokenRegex =
    /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:import|from|export|default|const|let|var|function|return|async|await|if|else|elif|for|while|class|def|try|except|finally|raise|true|false|null|None|True|False)\b|\b\d+(?:\.\d+)?\b)/g;

  const parts = [];
  let lastIdx = 0;
  let match;

  while ((match = tokenRegex.exec(line)) !== null) {
    if (match.index > lastIdx) {
      parts.push(line.slice(lastIdx, match.index));
    }
    const token = match[0];
    let cls = 'text-[#ECECEC]';
    if (token.startsWith('"') || token.startsWith("'") || token.startsWith('`')) {
      cls = 'text-[#A5D6A7]';
    } else if (/^\d/.test(token)) {
      cls = 'text-[#D4D4D4] font-medium';
    } else {
      cls = 'text-[#C5C8C6] font-semibold';
    }
    parts.push(
      <span key={match.index} className={cls}>
        {token}
      </span>
    );
    lastIdx = tokenRegex.lastIndex;
  }

  if (lastIdx < line.length) {
    parts.push(line.slice(lastIdx));
  }
  return parts.length > 0 ? parts : line;
}

export default function CodeBlock({ code = '', language = 'text' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const lines = code.split('\n');

  return (
    <div className="my-3 overflow-hidden rounded-xl border border-[#2E2E2E] bg-[#171717]">
      <div className="flex items-center justify-between bg-[#2A2A2A] px-3.5 py-1.5 text-xs text-[#A1A1A1]">
        <span className="font-mono text-[11px] lowercase">{language || 'text'}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] text-[#A1A1A1] transition-colors hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-[#ECECEC]">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <div className="overflow-x-auto p-3.5">
        <pre className="m-0 font-mono text-[13px] leading-relaxed text-[#ECECEC]">
          <code>
            {lines.map((line, idx) => (
              <div key={idx} className="whitespace-pre">
                {highlightLine(line)}
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}
