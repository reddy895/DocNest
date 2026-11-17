import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  Loader2,
  Trash2,
  Copy,
  Check,
  FileText,
  Filter,
  Sparkles,
  AlertCircle,
  HelpCircle,
  Clock,
  BookOpen,
} from 'lucide-react';
import CitationCard from '../components/CitationCard';

export default function ChatWorkspace({
  documents = [],
  selectedDocId = null,
  onSelectDocId,
  onOpenViewer,
}) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am DocNest, your document intelligence assistant. Ask me questions about your uploaded PDFs, and I will provide answers grounded directly in document passages with exact page citations.',
      citations: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);

  // Fetch contextual suggestions whenever selected document changes
  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const url = selectedDocId
          ? `/api/chat/suggestions?doc_id=${selectedDocId}`
          : '/api/chat/suggestions';
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.suggestions || []);
        }
      } catch (err) {
        console.error('Failed to load suggestions:', err);
      }
    };
    fetchSuggestions();
  }, [selectedDocId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (questionText = null) => {
    const q = (questionText || inputQuestion).trim();
    if (!q || isLoading) return;

    const userMessageId = `user_${Date.now()}`;
    const userMsg = {
      id: userMessageId,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          doc_id: selectedDocId || null,
          top_k: 4,
          similarity_threshold: 0.25,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate answer');
      }

      const aiMsg = {
        id: `ai_${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        citations: data.citations || [],
        processingTime: data.processing_time_seconds,
        modelUsed: data.model_used,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `Error: ${err.message}. Please check that the local Ollama service is running.`,
          citations: [],
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: 'Conversation cleared. How can I assist you with your documents today?',
        citations: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] carbon-card overflow-hidden">
      {/* Workspace Top Toolbar */}
      <div className="p-3.5 bg-[#171A1C] border-b border-[#555C61] flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-[#F4D21F]" />
          <span className="text-xs text-[#969DA3] font-medium">Knowledge Scope:</span>
          <select
            value={selectedDocId || ''}
            onChange={(e) => onSelectDocId && onSelectDocId(e.target.value || null)}
            className="carbon-input py-1 px-2.5 text-xs text-[#E0E3E5] font-medium"
          >
            <option value="">All Uploaded Documents</option>
            {documents.map((doc) => (
              <option key={doc.doc_id} value={doc.doc_id}>
                {doc.filename} ({doc.page_count} pages)
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleClear}
          className="btn-secondary text-xs py-1 px-2.5 text-[#969DA3] hover:text-[#E0E3E5]"
          title="Clear conversation history"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Clear Chat</span>
        </button>
      </div>

      {/* Message Thread */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-2xl rounded-lg p-4 text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[#303538] text-[#E0E3E5] border border-[#555C61] rounded-tr-none'
                  : msg.isError
                  ? 'bg-rose-950/30 text-rose-300 border border-rose-500/50 rounded-tl-none'
                  : 'bg-[#292D30] text-[#E0E3E5] border border-[#555C61] rounded-tl-none'
              }`}
            >
              <div className="flex items-center justify-between gap-4 mb-1.5 pb-1 border-b border-[#555C61]/30">
                <span className="text-[11px] font-mono uppercase tracking-wider text-[#969DA3]">
                  {msg.sender === 'user' ? 'You' : 'DocNest AI'}
                </span>
                <span className="text-[10px] font-mono text-[#969DA3]">
                  {msg.timestamp}
                </span>
              </div>

              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Source Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#555C61]/50 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs text-[#F4D21F] font-semibold">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Verified Source Passages ({msg.citations.length})</span>
                  </div>
                  <div className="space-y-2">
                    {msg.citations.map((citation, idx) => (
                      <CitationCard
                        key={idx}
                        citation={citation}
                        index={idx}
                        onOpenPage={(filename, pageNum) => {
                          const targetDoc = documents.find((d) => d.filename === filename);
                          if (targetDoc && onOpenViewer) {
                            onOpenViewer(targetDoc, pageNum);
                          }
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Message Footer Actions */}
              {msg.sender === 'assistant' && !msg.isError && (
                <div className="mt-3 pt-2 border-t border-[#555C61]/30 flex items-center justify-between text-[11px] text-[#969DA3] font-mono">
                  <div className="flex items-center gap-2">
                    {msg.processingTime && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {msg.processingTime}s
                      </span>
                    )}
                    {msg.modelUsed && <span>• {msg.modelUsed}</span>}
                  </div>

                  <button
                    onClick={() => handleCopy(msg.id, msg.text)}
                    className="hover:text-[#E0E3E5] inline-flex items-center gap-1 p-0.5 rounded"
                  >
                    {copiedId === msg.id ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="bg-[#292D30] border border-[#555C61] rounded-lg rounded-tl-none p-4 max-w-sm flex items-center gap-3">
              <Loader2 className="w-4 h-4 text-[#F4D21F] animate-spin" />
              <span className="text-xs text-[#E0E3E5] font-medium">
                Searching passages & reasoning with Llama 3.2...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions Pills */}
      {suggestions.length > 0 && (
        <div className="px-4 py-2 bg-[#171A1C] border-t border-[#555C61] flex items-center gap-2 overflow-x-auto shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-[#F4D21F] shrink-0" />
          <span className="text-[11px] text-[#969DA3] shrink-0 font-mono">Suggested:</span>
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(s)}
              className="text-xs bg-[#202326] border border-[#555C61] hover:border-[#F4D21F] text-[#BFC3C7] hover:text-[#E0E3E5] px-2.5 py-1 rounded-full whitespace-nowrap transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input Form Bar */}
      <div className="p-3 md:p-4 bg-[#171A1C] border-t border-[#555C61] shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder={
              selectedDocId
                ? 'Ask a question grounded strictly in this document...'
                : 'Ask a question across all uploaded documents...'
            }
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            disabled={isLoading}
            className="carbon-input flex-1 py-2 px-3.5 text-sm"
          />

          <button
            type="submit"
            disabled={!inputQuestion.trim() || isLoading}
            className="btn-primary py-2 px-4 text-sm shrink-0"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Ask AI</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

