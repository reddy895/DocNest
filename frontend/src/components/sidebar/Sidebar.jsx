import React from 'react';
import {
  Layers,
  MessageSquare,
  Files,
  BookOpen,
  Settings as SettingsIcon,
  Plus,
  UploadCloud,
} from 'lucide-react';
import { cn } from '../../lib/cn';

export const PRIMARY_NAV = [
  { id: 'chat', name: 'Research Workspace', icon: MessageSquare },
  { id: 'library', name: 'Document Library', icon: Files },
  { id: 'research', name: 'Research Studio', icon: BookOpen },
  { id: 'settings', name: 'Settings', icon: SettingsIcon },
];

export default function Sidebar({
  activeTab,
  onNavigate,
  onNewChat,
  onOpenUpload,
  systemStatus,
  mobile = false,
}) {
  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';
  const configuredModel = systemStatus?.components?.ollama?.configured_model || 'llama3.2';

  return (
    <div className="flex h-full flex-col bg-surface-raised text-foreground">
      <div className="flex items-center gap-2.5 border-b border-border px-3.5 py-3.5">
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-brand text-brand-foreground">
          <Layers className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <span className="block truncate text-base font-bold leading-tight tracking-tight">DocNest</span>
          <span className="block truncate font-mono text-[10px] uppercase tracking-wider text-muted-dim">
            Document Intelligence
          </span>
        </div>
      </div>

      <div className="p-3">
        <button
          type="button"
          onClick={() => {
            onNewChat?.();
            onNavigate?.('chat');
          }}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-3 py-2 text-xs font-bold text-brand-foreground transition-colors hover:bg-brand-hover"
        >
          <Plus className="h-4 w-4" strokeWidth={2.5} />
          <span>New Chat</span>
        </button>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate?.(item.id)}
              aria-current={isActive ? 'page' : undefined}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-colors',
                isActive
                  ? 'border-l-2 border-brand bg-surface text-brand'
                  : 'border-l-2 border-transparent text-muted hover:bg-surface hover:text-foreground'
              )}
            >
              <Icon className={cn('h-4 w-4 flex-shrink-0', isActive ? 'text-brand' : 'text-muted-dim')} />
              <span className="truncate">{item.name}</span>
            </button>
          );
        })}
      </nav>

      <div className="space-y-2 border-t border-border p-3">
        {onOpenUpload && (
          <button
            type="button"
            onClick={onOpenUpload}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-surface px-2 py-1.5 text-[11px] font-medium text-foreground transition-colors hover:border-brand/50"
          >
            <UploadCloud className="h-3.5 w-3.5 text-brand" />
            <span>Upload Document</span>
          </button>
        )}

        <div
          className="flex items-center justify-between rounded-lg border border-border bg-surface px-2 py-2"
          title={`Ollama: ${isOllamaConnected ? 'connected' : 'unavailable'}`}
        >
          <div className="flex min-w-0 items-center gap-2">
            <span
              className={cn(
                'h-2 w-2 flex-shrink-0 rounded-full',
                isOllamaConnected ? 'bg-emerald-400' : 'animate-pulse bg-amber-400'
              )}
            />
            <span className="truncate font-mono text-xs text-foreground">{configuredModel}</span>
          </div>
          <span className="font-mono text-[10px] text-muted-dim">{mobile ? 'local' : 'local'}</span>
        </div>
      </div>
    </div>
  );
}
