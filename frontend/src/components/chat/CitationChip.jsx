import React from 'react';
import { FileText } from 'lucide-react';

export default function CitationChip({
  filename,
  pageNumber = 1,
  sectionHeading,
  snippet,
  relevanceScore,
  onClick,
  inline = false,
}) {
  const shortName = filename && filename.length > 26 ? `${filename.slice(0, 23)}...` : filename || 'Source';
  const titleParts = [`${filename || 'Document'} (Page ${pageNumber})`];
  if (sectionHeading) titleParts.push(`Section: ${sectionHeading}`);
  if (typeof relevanceScore === 'number') titleParts.push(`Relevance: ${(relevanceScore * 100).toFixed(0)}%`);
  if (snippet) titleParts.push(`"${snippet.slice(0, 140)}..."`);

  if (inline) {
    return (
      <button
        type="button"
        onClick={onClick}
        title={titleParts.join('\n')}
        className="mx-0.5 inline-flex items-center gap-1 rounded-md border border-[#3A3A3A] bg-[#2A2A2A] px-1.5 py-0.5 align-baseline font-mono text-[11px] text-[#ECECEC] transition-colors hover:border-[#555555] hover:bg-[#3A3A3A]"
      >
        <FileText className="h-3 w-3 text-[#A1A1A1]" />
        <span>
          {shortName}, p.{pageNumber}
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      title={titleParts.join('\n')}
      className="group inline-flex items-center gap-1.5 rounded-full border border-[#3A3A3A] bg-[#2A2A2A] px-2.5 py-1 text-xs text-[#ECECEC] transition-colors hover:border-[#555555] hover:bg-[#2F2F2F]"
    >
      <FileText className="h-3 w-3 flex-shrink-0 text-[#A1A1A1] group-hover:text-[#ECECEC]" />
      <span className="max-w-[160px] truncate font-medium">{shortName}</span>
      <span className="text-[11px] text-[#A1A1A1]">p.{pageNumber}</span>
    </button>
  );
}

