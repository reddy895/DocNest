import React, { useState } from 'react';
import { Folder, ChevronDown, Plus, Check, Sparkles } from 'lucide-react';

export default function WorkspaceSelector({
  workspaces = [],
  activeWorkspace = null,
  onSelectWorkspace = () => {},
  onCreateWorkspace = () => {},
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const currentWs = activeWorkspace || {
    id: 'default',
    name: 'Default Research Workspace',
    color: '#F5C542',
    document_count: 0,
  };

  const handleCreate = (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    onCreateWorkspace(newTitle.trim());
    setNewTitle('');
    setIsCreating(false);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-[#1A1D20] hover:bg-[#22262B] border border-[#30353A] hover:border-[#F5C542]/60 rounded-xl text-xs text-[#F2F3F4] transition shadow-sm"
      >
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: currentWs.color || '#F5C542' }}
        />
        <Folder className="w-3.5 h-3.5 text-[#A2A9B0]" />
        <span className="font-medium truncate max-w-[150px]">{currentWs.name}</span>
        <ChevronDown className="w-3 h-3 text-[#A2A9B0]" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 bg-[#1A1D20] border border-[#30353A] rounded-xl shadow-xl p-2 z-50 text-xs space-y-1 animate-fade-in">
          <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-[#A2A9B0]/70 flex items-center justify-between">
            <span>Research Workspaces</span>
            <span className="text-[#F5C542]">{workspaces.length}</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-0.5">
            {workspaces.map((ws) => {
              const isSelected = ws.id === currentWs.id;
              return (
                <button
                  key={ws.id}
                  onClick={() => {
                    onSelectWorkspace(ws);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left transition ${
                    isSelected
                      ? 'bg-[#17191B] text-[#F5C542] font-semibold border border-[#F5C542]/40'
                      : 'text-[#F2F3F4] hover:bg-[#22262B]'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: ws.color || '#F5C542' }}
                    />
                    <span className="truncate">{ws.name}</span>
                  </div>
                  {isSelected && <Check className="w-3 h-3 text-[#F5C542] shrink-0" />}
                </button>
              );
            })}
          </div>

          {isCreating ? (
            <form onSubmit={handleCreate} className="pt-2 border-t border-[#30353A] space-y-2">
              <input
                type="text"
                placeholder="Workspace name..."
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                autoFocus
                className="w-full bg-[#101214] border border-[#30353A] focus:border-[#F5C542] rounded-lg px-2 py-1 text-xs text-[#F2F3F4] focus:outline-none"
              />
              <div className="flex justify-end gap-1.5">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="px-2 py-1 text-[10px] text-[#A2A9B0] hover:text-[#F2F3F4]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-2.5 py-1 bg-[#F5C542] hover:bg-[#FFD358] text-[#101214] font-bold text-[10px] rounded-md transition"
                >
                  Create
                </button>
              </div>
            </form>
          ) : (
            <div className="pt-1 border-t border-[#30353A]">
              <button
                onClick={() => setIsCreating(true)}
                className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[11px] text-[#A2A9B0] hover:text-[#F5C542] rounded-lg hover:bg-[#22262B] transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create New Workspace</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
