import React, { useState } from 'react';
import {
  LayoutDashboard,
  Files,
  UploadCloud,
  MessageSquare,
  Settings as SettingsIcon,
  Menu,
  X,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';

export default function AppLayout({
  activeTab,
  setActiveTab,
  systemStatus,
  children,
  onOpenUpload,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat', name: 'AI Chat Workspace', icon: MessageSquare },
    { id: 'library', name: 'Document Library', icon: Files },
    { id: 'upload', name: 'Upload PDF', icon: UploadCloud },
    { id: 'settings', name: 'System Settings', icon: SettingsIcon },
  ];

  const handleNavClick = (tabId) => {
    if (tabId === 'upload' && onOpenUpload) {
      onOpenUpload();
    } else {
      setActiveTab(tabId);
    }
    setMobileMenuOpen(false);
  };

  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';

  return (
    <div className="min-h-screen bg-[#202326] flex flex-col md:flex-row">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex md:w-64 flex-col bg-[#171A1C] border-r border-[#555C61]">
        {/* Brand Header */}
        <div className="p-5 border-b border-[#555C61]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#F4D21F] text-[#171A1C] flex items-center justify-center font-bold text-xl shadow-signal-glow">
              <Layers className="w-5 h-5 text-[#171A1C]" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-[#E0E3E5] block">
                DocNest
              </span>
              <span className="text-[10px] text-[#969DA3] tracking-wider uppercase block font-mono">
                RAG Intelligence
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#292D30] text-[#F4D21F] border-l-4 border-[#F4D21F] shadow-carbon-sm font-semibold'
                    : 'text-[#BFC3C7] hover:bg-[#202326] hover:text-[#E0E3E5]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#F4D21F]' : 'text-[#969DA3]'}`} />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>

        {/* Quick System Status Card in Sidebar */}
        <div className="p-4 border-t border-[#555C61] bg-[#171A1C]">
          <div className="bg-[#202326] border border-[#555C61] rounded p-3 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[#969DA3] uppercase tracking-wider font-mono text-[10px]">
                Ollama Runtime
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  isOllamaConnected ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
            </div>
            <div className="font-medium text-[#E0E3E5] truncate">
              {systemStatus?.components?.ollama?.configured_model || 'llama3.2'}
            </div>
            <div className="text-[11px] text-[#969DA3] mt-0.5">
              {isOllamaConnected ? 'Active & Ready' : 'Connecting...'}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-[#202326] border-b border-[#555C61] px-4 md:px-8 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden text-[#BFC3C7] hover:text-[#E0E3E5] p-1.5 rounded focus:outline-none"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <div>
              <h1 className="text-sm font-semibold text-[#E0E3E5] uppercase tracking-wider font-mono">
                {navigation.find((n) => n.id === activeTab)?.name || 'DocNest'}
              </h1>
              <p className="text-xs text-[#969DA3] hidden sm:block">
                Your documents. Your questions. Clear answers.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs bg-[#292D30] border border-[#555C61] px-3 py-1.5 rounded font-mono">
              <Activity className="w-3.5 h-3.5 text-[#F4D21F]" />
              <span className="text-[#969DA3]">Vectors:</span>
              <span className="text-[#E0E3E5] font-semibold">
                {systemStatus?.total_chunks || 0}
              </span>
            </div>

            <button
              onClick={() => onOpenUpload && onOpenUpload()}
              className="btn-primary text-xs py-1.5 px-3"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload PDF</span>
            </button>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#171A1C] border-b border-[#555C61] p-3 space-y-1 z-30">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded text-sm ${
                    isActive
                      ? 'bg-[#292D30] text-[#F4D21F] font-semibold'
                      : 'text-[#BFC3C7] hover:bg-[#202326]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Dynamic Page Outlet */}
        <main className="flex-1 p-4 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
