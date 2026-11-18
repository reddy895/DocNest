import React, { useState } from 'react';
import {
  LayoutDashboard,
  Files,
  MessageSquare,
  Settings as SettingsIcon,
  Layers,
  UploadCloud,
  User,
  Shield,
  Activity,
  Menu,
  X,
} from 'lucide-react';
import AuthModal from '../components/AuthModal';

export default function AppLayout({
  activeTab,
  setActiveTab,
  systemStatus,
  children,
  onOpenUpload,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat', name: 'AI Chat Workspace', icon: MessageSquare },
    { id: 'library', name: 'Document Library', icon: Files },
    { id: 'settings', name: 'RAG Evaluation & Settings', icon: SettingsIcon },
  ];

  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';

  return (
    <div className="min-h-screen bg-carbon-primary flex flex-col md:flex-row text-silver-primary">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex md:w-64 flex-col bg-carbon-deep border-r border-silver-border">
        {/* Brand Header */}
        <div className="p-5 border-b border-silver-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-signal-yellow text-carbon-deep flex items-center justify-center font-bold text-xl shadow-signal-glow">
                <Layers className="w-5 h-5 text-carbon-deep" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-silver-light block">
                  DocNest
                </span>
                <span className="text-[10px] text-silver-secondary tracking-wider uppercase block font-mono">
                  RAG Platform
                </span>
              </div>
            </div>
          </div>

          {/* Workspace Pill */}
          <button
            onClick={() => setAuthModalOpen(true)}
            className="mt-4 w-full flex items-center justify-between px-3 py-1.5 bg-carbon-secondary hover:bg-carbon-surface border border-silver-border rounded-lg text-xs transition"
          >
            <div className="flex items-center gap-2 truncate">
              <Shield className="w-3.5 h-3.5 text-signal-yellow" />
              <span className="truncate text-silver-light font-medium">
                {currentUser?.workspace_name || 'Default Workspace'}
              </span>
            </div>
            <User className="w-3.5 h-3.5 text-silver-secondary" />
          </button>
        </div>

        {/* Primary Action Button */}
        {onOpenUpload && (
          <div className="px-3 pt-4">
            <button
              onClick={onOpenUpload}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg shadow-carbon-sm transition"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Document</span>
            </button>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-carbon-secondary text-signal-yellow border-l-4 border-signal-yellow shadow-carbon-sm font-semibold'
                    : 'text-silver-primary hover:bg-carbon-primary hover:text-silver-light'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-signal-yellow' : 'text-silver-secondary'}`} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        {/* System Status in Sidebar Footer */}
        <div className="p-4 border-t border-silver-border bg-carbon-deep">
          <div className="bg-carbon-primary border border-silver-border rounded-lg p-3 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-silver-secondary uppercase tracking-wider font-mono text-[10px]">
                Ollama Engine
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  isOllamaConnected ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
                }`}
              />
            </div>
            <div className="font-medium text-silver-light truncate">
              {systemStatus?.components?.ollama?.configured_model || 'llama3.2'}
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px] text-silver-secondary font-mono">
              <span>Embedding</span>
              <span className="text-signal-yellow">nomic-embed</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between p-4 bg-carbon-deep border-b border-silver-border">
        <div className="flex items-center gap-2">
          <Layers className="w-6 h-6 text-signal-yellow" />
          <span className="font-bold text-lg text-silver-light">DocNest</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-silver-secondary hover:text-silver-light rounded-lg hover:bg-carbon-secondary"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden p-4 bg-carbon-surface border-b border-silver-border space-y-2 animate-fade-in">
          {navigation.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                activeTab === item.id ? 'bg-carbon-secondary text-signal-yellow font-bold' : 'text-silver-primary'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span>{item.name}</span>
            </button>
          ))}
          {onOpenUpload && (
            <button
              onClick={() => {
                onOpenUpload();
                setMobileMenuOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 py-2 mt-2 bg-signal-yellow text-carbon-deep font-bold rounded-lg text-sm"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload PDF</span>
            </button>
          )}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto min-h-screen bg-carbon-primary">
        {children}
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
      />
    </div>
  );
}
