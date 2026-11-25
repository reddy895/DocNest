import React, { useState, useRef } from 'react';
import {
  Layers,
  SquarePen,
  Search,
  Files,
  BookOpen,
  Bookmark,
  Settings as SettingsIcon,
  PanelLeftClose,
  PanelLeftOpen,
  UploadCloud,
  X,
} from 'lucide-react';
import { cn } from '../../lib/cn';
import ConversationList from './ConversationList';

export const PRIMARY_NAV = [
  { id: 'library', name: 'Document library', icon: Files },
  { id: 'research', name: 'Research workspace', icon: BookOpen },
  { id: 'notes', name: 'Saved notes', icon: Bookmark },
];

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
  const [showSearch, setShowSearch] = useState(false);
  const searchInputRef = useRef(null);

  const collapsed = mobile ? false : isCollapsed;
  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';
  const configuredModel = systemStatus?.components?.ollama?.configured_model || 'llama3.2';

  const handleToggleSearch = () => {
    if (collapsed) {
      onToggleCollapse?.();
      setShowSearch(true);
      setTimeout(() => searchInputRef.current?.focus(), 120);
      return;
    }
    setShowSearch((prev) => {
      const next = !prev;
      if (next) {
        setTimeout(() => searchInputRef.current?.focus(), 40);
      } else {
        setSearchQuery('');
      }
      return next;
    });
  };

  const selectSession = (sessionId) => {
    onSelectSession?.(sessionId);
    onNavigate?.('chat');
  };

  return (
    <div className="flex h-full flex-col bg-[#171717] text-[#ECECEC] select-none">
      {/* Top Branding + Collapse + New Chat */}
      <div
        className={cn(
          'flex items-center px-3 pt-3 pb-2',
          collapsed ? 'flex-col gap-2' : 'justify-between'
        )}
      >
        <button
          type="button"
          onClick={() => onNavigate?.('chat')}
          className="flex min-w-0 items-center gap-2.5 rounded-lg px-1.5 py-1 text-left transition-colors hover:bg-[#2F2F2F]"
          aria-label="DocNest home"
        >
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center overflow-hidden rounded-lg border border-[#3A3A3A] bg-black">
            <img src="/docnest-logo.jpg" alt="DocNest" className="h-full w-full object-cover" />
          </div>
          {!collapsed && (
            <span className="truncate text-sm font-semibold tracking-tight text-[#ECECEC]">
              DocNest
            </span>
          )}
        </button>

        <div className={cn('flex items-center gap-1', collapsed && 'flex-col')}>
          {!mobile && (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="rounded-lg p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? (
                <PanelLeftOpen className="h-4 w-4" />
              ) : (
                <PanelLeftClose className="h-4 w-4" />
              )}
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              onNewChat?.();
              onNavigate?.('chat');
            }}
            className="rounded-lg p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
            aria-label="New chat"
            title="New chat"
          >
            <SquarePen className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ChatGPT-style Primary Actions */}
      <div className={cn('space-y-0.5 px-2 pb-2', collapsed && 'px-2')}>
        <button
          type="button"
          onClick={() => {
            onNewChat?.();
            onNavigate?.('chat');
          }}
          className={cn(
            'flex w-full items-center rounded-lg py-2 text-[13px] font-medium text-[#ECECEC] transition-colors hover:bg-[#2F2F2F]',
            collapsed ? 'justify-center px-2' : 'gap-2.5 px-2.5'
          )}
          title="New chat"
        >
          <SquarePen className="h-4 w-4 flex-shrink-0 text-[#A1A1A1]" />
          {!collapsed && <span>New chat</span>}
        </button>

        <button
          type="button"
          onClick={handleToggleSearch}
          className={cn(
            'flex w-full items-center rounded-lg py-2 text-[13px] font-medium transition-colors',
            showSearch
              ? 'bg-[#2A2A2A] text-[#ECECEC]'
              : 'text-[#ECECEC]/85 hover:bg-[#2F2F2F] hover:text-[#ECECEC]',
            collapsed ? 'justify-center px-2' : 'gap-2.5 px-2.5'
          )}
          title="Search chats"
        >
          <Search className="h-4 w-4 flex-shrink-0 text-[#A1A1A1]" />
          {!collapsed && <span>Search chats</span>}
        </button>

        {!collapsed && showSearch && (
          <div className="px-1 py-1 animate-fade-in">
            <div className="relative flex items-center rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] px-2.5 py-1.5">
              <Search className="mr-2 h-3.5 w-3.5 flex-shrink-0 text-[#777777]" />
              <input
                ref={searchInputRef}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search chats..."
                className="w-full bg-transparent text-xs text-[#ECECEC] placeholder-[#777777] focus:outline-none"
                aria-label="Search chats"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="ml-1 text-[#777777] hover:text-[#ECECEC]"
                  aria-label="Clear search"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
        )}

        <nav className="space-y-0.5 pt-1" aria-label="Workspace sections">
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
                  'flex w-full items-center rounded-lg py-2 text-[13px] transition-colors',
                  collapsed ? 'justify-center px-2' : 'gap-2.5 px-2.5',
                  isActive
                    ? 'bg-[#2F2F2F] font-medium text-[#ECECEC]'
                    : 'text-[#ECECEC]/85 hover:bg-[#2A2A2A] hover:text-[#ECECEC]'
                )}
              >
                <Icon
                  className={cn(
                    'h-4 w-4 flex-shrink-0',
                    isActive ? 'text-[#ECECEC]' : 'text-[#A1A1A1]'
                  )}
                />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Scrollable Recent Conversations */}
      {!collapsed ? (
        <div className="flex-1 overflow-y-auto px-2 py-2 border-t border-[#2E2E2E]">
          <ConversationList
            sessions={sessions}
            activeSessionId={activeSessionId}
            activeTab={activeTab}
            searchQuery={searchQuery}
            collapsed={collapsed}
            onSelectSession={selectSession}
            onRenameSession={onRenameSession}
            onPinSession={onPinSession}
            onDeleteSession={onDeleteSession}
          />
        </div>
      ) : (
        <div className="flex-1" />
      )}

      {/* Fixed Bottom User, Model & Settings Section */}
      <div className={cn('space-y-1.5 border-t border-[#2E2E2E] p-2.5', collapsed && 'px-2')}>
        {onOpenUpload && (
          <button
            type="button"
            onClick={onOpenUpload}
            className={cn(
              'flex w-full items-center rounded-lg border border-[#3A3A3A] bg-[#212121] py-1.5 text-xs font-medium text-[#ECECEC] transition-colors hover:bg-[#2F2F2F]',
              collapsed ? 'justify-center px-2' : 'justify-center gap-2 px-2.5'
            )}
            title="Upload document"
          >
            <UploadCloud className="h-3.5 w-3.5 flex-shrink-0 text-[#A1A1A1]" />
            {!collapsed && <span>Upload document</span>}
          </button>
        )}

        <div
          className={cn(
            'flex items-center rounded-lg px-2.5 py-1.5 text-xs text-[#A1A1A1]',
            collapsed ? 'justify-center px-1' : 'justify-between'
          )}
          title={`Model: ${configuredModel} (${isOllamaConnected ? 'online' : 'offline'})`}
        >
          <div className="flex min-w-0 items-center gap-2">
            <span
              className={cn(
                'h-2 w-2 flex-shrink-0 rounded-full',
                isOllamaConnected ? 'bg-emerald-500' : 'bg-[#777777]'
              )}
            />
            {!collapsed && (
              <span className="truncate font-mono text-[11px] text-[#A1A1A1]">
                {configuredModel}
              </span>
            )}
          </div>
          {!collapsed && (
            <span className="text-[10px] text-[#777777]">
              {isOllamaConnected ? 'Online' : 'Offline'}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => onNavigate?.('settings')}
          className={cn(
            'flex w-full items-center rounded-lg py-1.5 text-[13px] transition-colors',
            collapsed ? 'justify-center px-2' : 'gap-2.5 px-2.5',
            activeTab === 'settings'
              ? 'bg-[#2F2F2F] text-[#ECECEC]'
              : 'text-[#A1A1A1] hover:bg-[#2F2F2F] hover:text-[#ECECEC]'
          )}
          title="Settings"
        >
          <SettingsIcon className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>

        <button
          type="button"
          onClick={onOpenProfile}
          className={cn(
            'flex w-full items-center rounded-lg py-1.5 text-left transition-colors hover:bg-[#2F2F2F]',
            collapsed ? 'justify-center px-1' : 'gap-2.5 px-2'
          )}
          title="User profile"
        >
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[#303030] border border-[#3A3A3A] text-xs font-medium text-[#ECECEC]">
            {(currentUser?.username || currentUser?.full_name || 'R').charAt(0).toUpperCase()}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <span className="block truncate text-[13px] font-medium text-[#ECECEC]">
                {currentUser?.full_name || currentUser?.username || 'Local Researcher'}
              </span>
              <span className="block truncate text-[11px] text-[#777777]">
                {currentUser?.workspace_name || 'Personal Workspace'}
              </span>
            </div>
          )}
        </button>
      </div>
    </div>
  );
}
