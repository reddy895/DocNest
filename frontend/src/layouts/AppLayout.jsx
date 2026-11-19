import React, { useState } from 'react';
import {
  MessageSquare,
  Files,
  BookOpen,
  Cpu,
  Zap,
  BarChart3,
  Settings as SettingsIcon,
  Plus,
  Pin,
  Trash2,
  Edit2,
  Search,
  ChevronLeft,
  ChevronRight,
  Layers,
  Shield,
  User,
  UploadCloud,
  Menu,
  X,
  Check,
} from 'lucide-react';
import AuthModal from '../components/AuthModal';

export default function AppLayout({
  activeTab,
  setActiveTab,
  systemStatus,
  children,
  onOpenUpload,
  sessions = [],
  activeSessionId = null,
  onSelectSession = () => {},
  onNewSession = () => {},
  onRenameSession = () => {},
  onPinSession = () => {},
  onDeleteSession = () => {},
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const navigation = [
    { id: 'chat', name: 'Research Workspace', icon: MessageSquare },
    { id: 'library', name: 'Document Library', icon: Files },
    { id: 'research', name: 'Research Studio', icon: BookOpen },
    { id: 'rag-lab', name: 'RAG Developer Lab', icon: Cpu },
    { id: 'models', name: 'Model Arena', icon: Zap },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'settings', name: 'Settings', icon: SettingsIcon },
  ];

  const isOllamaConnected = systemStatus?.components?.ollama?.status === 'connected';
  const configuredModel = systemStatus?.components?.ollama?.configured_model || 'llama3.2';

  const filteredSessions = sessions.filter((s) =>
    (s.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  );
  const pinnedSessions = filteredSessions.filter((s) => s.is_pinned);
  const recentSessions = filteredSessions.filter((s) => !s.is_pinned);

  const startRename = (session, e) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitle(session.title);
  };

  const saveRename = (sessionId, e) => {
    e?.stopPropagation();
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim());
    }
    setEditingSessionId(null);
  };

  return (
    <div className="min-h-screen bg-carbon-primary flex flex-col md:flex-row text-silver-primary font-sans antialiased selection:bg-signal-yellow selection:text-carbon-deep">
      {/* Sidebar Desktop */}
      <aside
        className={`hidden md:flex flex-col bg-[#111315] border-r border-[#343A3F] transition-all duration-200 z-30 select-none ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="p-3.5 border-b border-[#343A3F] flex items-center justify-between">
          <div
            onClick={() => setActiveTab('chat')}
            className="flex items-center gap-2.5 cursor-pointer overflow-hidden"
          >
            <div className="w-8 h-8 rounded-lg bg-[#E5B83D] text-[#111315] flex items-center justify-center font-bold text-lg shadow-sm flex-shrink-0">
              <Layers className="w-4 h-4 text-[#111315]" />
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <span className="font-bold text-base tracking-tight text-[#F0F1F2] block leading-tight">
                  DocNest
                </span>
                <span className="text-[10px] text-[#A0A6AC] tracking-wider uppercase block font-mono">
                  Research AI
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 text-[#A0A6AC] hover:text-[#F0F1F2] hover:bg-[#191C1F] rounded-md transition"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* New Research Button */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewSession();
              setActiveTab('chat');
            }}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 bg-[#E5B83D] hover:bg-[#F2C64B] text-[#111315] text-xs font-semibold rounded-lg shadow-sm transition ${
              isCollapsed ? 'px-2' : ''
            }`}
            title="Start New Research"
          >
            <Plus className="w-4 h-4 flex-shrink-0 stroke-[2.5]" />
            {!isCollapsed && <span>New Research</span>}
          </button>
        </div>

        {/* Conversation History & Navigation */}
        <div className="flex-1 overflow-y-auto px-2 space-y-4 text-xs">
          {/* Main Navigation Items */}
          <div className="space-y-0.5">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  title={item.name}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-[#191C1F] text-[#E5B83D] border-l-2 border-[#E5B83D] font-semibold'
                      : 'text-[#A0A6AC] hover:bg-[#191C1F] hover:text-[#F0F1F2]'
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-[#E5B83D]' : 'text-[#A0A6AC]'}`} />
                  {!isCollapsed && <span className="truncate">{item.name}</span>}
                </button>
              );
            })}
          </div>

          {/* Persistent Conversation History (Visible when not collapsed) */}
          {!isCollapsed && (
            <div className="pt-2 border-t border-[#343A3F]/60 space-y-3">
              {/* Search History Input */}
              <div className="relative px-1">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2 text-[#A0A6AC]" />
                <input
                  type="text"
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#191C1F] border border-[#343A3F] rounded-md pl-7 pr-2 py-1.5 text-[11px] text-[#F0F1F2] placeholder-[#A0A6AC]/60 focus:outline-none focus:border-[#E5B83D]"
                />
              </div>

              {/* Pinned Conversations */}
              {pinnedSessions.length > 0 && (
                <div className="space-y-1">
                  <div className="px-2 text-[10px] uppercase font-mono tracking-wider text-[#A0A6AC]/70 flex items-center gap-1">
                    <Pin className="w-3 h-3 text-[#E5B83D]" />
                    <span>Pinned</span>
                  </div>
                  {pinnedSessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => {
                        onSelectSession(session.id);
                        setActiveTab('chat');
                      }}
                      className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md cursor-pointer transition ${
                        activeSessionId === session.id && activeTab === 'chat'
                          ? 'bg-[#22262A] text-[#E5B83D] font-medium'
                          : 'text-[#F0F1F2]/80 hover:bg-[#191C1F] hover:text-[#F0F1F2]'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate pr-1">
                        <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-[#E5B83D]" />
                        <span className="truncate text-xs">{session.title}</span>
                      </div>
                      <div className="hidden group-hover:flex items-center gap-1 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onPinSession(session.id, false);
                          }}
                          title="Unpin"
                          className="p-1 text-[#A0A6AC] hover:text-[#E5B83D]"
                        >
                          <Pin className="w-3 h-3 fill-[#E5B83D]" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(session.id);
                          }}
                          title="Delete"
                          className="p-1 text-[#A0A6AC] hover:text-rose-400"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Recent Conversations */}
              <div className="space-y-1">
                <div className="px-2 text-[10px] uppercase font-mono tracking-wider text-[#A0A6AC]/70">
                  Recent
                </div>
                {recentSessions.length === 0 ? (
                  <div className="px-2 py-1.5 text-[11px] text-[#A0A6AC]/60 italic">
                    No recent chats
                  </div>
                ) : (
                  recentSessions.slice(0, 15).map((session) => (
                    <div
                      key={session.id}
                      onClick={() => {
                        onSelectSession(session.id);
                        setActiveTab('chat');
                      }}
                      className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md cursor-pointer transition ${
                        activeSessionId === session.id && activeTab === 'chat'
                          ? 'bg-[#22262A] text-[#E5B83D] font-medium'
                          : 'text-[#F0F1F2]/80 hover:bg-[#191C1F] hover:text-[#F0F1F2]'
                      }`}
                    >
                      {editingSessionId === session.id ? (
                        <div
                          className="flex items-center gap-1 w-full"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') saveRename(session.id, e);
                              if (e.key === 'Escape') setEditingSessionId(null);
                            }}
                            autoFocus
                            className="w-full bg-[#111315] border border-[#E5B83D] rounded px-1.5 py-0.5 text-xs text-[#F0F1F2] focus:outline-none"
                          />
                          <button
                            onClick={(e) => saveRename(session.id, e)}
                            className="p-1 text-emerald-400 hover:text-emerald-300"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-2 truncate pr-1">
                            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-[#A0A6AC]" />
                            <span className="truncate text-xs">{session.title}</span>
                          </div>
                          <div className="hidden group-hover:flex items-center gap-1 flex-shrink-0">
                            <button
                              onClick={(e) => startRename(session, e)}
                              title="Rename"
                              className="p-1 text-[#A0A6AC] hover:text-[#F0F1F2]"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onPinSession(session.id, true);
                              }}
                              title="Pin"
                              className="p-1 text-[#A0A6AC] hover:text-[#E5B83D]"
                            >
                              <Pin className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteSession(session.id);
                              }}
                              title="Delete"
                              className="p-1 text-[#A0A6AC] hover:text-rose-400"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-[#343A3F] bg-[#111315] space-y-2">
          {/* Quick Upload action */}
          {onOpenUpload && !isCollapsed && (
            <button
              onClick={onOpenUpload}
              className="w-full flex items-center justify-center gap-2 py-1.5 px-2 bg-[#191C1F] hover:bg-[#22262A] border border-[#343A3F] text-[#F0F1F2] rounded-md text-[11px] font-medium transition"
            >
              <UploadCloud className="w-3.5 h-3.5 text-[#E5B83D]" />
              <span>Upload Document</span>
            </button>
          )}

          {/* Model Status Pill */}
          <div
            onClick={() => setActiveTab('models')}
            className="flex items-center justify-between p-2 bg-[#191C1F] border border-[#343A3F] rounded-md cursor-pointer hover:border-[#E5B83D]/60 transition"
            title="Configure Active Ollama Model"
          >
            <div className="flex items-center gap-2 truncate">
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  isOllamaConnected ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
                }`}
              />
              {!isCollapsed && (
                <span className="text-xs font-mono text-[#F0F1F2] truncate">
                  {configuredModel}
                </span>
              )}
            </div>
            {!isCollapsed && (
              <span className="text-[10px] text-[#A0A6AC] font-mono">131K ctx</span>
            )}
          </div>

          {/* User Workspace Button */}
          <button
            onClick={() => setAuthModalOpen(true)}
            className="w-full flex items-center justify-between p-1.5 hover:bg-[#191C1F] rounded-md transition text-[#A0A6AC] hover:text-[#F0F1F2]"
            title="Workspace & User Account"
          >
            <div className="flex items-center gap-2 truncate">
              <Shield className="w-3.5 h-3.5 text-[#E5B83D]" />
              {!isCollapsed && (
                <span className="text-xs truncate font-medium text-[#F0F1F2]">
                  {currentUser?.workspace_name || 'Default Workspace'}
                </span>
              )}
            </div>
            {!isCollapsed && <User className="w-3.5 h-3.5" />}
          </button>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between p-3.5 bg-[#111315] border-b border-[#343A3F]">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-[#E5B83D]" />
          <span className="font-bold text-base text-[#F0F1F2]">DocNest</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              onNewSession();
              setActiveTab('chat');
            }}
            className="p-1.5 bg-[#E5B83D] text-[#111315] rounded-md text-xs font-bold"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 text-[#A0A6AC] hover:text-[#F0F1F2] rounded-md hover:bg-[#191C1F]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden p-3 bg-[#191C1F] border-b border-[#343A3F] space-y-1 animate-fade-in">
          {navigation.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium ${
                activeTab === item.id ? 'bg-[#22262A] text-[#E5B83D] font-bold' : 'text-[#F0F1F2]'
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
              className="w-full flex items-center justify-center gap-2 py-2 mt-2 bg-[#E5B83D] text-[#111315] font-semibold rounded-md text-xs"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload Document</span>
            </button>
          )}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden min-h-screen bg-[#111315] flex flex-col">
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
