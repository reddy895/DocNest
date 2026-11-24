import React, { useMemo, useState } from 'react';
import {
  Layers,
  MessageSquare,
  Files,
  BookOpen,
  Bookmark,
  Settings as SettingsIcon,
  Plus,
  UploadCloud,
  Search,
  Pin,
  Trash2,
  Edit2,
  Check,
  ChevronLeft,
  ChevronRight,
  Settings,
} from 'lucide-react';
import { cn } from '../../lib/cn';

export const PRIMARY_NAV = [
  { id: 'library', name: 'Document Library', icon: Files },
  { id: 'chat', name: 'Research Workspace', icon: MessageSquare },
  { id: 'notes', name: 'Saved Notes', icon: Bookmark },
  { id: 'research', name: 'Research Studio', icon: BookOpen },
  { id: 'settings', name: 'Settings', icon: SettingsIcon },
];

function ConversationRow({
  session,
  active,
  collapsed,
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
  if (collapsed) return null;

  if (editing) {
    return (
      <div className="flex items-center gap-1 px-2 py-1">
        <input
          value={editTitle}
          onChange={(event) => onEditTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') onSaveEdit();
            if (event.key === 'Escape') onCancelEdit();
          }}
          autoFocus
          className="dn-input w-full px-1.5 py-0.5 text-xs"
          aria-label="Conversation title"
        />
        <button
          type="button"
          onClick={onSaveEdit}
          className="rounded p-1 text-emerald-300 hover:bg-emerald-500/10"
          aria-label="Save title"
        >
          <Check className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div
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
        'group flex cursor-pointer items-center justify-between rounded-md px-2.5 py-1.5 transition-colors',
        active
          ? 'bg-surface text-brand'
          : 'text-muted hover:bg-surface hover:text-foreground'
      )}
    >
      <div className="flex min-w-0 items-center gap-2">
        <MessageSquare
          className={cn('h-3.5 w-3.5 flex-shrink-0', session.is_pinned ? 'text-brand' : 'text-muted-dim')}
        />
        <span className="truncate text-xs">{session.title}</span>
      </div>
      <div className="ml-1 hidden flex-shrink-0 items-center gap-0.5 group-hover:flex group-focus-within:flex">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onStartEdit();
          }}
          className="rounded p-1 text-muted-dim hover:bg-background hover:text-foreground"
          aria-label="Rename conversation"
        >
          <Edit2 className="h-3 w-3" />
        </button>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onPin();
          }}
          className="rounded p-1 text-muted-dim hover:bg-background hover:text-brand"
          aria-label={session.is_pinned ? 'Unpin conversation' : 'Pin conversation'}
        >
          <Pin className={cn('h-3 w-3', session.is_pinned && 'fill-brand text-brand')} />
        </button>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onDelete();
          }}
          className="rounded p-1 text-muted-dim hover:bg-rose-500/10 hover:text-rose-300"
          aria-label="Delete conversation"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({
  activeTab,
  onNavigate,
  onNewChat,
  onOpenUpload,
  systemStatus,
  mobile = false,
  isCollapsed = false,
  onToggleCollapse,
  sessions = [],
  activeSessionId = null,
  onSelectSession,
  onRenameSession,
  onPinSession,
  onDeleteSession,
  currentUser,
  onOpenProfile,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const collapsed = mobile ? false : isCollapsed;
  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';
  const configuredModel = systemStatus?.components?.ollama?.configured_model || 'llama3.2';

  const { pinnedSessions, recentSessions } = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const filtered = query
      ? sessions.filter((session) => (session.title || '').toLowerCase().includes(query))
      : sessions;
    return {
      pinnedSessions: filtered.filter((session) => session.is_pinned),
      recentSessions: filtered.filter((session) => !session.is_pinned).slice(0, 20),
    };
  }, [sessions, searchQuery]);

  const startRename = (session) => {
    setEditingSessionId(session.id);
    setEditTitle(session.title || '');
  };

  const saveRename = (sessionId) => {
    const title = editTitle.trim();
    if (title) onRenameSession?.(sessionId, title);
    setEditingSessionId(null);
  };

  const selectSession = (sessionId) => {
    onSelectSession?.(sessionId);
    onNavigate?.('chat');
  };

  const renderConversationGroup = (title, items, icon) => {
    if (collapsed || items.length === 0) return null;
    return (
      <div className="space-y-0.5">
        <div className="flex items-center gap-1 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-dim">
          {icon}
          <span>{title}</span>
        </div>
        {items.map((session) => (
          <ConversationRow
            key={session.id}
            session={session}
            active={activeSessionId === session.id && activeTab === 'chat'}
            collapsed={collapsed}
            editing={editingSessionId === session.id}
            editTitle={editTitle}
            onEditTitle={setEditTitle}
            onStartEdit={() => startRename(session)}
            onSaveEdit={() => saveRename(session.id)}
            onCancelEdit={() => setEditingSessionId(null)}
            onSelect={() => selectSession(session.id)}
            onPin={() => onPinSession?.(session.id, !session.is_pinned)}
            onDelete={() => onDeleteSession?.(session.id)}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col bg-surface-raised text-foreground">
      <div className={cn('flex items-center border-b border-border py-3.5', collapsed ? 'justify-center px-2' : 'justify-between px-3.5')}>
        <button
          type="button"
          onClick={() => onNavigate?.('chat')}
          className="flex min-w-0 items-center gap-2.5 text-left"
          aria-label="DocNest home"
        >
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground">
            <Layers className="h-4 w-4" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <span className="block truncate text-base font-bold leading-tight tracking-tight">DocNest</span>
              <span className="block truncate font-mono text-[10px] uppercase tracking-wider text-muted-dim">
                Document Intelligence
              </span>
            </div>
          )}
        </button>

        {!mobile && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="rounded-md p-1.5 text-muted-dim transition-colors hover:bg-surface hover:text-foreground"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        )}
      </div>

      <div className={cn('p-3', collapsed && 'px-2')}>
        <button
          type="button"
          onClick={() => {
            onNewChat?.();
            onNavigate?.('chat');
          }}
          className={cn(
            'flex w-full items-center justify-center gap-2 rounded-lg bg-brand py-2 text-xs font-bold text-brand-foreground transition-colors hover:bg-brand-hover',
            collapsed ? 'px-2' : 'px-3'
          )}
          title="New Chat"
        >
          <Plus className="h-4 w-4 flex-shrink-0" strokeWidth={2.5} />
          {!collapsed && <span>New Chat</span>}
        </button>
      </div>

      {!collapsed && (
        <div className="px-2 pb-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-muted-dim" />
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search conversations..."
              className="dn-input w-full py-1.5 pl-7 pr-2 text-[11px]"
              aria-label="Search conversations"
            />
          </div>
        </div>
      )}

      <nav className={cn('space-y-0.5 pb-2', collapsed ? 'px-2' : 'px-2')} aria-label="Primary">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate?.(item.id)}
              aria-current={isActive ? 'page' : undefined}
              title={item.name}
              className={cn(
                'flex w-full items-center rounded-lg py-2 text-xs font-medium transition-colors',
                collapsed ? 'justify-center px-2' : 'gap-2.5 px-2.5',
                isActive
                  ? 'border-l-2 border-brand bg-surface text-brand'
                  : 'border-l-2 border-transparent text-muted hover:bg-surface hover:text-foreground'
              )}
            >
              <Icon className={cn('h-4 w-4 flex-shrink-0', isActive ? 'text-brand' : 'text-muted-dim')} />
              {!collapsed && <span className="truncate">{item.name}</span>}
            </button>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="flex-1 space-y-3 overflow-y-auto border-t border-border px-2 py-2">
          {renderConversationGroup('Pinned', pinnedSessions, <Pin className="h-3 w-3 text-brand" />)}
          {renderConversationGroup('Recent', recentSessions, <MessageSquare className="h-3 w-3" />)}
          {sessions.length === 0 && (
            <p className="px-2 py-3 text-[11px] italic text-muted-dim">No conversations yet.</p>
          )}
          {sessions.length > 0 && pinnedSessions.length === 0 && recentSessions.length === 0 && (
            <p className="px-2 py-3 text-[11px] italic text-muted-dim">No matches found.</p>
          )}
        </div>
      )}
      {collapsed && <div className="flex-1" />}

      <div className={cn('space-y-2 border-t border-border p-3', collapsed && 'px-2')}>
        {onOpenUpload && (
          <button
            type="button"
            onClick={onOpenUpload}
            className={cn(
              'flex w-full items-center justify-center rounded-lg border border-border bg-surface py-1.5 text-[11px] font-medium text-foreground transition-colors hover:border-brand/50',
              collapsed ? 'px-2' : 'gap-2 px-2'
            )}
            title="Upload Document"
          >
            <UploadCloud className="h-3.5 w-3.5 flex-shrink-0 text-brand" />
            {!collapsed && <span>Upload Document</span>}
          </button>
        )}

        <div
          className={cn(
            'flex items-center rounded-lg border border-border bg-surface px-2 py-2',
            collapsed ? 'justify-center' : 'justify-between'
          )}
          title={`Ollama: ${isOllamaConnected ? 'connected' : 'unavailable'}`}
        >
          <div className="flex min-w-0 items-center gap-2">
            <span
              className={cn(
                'h-2 w-2 flex-shrink-0 rounded-full',
                isOllamaConnected ? 'bg-emerald-400' : 'animate-pulse bg-amber-400'
              )}
            />
            {!collapsed && (
              <span className="truncate font-mono text-xs text-foreground">{configuredModel}</span>
            )}
          </div>
          {!collapsed && <span className="font-mono text-[10px] text-muted-dim">local</span>}
        </div>

        <button
          type="button"
          onClick={onOpenProfile}
          className={cn(
            'flex w-full items-center rounded-lg border border-border bg-surface px-2 py-2 text-left transition-colors hover:border-brand/40',
            collapsed ? 'justify-center' : 'justify-between gap-2'
          )}
          title="Account and preferences"
        >
          <div className={cn('flex min-w-0 items-center', collapsed ? '' : 'gap-2.5')}>
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-brand/40 bg-brand/10 text-[10px] font-bold text-brand">
              {(currentUser?.username || currentUser?.full_name || 'U').charAt(0).toUpperCase()}
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <span className="block truncate text-xs font-semibold leading-tight text-foreground">
                  {currentUser?.full_name || currentUser?.username || 'Local Researcher'}
                </span>
                <span className="block truncate font-mono text-[10px] text-muted-dim">
                  {currentUser?.workspace_name || 'Default Workspace'}
                </span>
              </div>
            )}
          </div>
          {!collapsed && <Settings className="h-3.5 w-3.5 flex-shrink-0 text-muted-dim" />}
        </button>
      </div>
    </div>
  );
}
