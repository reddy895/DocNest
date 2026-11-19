import React, { useState } from 'react';
import { Copy, Check, FileText } from 'lucide-react';

/**
 * Lightweight Markdown & Code Block Renderer
 * Formats headers, lists, code blocks with copy, tables, and clickable citation tags.
 */
export default function MarkdownRenderer({ content = '', onCitationClick }) {
  if (!content) return null;

  // Helper to render citation tags [Filename, p. X] as clickable pills
  const renderTextWithCitations = (text) => {
    // Regex matches [Filename.ext, p. 1] or [Filename, p. 1] or [Page 1]
    const citationRegex = /\[([^\]]+,\s*p\.\s*\d+|[^\]]+,\s*Page\s*\d+|Page\s*\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const citationText = match[1];
      // Extract page number if present
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
          className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-[#E5B83D]/15 text-[#E5B83D] border border-[#E5B83D]/40 hover:bg-[#E5B83D]/25 hover:border-[#E5B83D] transition cursor-pointer select-none"
          title={`Jump to ${filenameMatch} page ${pageNum}`}
        >
          <FileText className="w-3 h-3 text-[#E5B83D]" />
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

  // Parse lines into blocks (code blocks, headers, lists, tables, paragraphs)
  const lines = content.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Code Block
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

    // 2. Headers
    if (line.startsWith('### ')) {
      elements.push(
        <h4 key={`h4_${i}`} className="text-sm font-bold text-[#F0F1F2] mt-4 mb-1.5">
          {renderTextWithCitations(line.replace('### ', ''))}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h3 key={`h3_${i}`} className="text-base font-bold text-[#F0F1F2] mt-5 mb-2 border-b border-[#343A3F]/50 pb-1">
          {renderTextWithCitations(line.replace('## ', ''))}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={`h2_${i}`} className="text-lg font-bold text-[#F0F1F2] mt-6 mb-2.5">
          {renderTextWithCitations(line.replace('# ', ''))}
        </h2>
      );
      i++;
      continue;
    }

    // 3. Bullet lists
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
        <ul key={`ul_${i}`} className="list-disc list-outside pl-5 my-2 space-y-1 text-sm text-[#F0F1F2]/90">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderFormattedInline(item, onCitationClick)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 4. Tables
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
          <div key={`table_${i}`} className="my-3 overflow-x-auto border border-[#343A3F] rounded-lg">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#191C1F] text-[#F0F1F2] font-semibold border-b border-[#343A3F]">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3 py-2">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#343A3F]/50">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-[#191C1F]/40 transition">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3 py-2 text-[#F0F1F2]/90">
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

    // 5. Empty line
    if (!line.trim()) {
      elements.push(<div key={`sp_${i}`} className="h-2" />);
      i++;
      continue;
    }

    // 6. Regular Paragraph
    elements.push(
      <p key={`p_${i}`} className="my-1.5 leading-relaxed text-sm text-[#F0F1F2]/90">
        {renderFormattedInline(line, onCitationClick)}
      </p>
    );
    i++;
  }

  return <div className="space-y-1">{elements}</div>;
}

function renderFormattedInline(text, onCitationClick) {
  // Bold formatting **text**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-[#F0F1F2]">
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
            key={`${index}_${sIdx}`}
            className="px-1.5 py-0.5 mx-0.5 rounded bg-[#191C1F] border border-[#343A3F] font-mono text-xs text-[#E5B83D]"
          >
            {sub.slice(1, -1)}
          </code>
        );
      }
      return renderInlineCitations(sub, onCitationClick);
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
        className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-[#E5B83D]/15 text-[#E5B83D] border border-[#E5B83D]/40 hover:bg-[#E5B83D]/30 hover:border-[#E5B83D] transition cursor-pointer select-none align-baseline"
        title={`Jump to ${filenameMatch} page ${pageNum}`}
      >
        <FileText className="w-3 h-3 text-[#E5B83D]" />
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
    <div className="my-3 rounded-lg border border-[#343A3F] bg-[#111315] overflow-hidden text-xs">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#191C1F] border-b border-[#343A3F] text-[#A0A6AC] font-mono">
        <span className="uppercase text-[10px] tracking-wider">{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] hover:text-[#F0F1F2] transition"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy code'}</span>
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-[#F0F1F2] font-mono leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}
