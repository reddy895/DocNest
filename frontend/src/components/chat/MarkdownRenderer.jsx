import React from 'react';
import CodeBlock from './CodeBlock';
import CitationChip from './CitationChip';

/**
 * ChatGPT-style Markdown, Code Block, Table, List, Blockquote, and Math Renderer
 * Uses neutral dark typography and clickable CitationChip tags.
 */
export default function MarkdownRenderer({ content = '', onCitationClick }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Code Block ```lang
    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim() || 'text';
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <CodeBlock key={`code_${i}`} code={codeLines.join('\n')} language={lang} />
      );
      continue;
    }

    // 2. Block Math $$ formula $$
    if (trimmed.startsWith('$$')) {
      const mathLines = [];
      if (trimmed.length > 2 && trimmed.endsWith('$$') && trimmed !== '$$') {
        mathLines.push(trimmed.slice(2, -2).trim());
        i++;
      } else {
        i++;
        while (i < lines.length && !lines[i].trim().startsWith('$$')) {
          mathLines.push(lines[i]);
          i++;
        }
        i++; // skip closing $$
      }
      elements.push(
        <div
          key={`math_${i}`}
          className="my-3 overflow-x-auto rounded-xl border border-[#2E2E2E] bg-[#171717] p-3.5 text-center font-mono text-sm text-[#ECECEC]"
        >
          {mathLines.join('\n')}
        </div>
      );
      continue;
    }

    // 3. Horizontal Rule
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      elements.push(<hr key={`hr_${i}`} className="my-4 border-[#2E2E2E]" />);
      i++;
      continue;
    }

    // 4. Headings
    if (line.startsWith('#### ')) {
      elements.push(
        <h4 key={`h4_${i}`} className="mt-4 mb-1.5 text-[15px] font-semibold text-[#ECECEC]">
          {renderFormattedInline(line.slice(5), onCitationClick)}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3_${i}`} className="mt-5 mb-2 text-base font-semibold text-[#ECECEC]">
          {renderFormattedInline(line.slice(4), onCitationClick)}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={`h2_${i}`} className="mt-6 mb-2.5 text-lg font-semibold text-[#ECECEC]">
          {renderFormattedInline(line.slice(3), onCitationClick)}
        </h2>
      );
      i++;
      continue;
    }
    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={`h1_${i}`} className="mt-6 mb-3 text-xl font-semibold text-[#ECECEC]">
          {renderFormattedInline(line.slice(2), onCitationClick)}
        </h1>
      );
      i++;
      continue;
    }

    // 5. Blockquotes
    if (trimmed.startsWith('> ')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].trim().startsWith('> ')) {
        quoteLines.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <blockquote
          key={`bq_${i}`}
          className="my-3 border-l-2 border-[#3A3A3A] pl-4 text-[15px] leading-relaxed text-[#A1A1A1]"
        >
          {quoteLines.map((qLine, qIdx) => (
            <p key={qIdx} className="my-1">
              {renderFormattedInline(qLine, onCitationClick)}
            </p>
          ))}
        </blockquote>
      );
      continue;
    }

    // 6. Unordered lists
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      const listItems = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith('* ') ||
          lines[i].trim().startsWith('- ') ||
          lines[i].trim().startsWith('• '))
      ) {
        listItems.push(lines[i].trim().replace(/^[\*\-•]\s*/, ''));
        i++;
      }
      elements.push(
        <ul key={`ul_${i}`} className="my-2.5 list-disc space-y-1.5 pl-6 text-[15px] text-[#ECECEC]">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-[1.7]">
              {renderFormattedInline(item, onCitationClick)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 7. Ordered lists
    if (/^\d+\.\s+/.test(trimmed)) {
      const orderedItems = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        orderedItems.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }
      elements.push(
        <ol key={`ol_${i}`} className="my-2.5 list-decimal space-y-1.5 pl-6 text-[15px] text-[#ECECEC]">
          {orderedItems.map((item, idx) => (
            <li key={idx} className="leading-[1.7]">
              {renderFormattedInline(item, onCitationClick)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 8. Tables
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const tableRows = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const rowStr = lines[i].trim();
        if (!rowStr.replace(/\||\-|\:|\s/g, '')) {
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
          <div key={`table_${i}`} className="my-3 overflow-x-auto rounded-xl border border-[#3A3A3A]">
            <table className="w-full text-left text-[13px]">
              <thead className="border-b border-[#3A3A3A] bg-[#2A2A2A] text-[#ECECEC]">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3.5 py-2.5 font-semibold">
                      {renderFormattedInline(h, onCitationClick)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2E2E2E] bg-[#212121]">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className="transition-colors hover:bg-[#2A2A2A]/60">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="px-3.5 py-2 text-[#ECECEC]">
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

    // 9. Empty line
    if (!trimmed) {
      elements.push(<div key={`sp_${i}`} className="h-1.5" />);
      i++;
      continue;
    }

    // 10. Regular Paragraph
    elements.push(
      <p key={`p_${i}`} className="my-1.5 text-[15px] leading-[1.7] text-[#ECECEC]">
        {renderFormattedInline(line, onCitationClick)}
      </p>
    );
    i++;
  }

  return <div className="prose-chatgpt space-y-1">{elements}</div>;
}

function renderFormattedInline(text, onCitationClick) {
  // Inline math $...$
  const mathParts = text.split(/(\$[^\$]+\$)/g);
  return mathParts.map((mPart, mIdx) => {
    if (mPart.startsWith('$') && mPart.endsWith('$') && mPart.length > 2) {
      return (
        <span
          key={`math_${mIdx}`}
          className="mx-0.5 rounded border border-[#3A3A3A] bg-[#2A2A2A] px-1.5 py-0.5 font-mono text-[13px] text-[#ECECEC]"
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
          <strong key={`${mIdx}_${index}`} className="font-semibold text-[#ECECEC]">
            {renderInlineCodeAndCitations(part.slice(2, -2), onCitationClick)}
          </strong>
        );
      }
      return renderInlineCodeAndCitations(part, onCitationClick);
    });
  });
}

function renderInlineCodeAndCitations(text, onCitationClick) {
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.map((sub, sIdx) => {
    if (sub.startsWith('`') && sub.endsWith('`') && sub.length > 2) {
      return (
        <code
          key={`ic_${sIdx}`}
          className="mx-0.5 rounded bg-[#2A2A2A] px-1.5 py-0.5 font-mono text-[13px] text-[#ECECEC]"
        >
          {sub.slice(1, -1)}
        </code>
      );
    }
    return renderInlineCitations(sub, onCitationClick);
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
      <CitationChip
        key={`cite_${match.index}`}
        inline
        filename={filenameMatch}
        pageNumber={pageNum}
        onClick={() => onCitationClick?.({ filename: filenameMatch, page_number: pageNum })}
      />
    );

    lastIndex = citationRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}
