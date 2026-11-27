import React, { useState } from 'react';
import { Copy, Check, Edit2, Paperclip } from 'lucide-react';

export default function UserMessage({
  message,
  onEditSubmit,
  isStreaming = false,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.text || '');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!message.text) return;
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleSave = () => {
    const trimmed = editText.trim();
    if (!trimmed) return;
    setIsEditing(false);
    onEditSubmit?.(message.id, trimmed);
  };

  if (isEditing) {
    return (
      <div className="flex w-full justify-end animate-fade-in">
        <div className="w-full max-w-2xl rounded-2xl border border-[#3A3A3A] bg-[#303030] p-3">
          <textarea
            value={editText}
            onChange={(event) => setEditText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleSave();
              }
              if (event.key === 'Escape') {
                setIsEditing(false);
                setEditText(message.text || '');
              }
            }}
            rows={3}
            autoFocus
            className="w-full resize-none bg-transparent text-[15px] leading-relaxed text-[#ECECEC] focus:outline-none"
          />
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setIsEditing(false);
                setEditText(message.text || '');
              }}
              className="rounded-full border border-[#3A3A3A] px-3 py-1 text-xs font-medium text-[#ECECEC] transition-colors hover:bg-[#3A3A3A]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="rounded-full bg-[#F0F0F0] px-3 py-1 text-xs font-medium text-[#171717] transition-colors hover:bg-white"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group flex w-full flex-col items-end gap-1 animate-fade-in">
      {message.attachments && message.attachments.length > 0 && (
        <div className="flex flex-wrap justify-end gap-1.5 mb-1">
          {message.attachments.map((file, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#3A3A3A] bg-[#2A2A2A] px-2.5 py-1 text-xs text-[#ECECEC]"
            >
              <Paperclip className="h-3 w-3 text-[#A1A1A1]" />
              <span className="max-w-[160px] truncate">{file.name || file}</span>
            </span>
          ))}
        </div>
      )}

      <div className="max-w-[85%] sm:max-w-[75%] rounded-3xl bg-[#2F2F2F] px-4 py-2.5 text-[15px] leading-relaxed text-[#ECECEC] whitespace-pre-wrap break-words">
        {message.text}
      </div>

      <div className="flex items-center gap-1 pr-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-md p-1 text-[#777777] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
          title="Copy message"
          aria-label="Copy message"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
        {!isStreaming && onEditSubmit && (
          <button
            type="button"
            onClick={() => {
              setEditText(message.text || '');
              setIsEditing(true);
            }}
            className="rounded-md p-1 text-[#777777] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
            title="Edit message"
            aria-label="Edit message"
          >
            <Edit2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

