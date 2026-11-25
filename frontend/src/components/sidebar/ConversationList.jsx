import React, { useMemo, useState, useEffect, useRef } from 'react';
import { MoreHorizontal, Edit2, Pin, Trash2, Check, X } from 'lucide-react';
import { cn } from '../../lib/cn';

function getDateBucket(isoString) {
  if (!isoString) return 'Today';
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return 'Older';

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfToday.getDate() - 1);
  const startOf7Days = new Date(startOfToday);
  startOf7Days.setDate(startOfToday.getDate() - 7);

  if (date >= startOfToday) return 'Today';
  if (date >= startOfYesterday) return 'Yesterday';
  if (date >= startOf7Days) return 'Previous 7 Days';
  return 'Older';
}

function ConversationRow({
  session,
  active,
  editing,
  editTitle,
  onEditTitle,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onSelect,
  onPin,
  onDelete,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  if (editing) {
    return (
      <div className="flex items-center gap-1 rounded-lg bg-[#2A2A2A] px-2 py-1.5">
        <input
          value={editTitle}
          onChange={(event) => onEditTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') onSaveEdit();
            if (event.key === 'Escape') onCancelEdit();
          }}
          autoFocus
          className="w-full bg-transparent text-[13px] text-[#ECECEC] focus:outline-none"
          aria-label="Conversation title"
        />
        <button
          type="button"
          onClick={onSaveEdit}
          className="rounded p-1 text-[#A1A1A1] hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
          aria-label="Save title"
        >
          <Check className="h-3.5 w-3.5" />
        </button>
        <button
          type="button"
          onClick={onCancelEdit}
          className="rounded p-1 text-[#A1A1A1] hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
          aria-label="Cancel rename"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div
      ref={menuRef}
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        'group relative flex cursor-pointer items-center justify-between rounded-lg px-2.5 py-2 text-[13px] transition-colors',
        active
          ? 'bg-[#2F2F2F] text-[#ECECEC] font-medium'
          : 'text-[#ECECEC]/85 hover:bg-[#2A2A2A] hover:text-[#ECECEC]'
      )}
    >
      <span className="truncate pr-2">{session.title || 'New chat'}</span>

      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          setMenuOpen((prev) => !prev);
        }}
        className={cn(
          'flex-shrink-0 rounded-md p-1 text-[#A1A1A1] transition-opacity hover:bg-[#3A3A3A] hover:text-[#ECECEC]',
          menuOpen || active ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
        )}
        aria-label="Conversation options"
        aria-expanded={menuOpen}
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {menuOpen && (
        <div
          onClick={(event) => event.stopPropagation()}
          className="absolute right-1 top-9 z-40 w-36 rounded-xl border border-[#3A3A3A] bg-[#2A2A2A] p-1 shadow-carbon-lg animate-fade-in"
        >
          <button
            type="button"
            onClick={() => {
              setMenuOpen(false);
              onStartEdit();
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs text-[#ECECEC] transition-colors hover:bg-[#3A3A3A]"
          >
            <Edit2 className="h-3.5 w-3.5 text-[#A1A1A1]" />
            <span>Rename</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setMenuOpen(false);
              onPin();
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs text-[#ECECEC] transition-colors hover:bg-[#3A3A3A]"
          >
            <Pin className="h-3.5 w-3.5 text-[#A1A1A1]" />
            <span>{session.is_pinned ? 'Unpin' : 'Pin'}</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setMenuOpen(false);
              onDelete();
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs text-rose-400 transition-colors hover:bg-[#3A3A3A]"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Delete</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default function ConversationList({
  sessions = [],
  activeSessionId = null,
  activeTab = 'chat',
  searchQuery = '',
  collapsed = false,
  onSelectSession,
  onRenameSession,
  onPinSession,
  onDeleteSession,
}) {
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const grouped = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const filtered = query
      ? sessions.filter((s) => (s.title || '').toLowerCase().includes(query))
      : sessions;

    const buckets = {
      Pinned: [],
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: [],
    };

    for (const session of filtered) {
      if (session.is_pinned) {
        buckets.Pinned.push(session);
      } else {
        const bucket = getDateBucket(session.updated_at || session.created_at);
        buckets[bucket].push(session);
      }
    }

    return Object.entries(buckets).filter(([, items]) => items.length > 0);
  }, [sessions, searchQuery]);

  if (collapsed) return null;

  const startRename = (session) => {
    setEditingSessionId(session.id);
    setEditTitle(session.title || '');
  };

  const saveRename = (sessionId) => {
    const title = editTitle.trim();
    if (title) onRenameSession?.(sessionId, title);
    setEditingSessionId(null);
  };

  if (grouped.length === 0) {
    return (
      <div className="px-2.5 py-4 text-xs text-[#777777]">
        {searchQuery.trim() ? 'No matching chats' : 'No recent conversations'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {grouped.map(([groupName, items]) => (
        <div key={groupName} className="space-y-0.5">
          <div className="px-2.5 py-1 text-[11px] font-medium text-[#777777]">
            {groupName}
          </div>
          {items.map((session) => (
            <ConversationRow
              key={session.id}
              session={session}
              active={activeSessionId === session.id && activeTab === 'chat'}
              editing={editingSessionId === session.id}
              editTitle={editTitle}
              onEditTitle={setEditTitle}
              onStartEdit={() => startRename(session)}
              onSaveEdit={() => saveRename(session.id)}
              onCancelEdit={() => setEditingSessionId(null)}
              onSelect={() => onSelectSession?.(session.id)}
              onPin={() => onPinSession?.(session.id, !session.is_pinned)}
              onDelete={() => onDeleteSession?.(session.id)}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
