import React, { useState } from 'react';
import { Copy, Check, FileText } from 'lucide-react';

/**
 * Enhanced Markdown, Code Block, Table, and Math Renderer
 * Formats headers, lists, syntax-highlighted code blocks with copy,
 * tables with titanium borders, math expressions, and clickable citation tags.
 */
export default function MarkdownRenderer({ content = '', onCitationClick }) {
  if (!content) return null;

  // Helper to render citation tags [Filename, p. X] as clickable pills
  const renderTextWithCitations = (text) => {
    const citationRegex = /\[([^\]]+,\s*p\.\s*\d+|[^\]]+,\s*Page\s*\d+|Page\s*\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const citationText = match[1];
      const pageMatch = citationText.match(/p\.\s*(\d+)/i) || citationText.match(/Page\s*(\d+)/i);
      const pageNum = pageMatch ? parseInt(pageMatch[1], 10) : 1;
      const filenameMatch = citationText.split(',')[0].trim();

      parts.push(
        <button
          key={`cite_${match.index}`}
          onClick={() => {
            if (onCitationClick) {
              onCitationClick({ filename: filenameMatch, page_number: pageNum });
            }
          }}
          className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-[#F5C542]/15 text-[#F5C542] border border-[#F5C542]/40 hover:bg-[#F5C542]/25 hover:border-[#F5C542] transition cursor-pointer select-none"
          title={`Jump to ${filenameMatch} page ${pageNum}`}
        >
          <FileText className="w-3 h-3 text-[#F5C542]" />
          <span>{citationText}</span>
        </button>
      );

      lastIndex = citationRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  // Parse lines into blocks (code blocks, block math, headers, lists, tables, paragraphs)
  const lines = content.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Code Block ```lang
    if (line.trim().startsWith('```')) {
      const lang = line.trim().slice(3).trim() || 'text';
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      const codeString = codeLines.join('\n');

      elements.push(
        <CodeBlock key={`code_${i}`} code={codeString} language={lang} />
      );
      continue;
    }

    // 2. Block Math $$ formula $$
    if (line.trim().startsWith('$$')) {
      const mathLines = [];
      if (line.trim().length > 2 && line.trim().endsWith('$$') && line.trim() !== '$$') {
        mathLines.push(line.trim().slice(2, -2).trim());
        i++;
      } else {
        i++;
        while (i < lines.length && !lines[i].trim().startsWith('$$')) {
          mathLines.push(lines[i]);
          i++;
        }
        i++; // skip closing $$
      }
      const formula = mathLines.join('\n');
      elements.push(
        <div
          key={`math_${i}`}
          className="my-3 p-3.5 bg-[#17191B] border border-[#30353A] rounded-xl text-center font-mono text-sm text-[#F5C542] overflow-x-auto shadow-inner"
        >
          {formula}
        </div>
      );
      continue;
    }

    // 3. Headers
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={`h4_${i}`} className="text-sm font-bold text-[#F2F3F4] mt-4 mb-1.5 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#F5C542]" />
          {renderTextWithCitations(line.replace('### ', ''))}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={`h3_${i}`} className="text-base font-bold text-[#F2F3F4] mt-5 mb-2 border-b border-[#30353A] pb-1.5">
          {renderTextWithCitations(line.replace('## ', ''))}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={`h2_${i}`} className="text-lg font-bold text-[#F2F3F4] mt-6 mb-2.5">
          {renderTextWithCitations(line.replace('# ', ''))}
        </h2>
      );
      i++;
      continue;
    }

    // 4. Bullet lists
    if (line.trim().startsWith('* ') || line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
      const listItems = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith('* ') ||
          lines[i].trim().startsWith('- ') ||
          lines[i].trim().startsWith('• '))
      ) {
        const itemText = lines[i].trim().replace(/^[\*\-•]\s*/, '');
        listItems.push(itemText);
        i++;
      }
      elements.push(
        <ul key={`ul_${i}`} className="list-disc list-outside pl-5 my-2 space-y-1.5 text-sm text-[#F2F3F4]/90">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderFormattedInline(item, onCitationClick)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 5. Tables
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const tableRows = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const rowStr = lines[i].trim();
        // Skip separator row |---|---|
        if (!rowStr.replace(/\||\-|\s/g, '')) {
          i++;
          continue;
        }
        const cells = rowStr
          .slice(1, -1)
          .split('|')
          .map((c) => c.trim());
        tableRows.push(cells);
        i++;
      }

      if (tableRows.length > 0) {
        const [headers, ...rows] = tableRows;
        elements.push(
          <div key={`table_${i}`} className="my-3 overflow-x-auto border border-[#30353A] rounded-xl shadow-lg">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#17191B] text-[#F2F3F4] font-semibold border-b border-[#30353A]">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3.5 py-2.5 font-mono text-[11px] text-[#A2A9B0] uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30353A]/50 bg-[#101214]">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-[#1A1D20]/70 transition">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3.5 py-2 text-[#F2F3F4]/90">
                        {renderFormattedInline(cell, onCitationClick)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 6. Empty line
    if (!line.trim()) {
      elements.push(<div key={`sp_${i}`} className="h-2" />);
      i++;
      continue;
    }

    // 7. Regular Paragraph
    elements.push(
      <p key={`p_${i}`} className="my-1.5 leading-relaxed text-sm text-[#F2F3F4]/90">
        {renderFormattedInline(line, onCitationClick)}
      </p>
    );
    i++;
  }

  return <div className="space-y-1">{elements}</div>;
}

function renderFormattedInline(text, onCitationClick) {
  // Inline math $...$
  const mathParts = text.split(/(\$[^\$]+\$)/g);
  return mathParts.map((mPart, mIdx) => {
    if (mPart.startsWith('$') && mPart.endsWith('$') && mPart.length > 2) {
      return (
        <span
          key={`math_${mIdx}`}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-[#17191B] border border-[#30353A] font-mono text-xs text-[#F5C542]"
        >
          {mPart.slice(1, -1)}
        </span>
      );
    }

    // Bold formatting **text**
    const parts = mPart.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={`${mIdx}_${index}`} className="font-semibold text-[#F2F3F4]">
            {renderInlineCitations(part.slice(2, -2), onCitationClick)}
          </strong>
        );
      }
      // Inline code `code`
      const codeParts = part.split(/(`[^`]+`)/g);
      return codeParts.map((sub, sIdx) => {
        if (sub.startsWith('`') && sub.endsWith('`')) {
          return (
            <code
              key={`${mIdx}_${index}_${sIdx}`}
              className="px-1.5 py-0.5 mx-0.5 rounded bg-[#17191B] border border-[#30353A] font-mono text-xs text-[#F5C542]"
            >
              {sub.slice(1, -1)}
            </code>
          );
        }
        return renderInlineCitations(sub, onCitationClick);
      });
    });
  });
}

function renderInlineCitations(text, onCitationClick) {
  const citationRegex = /\[([^\]]+,\s*p\.\s*\d+|[^\]]+,\s*Page\s*\d+|Page\s*\d+)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const citationText = match[1];
    const pageMatch = citationText.match(/p\.\s*(\d+)/i) || citationText.match(/Page\s*(\d+)/i);
    const pageNum = pageMatch ? parseInt(pageMatch[1], 10) : 1;
    const filenameMatch = citationText.split(',')[0].trim();

    parts.push(
      <button
        key={`cite_${match.index}`}
        onClick={() => {
          if (onCitationClick) {
            onCitationClick({ filename: filenameMatch, page_number: pageNum });
          }
        }}
        className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-[#F5C542]/15 text-[#F5C542] border border-[#F5C542]/40 hover:bg-[#F5C542]/30 hover:border-[#F5C542] transition cursor-pointer select-none align-baseline"
        title={`Jump to ${filenameMatch} page ${pageNum}`}
      >
        <FileText className="w-3 h-3 text-[#F5C542]" />
        <span>{citationText}</span>
      </button>
    );

    lastIndex = citationRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

function CodeBlock({ code, language }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl border border-[#30353A] bg-[#101214] overflow-hidden text-xs shadow-xl">
      <div className="flex items-center justify-between px-3.5 py-2 bg-[#17191B] border-b border-[#30353A] text-[#A2A9B0] font-mono">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500/60 inline-block" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/60 inline-block" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60 inline-block" />
          <span className="uppercase text-[10px] tracking-wider font-semibold text-[#F5C542] ml-1">{language}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-[#A2A9B0] hover:text-[#F2F3F4] px-2 py-0.5 rounded hover:bg-[#1A1D20] transition"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy code'}</span>
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-[#F2F3F4] font-mono leading-relaxed bg-[#101214]">
        <code>{code}</code>
      </pre>
    </div>
  );
}
