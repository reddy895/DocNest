import React, { useState } from 'react';
import { Layers, Menu, Plus, X } from 'lucide-react';
import Sidebar from '../sidebar/Sidebar';
import AuthModal from '../ui/AuthModal';
import { cn } from '../../lib/cn';

export default function AppShell({
  activeTab,
  setActiveTab,
  systemStatus,
  onOpenUpload,
  onNewSession,
  sessions = [],
  activeSessionId = null,
  onSelectSession,
  onRenameSession,
  onPinSession,
  onDeleteSession,
  children,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  const handleNewChat = () => {
    onNewSession?.();
    setActiveTab('chat');
    setMobileMenuOpen(false);
  };

  const handleNavigate = (tab) => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#212121] text-[#ECECEC] md:flex-row">
      <aside
        className={cn(
          'hidden flex-shrink-0 border-r border-[#2E2E2E] bg-[#171717] transition-[width] duration-200 md:block',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        <Sidebar
          activeTab={activeTab}
          onNavigate={handleNavigate}
          onNewChat={handleNewChat}
          onOpenUpload={onOpenUpload}
          systemStatus={systemStatus}
          isCollapsed={isCollapsed}
          onToggleCollapse={() => setIsCollapsed((collapsed) => !collapsed)}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={onSelectSession}
          onRenameSession={onRenameSession}
          onPinSession={onPinSession}
          onDeleteSession={onDeleteSession}
          currentUser={currentUser}
          onOpenProfile={() => setAuthModalOpen(true)}
        />
      </aside>

      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-[#2E2E2E] bg-[#171717] px-3.5 py-2.5 md:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#3A3A3A] bg-[#2A2A2A] text-[#ECECEC]">
            <Layers className="h-4 w-4" />
          </div>
          <span className="text-sm font-semibold text-[#ECECEC]">DocNest</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-lg bg-[#F0F0F0] p-1.5 text-[#171717] transition-colors hover:bg-white"
            aria-label="New chat"
            title="New chat"
          >
            <Plus className="h-4 w-4" strokeWidth={2.2} />
          </button>
          <button
            type="button"
            onClick={() => setMobileMenuOpen((open) => !open)}
            className="rounded-lg border border-[#3A3A3A] p-1.5 text-[#A1A1A1] transition-colors hover:bg-[#2F2F2F] hover:text-[#ECECEC]"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </header>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        >
          <div
            className="h-full w-72 max-w-[85vw] animate-slide-up border-r border-[#2E2E2E] bg-[#171717]"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
          >
            <Sidebar
              mobile
              activeTab={activeTab}
              onNavigate={handleNavigate}
              onNewChat={handleNewChat}
              onOpenUpload={() => {
                onOpenUpload?.();
                setMobileMenuOpen(false);
              }}
              systemStatus={systemStatus}
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelectSession={(id) => {
                onSelectSession?.(id);
                setMobileMenuOpen(false);
              }}
              onRenameSession={onRenameSession}
              onPinSession={onPinSession}
              onDeleteSession={onDeleteSession}
              currentUser={currentUser}
              onOpenProfile={() => {
                setAuthModalOpen(true);
                setMobileMenuOpen(false);
              }}
            />
          </div>
        </div>
      )}

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background">{children}</main>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
      />
    </div>
  );
}
