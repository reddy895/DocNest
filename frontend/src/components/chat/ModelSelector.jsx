import React, { useState, useEffect, useRef } from 'react';
import { Cpu, ChevronDown, Check } from 'lucide-react';
import { fetchAvailableModels } from '../../services/api';
import { cn } from '../../lib/cn';

const DEFAULT_MODELS = [
  { id: 'llama3.2', name: 'Llama 3.2 (3B)', badge: 'Default' },
  { id: 'llama3.1:8b', name: 'Llama 3.1 (8B)', badge: '8B' },
  { id: 'mistral:7b', name: 'Mistral (7B)', badge: 'Fast' },
  { id: 'qwen2.5:7b', name: 'Qwen 2.5 (7B)', badge: 'Code' },
  { id: 'deepseek-r1:8b', name: 'DeepSeek R1 (8B)', badge: 'Reasoning' },
];

export default function ModelSelector({ selectedModel = 'llama3.2', onSelectModel }) {
  const [open, setOpen] = useState(false);
  const [models, setModels] = useState(DEFAULT_MODELS);
  const containerRef = useRef(null);

  useEffect(() => {
    fetchAvailableModels()
      .then((res) => {
        const list = res?.models || res?.available_models || [];
        if (Array.isArray(list) && list.length > 0) {
          const mapped = list
            .filter((m) => {
              const name = typeof m === 'string' ? m : m.name || m.id || '';
              return name && !name.includes('embed');
            })
            .map((m) => {
              const id = typeof m === 'string' ? m : m.name || m.id;
              return { id, name: id, badge: 'Local' };
            });
          if (mapped.length > 0) {
            setModels(mapped);
          }
        }
      })
      .catch(() => {
        // Keep default list if endpoint unavailable
      });
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  return (
    <div ref={containerRef} className="relative flex-shrink-0">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-medium text-[#A1A1A1] transition-colors hover:bg-[#3A3A3A] hover:text-[#ECECEC]"
        title="Select model"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Cpu className="h-3.5 w-3.5" />
        <span className="hidden max-w-[110px] truncate sm:inline">{selectedModel}</span>
        <ChevronDown className="h-3 w-3 opacity-70" />
      </button>

      {open && (
        <div
          className="absolute bottom-11 left-0 z-30 w-56 rounded-xl border border-[#3A3A3A] bg-[#2A2A2A] p-1.5 shadow-carbon-lg animate-fade-in"
          role="listbox"
        >
          <div className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-[#777777]">
            Models
          </div>
          {models.map((m) => {
            const active = selectedModel === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  onSelectModel?.(m.id);
                  setOpen(false);
                }}
                className={cn(
                  'flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors',
                  active
                    ? 'bg-[#3A3A3A] text-[#ECECEC] font-medium'
                    : 'text-[#ECECEC]/85 hover:bg-[#333333]'
                )}
              >
                <span className="truncate">{m.name}</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-[#777777]">{m.badge}</span>
                  {active && <Check className="h-3.5 w-3.5 text-[#ECECEC]" />}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

