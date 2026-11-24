import React, { useState } from 'react';
import { Layers, Menu, Plus, X } from 'lucide-react';
import Sidebar from '../sidebar/Sidebar';
import { cn } from '../../lib/cn';

export default function AppShell({
  activeTab,
  setActiveTab,
  systemStatus,
  onOpenUpload,
  onNewSession,
  children,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground md:flex-row">
      <aside className="hidden w-64 flex-shrink-0 border-r border-border md:block">
        <Sidebar
          activeTab={activeTab}
          onNavigate={handleNavigate}
          onNewChat={handleNewChat}
          onOpenUpload={onOpenUpload}
          systemStatus={systemStatus}
        />
      </aside>

      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-border bg-surface-raised px-3.5 py-3 md:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-brand-foreground">
            <Layers className="h-4 w-4" />
          </div>
          <span className="text-base font-bold text-foreground">DocNest</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-lg bg-brand p-2 text-brand-foreground transition-colors hover:bg-brand-hover"
            aria-label="New chat"
            title="New chat"
          >
            <Plus className="h-4 w-4" strokeWidth={2.5} />
          </button>
          <button
            type="button"
            onClick={() => setMobileMenuOpen((open) => !open)}
            className="rounded-lg border border-border p-2 text-muted transition-colors hover:bg-surface hover:text-foreground"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </header>

      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        >
          <div
            className={cn('h-full w-72 max-w-[85vw] animate-slide-up border-r border-border shadow-2xl')}
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
            />
          </div>
        </div>
      )}

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background">{children}</main>
    </div>
  );
}
