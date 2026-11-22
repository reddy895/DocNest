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
import WorkspaceSelector from '../components/WorkspaceSelector';

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
  workspaces = [],
  activeWorkspace = null,
  onSelectWorkspace = () => {},
  onCreateWorkspace = () => {},
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
    <div className="min-h-screen bg-[#0C0D0E] flex flex-col md:flex-row text-[#F0F2F5] font-sans antialiased selection:bg-[#F5C542] selection:text-[#0C0D0E]">
      {/* Sidebar Desktop */}
      <aside
        className={`hidden md:flex flex-col bg-[#121417] border-r border-[#20242A] transition-all duration-200 z-30 select-none ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="p-3.5 border-b border-[#20242A] flex items-center justify-between">
          <div
            onClick={() => setActiveTab('chat')}
            className="flex items-center gap-2.5 cursor-pointer overflow-hidden"
          >
            <div className="w-8 h-8 rounded-lg bg-[#F5C542] text-[#0C0D0E] flex items-center justify-center font-bold text-lg shadow-sm flex-shrink-0">
              <Layers className="w-4 h-4 text-[#0C0D0E]" />
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <span className="font-bold text-base tracking-tight text-[#F0F2F5] block leading-tight">
                  DocNest
                </span>
                <span className="text-[10px] text-[#8E95A0] tracking-wider uppercase block font-mono">
                  Research Workspace
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 text-[#8E95A0] hover:text-[#F0F2F5] hover:bg-[#181B1F] rounded-md transition"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* New Research Button */}
        <div className="p-3 space-y-2">
          <button
            onClick={() => {
              onNewSession();
              setActiveTab('chat');
            }}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 bg-[#F5C542] hover:bg-[#FFD358] text-[#0C0D0E] text-xs font-bold rounded-xl shadow-sm transition ${
              isCollapsed ? 'px-2' : ''
            }`}
            title="Start New Research"
          >
            <Plus className="w-4 h-4 flex-shrink-0 stroke-[2.5]" />
            {!isCollapsed && <span>New Research</span>}
          </button>

          {!isCollapsed && (
            <WorkspaceSelector
              workspaces={workspaces}
              activeWorkspace={activeWorkspace}
              onSelectWorkspace={onSelectWorkspace}
              onCreateWorkspace={onCreateWorkspace}
            />
          )}
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
                      ? 'bg-[#181B1F] text-[#F5C542] border-l-2 border-[#F5C542] font-semibold'
                      : 'text-[#8E95A0] hover:bg-[#181B1F] hover:text-[#F0F2F5]'
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-[#F5C542]' : 'text-[#8E95A0]'}`} />
                  {!isCollapsed && <span className="truncate">{item.name}</span>}
                </button>
              );
            })}
          </div>

          {/* Persistent Conversation History (Visible when not collapsed) */}
          {!isCollapsed && (
            <div className="pt-2 border-t border-[#20242A] space-y-3">
              {/* Search History Input */}
              <div className="relative px-1">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2 text-[#A0A6AC]" />
                <input
                  type="text"
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#1A1D20] border border-[#30353A] rounded-md pl-7 pr-2 py-1.5 text-[11px] text-[#F2F3F4] placeholder-[#A2A9B0]/60 focus:outline-none focus:border-[#F5C542]"
                />
              </div>

              {/* Pinned Conversations */}
              {pinnedSessions.length > 0 && (
                <div className="space-y-1">
                  <div className="px-2 text-[10px] uppercase font-mono tracking-wider text-[#A2A9B0]/70 flex items-center gap-1">
                    <Pin className="w-3 h-3 text-[#F5C542]" />
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
                          ? 'bg-[#1A1D20] text-[#F5C542] font-medium'
                          : 'text-[#F2F3F4]/80 hover:bg-[#1A1D20] hover:text-[#F2F3F4]'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate pr-1">
                        <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-[#F5C542]" />
                        <span className="truncate text-xs">{session.title}</span>
                      </div>
                      <div className="hidden group-hover:flex items-center gap-1 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onPinSession(session.id, false);
                          }}
                          title="Unpin"
                          className="p-1 text-[#A2A9B0] hover:text-[#F5C542]"
                        >
                          <Pin className="w-3 h-3 fill-[#F5C542]" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(session.id);
                          }}
                          title="Delete"
                          className="p-1 text-[#A2A9B0] hover:text-rose-400"
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
                <div className="px-2 text-[10px] uppercase font-mono tracking-wider text-[#A2A9B0]/70">
                  Recent
                </div>
                {recentSessions.length === 0 ? (
                  <div className="px-2 py-1.5 text-[11px] text-[#A2A9B0]/60 italic">
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
                          ? 'bg-[#1A1D20] text-[#F5C542] font-medium'
                          : 'text-[#F2F3F4]/80 hover:bg-[#1A1D20] hover:text-[#F2F3F4]'
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
                            className="w-full bg-[#101214] border border-[#F5C542] rounded px-1.5 py-0.5 text-xs text-[#F2F3F4] focus:outline-none"
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
                            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-[#A2A9B0]" />
                            <span className="truncate text-xs">{session.title}</span>
                          </div>
                          <div className="hidden group-hover:flex items-center gap-1 flex-shrink-0">
                            <button
                              onClick={(e) => startRename(session, e)}
                              title="Rename"
                              className="p-1 text-[#A2A9B0] hover:text-[#F2F3F4]"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onPinSession(session.id, true);
                              }}
                              title="Pin"
                              className="p-1 text-[#A2A9B0] hover:text-[#F5C542]"
                            >
                              <Pin className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteSession(session.id);
                              }}
                              title="Delete"
                              className="p-1 text-[#A2A9B0] hover:text-rose-400"
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
        <div className="p-3 border-t border-[#20242A] bg-[#121417] space-y-2">
          {/* Quick Upload action */}
          {onOpenUpload && !isCollapsed && (
            <button
              onClick={onOpenUpload}
              className="w-full flex items-center justify-center gap-2 py-1.5 px-2 bg-[#181B1F] hover:bg-[#20242A] border border-[#20242A] text-[#F0F2F5] rounded-lg text-[11px] font-medium transition"
            >
              <UploadCloud className="w-3.5 h-3.5 text-[#F5C542]" />
              <span>Upload Document</span>
            </button>
          )}

          {/* Model Status Pill */}
          <div
            onClick={() => setActiveTab('models')}
            className="flex items-center justify-between p-2 bg-[#181B1F] border border-[#20242A] rounded-lg cursor-pointer hover:border-[#F5C542]/50 transition"
            title="Configure Active Ollama Model"
          >
            <div className="flex items-center gap-2 truncate">
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  isOllamaConnected ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
                }`}
              />
              {!isCollapsed && (
                <span className="text-xs font-mono text-[#F0F2F5] truncate">
                  {configuredModel}
                </span>
              )}
            </div>
            {!isCollapsed && (
              <span className="text-[10px] text-[#8E95A0] font-mono">131K ctx</span>
            )}
          </div>

          {/* User Workspace Profile Badge */}
          <div className="pt-1 border-t border-[#20242A]">
            <button
              onClick={() => setAuthModalOpen(true)}
              className="w-full flex items-center justify-between p-2 bg-[#181B1F]/60 hover:bg-[#181B1F] border border-[#20242A] rounded-xl transition text-[#8E95A0] hover:text-[#F0F2F5] group"
              title="User Account & Preferences"
            >
              <div className="flex items-center gap-2.5 truncate">
                <div className="w-6 h-6 rounded-full bg-[#F5C542]/10 border border-[#F5C542]/40 text-[#F5C542] flex items-center justify-center text-[10px] font-bold">
                  {currentUser?.username ? currentUser.username[0].toUpperCase() : 'U'}
                </div>
                {!isCollapsed && (
                  <div className="truncate text-left">
                    <span className="text-xs font-semibold text-[#F0F2F5] block truncate leading-tight">
                      {currentUser?.full_name || currentUser?.username || 'Local Researcher'}
                    </span>
                    <span className="text-[10px] text-[#8E95A0] font-mono block truncate">
                      {currentUser?.workspace_name || 'Default Workspace'}
                    </span>
                  </div>
                )}
              </div>
              {!isCollapsed && (
                <SettingsIcon className="w-3.5 h-3.5 text-[#8E95A0] group-hover:text-[#F5C542] transition-colors" />
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between p-3.5 bg-[#121417] border-b border-[#20242A] sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#F5C542] text-[#0C0D0E] flex items-center justify-center font-bold text-sm shadow-sm">
            <Layers className="w-4 h-4 text-[#0C0D0E]" />
          </div>
          <span className="font-bold text-base text-[#F0F2F5]">DocNest</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              onNewSession();
              setActiveTab('chat');
            }}
            className="p-2 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] rounded-lg text-xs font-bold transition shadow-sm"
            title="New Research"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-[#A2A9B0] hover:text-[#F2F3F4] rounded-lg hover:bg-[#1A1D20] border border-[#30353A] transition"
            title="Toggle Menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Mobile Backdrop & Drawer */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="p-4 bg-[#17191B] border-b border-[#30353A] space-y-2 animate-fade-in shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-1">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition ${
                    activeTab === item.id
                      ? 'bg-[#1A1D20] text-[#F5C542] font-bold border-l-2 border-[#F5C542]'
                      : 'text-[#F2F3F4] hover:bg-[#1A1D20]'
                  }`}
                >
                  <item.icon className="w-4 h-4 shrink-0 text-[#F5C542]" />
                  <span>{item.name}</span>
                </button>
              ))}
            </div>

            {onOpenUpload && (
              <button
                onClick={() => {
                  onOpenUpload();
                  setMobileMenuOpen(false);
                }}
                className="w-full flex items-center justify-center gap-2 py-2.5 mt-2 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] font-bold rounded-xl text-xs transition shadow-sm"
              >
                <UploadCloud className="w-4 h-4 stroke-[2.5]" />
                <span>Upload Document</span>
              </button>
            )}
          </div>
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
