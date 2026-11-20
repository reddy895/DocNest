import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Loader2,
  Copy,
  Check,
  FileText,
  Filter,
  Sparkles,
  AlertCircle,
  Square,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Layers,
  ChevronRight,
  Sliders,
  ExternalLink,
  X,
  Bookmark,
  CheckCircle2,
} from 'lucide-react';
import MarkdownRenderer from '../components/MarkdownRenderer';
import ContextualResearchPanel from '../components/ContextualResearchPanel';
import {
  fetchSessionMessages,
  recordMessageFeedback,
  createChatSession,
} from '../services/api';

export default function ChatWorkspace({
  documents = [],
  selectedDocId = null,
  onSelectDocId = () => {},
  onOpenViewer = () => {},
  activeSessionId = null,
  onSessionCreated = () => {},
}) {
  const [messages, setMessages] = useState([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingStage, setStreamingStage] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [activeTrace, setActiveTrace] = useState(null);
  const [activeCitations, setActiveCitations] = useState([]);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('citations'); // 'citations' | 'inspector' | 'scope'
  const [selectedDocIds, setSelectedDocIds] = useState(selectedDocId ? [selectedDocId] : []);
  const [savedNoteSuccess, setSavedNoteSuccess] = useState(null);

  const abortControllerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Sync selectedDocId prop into selectedDocIds array
  useEffect(() => {
    if (selectedDocId) {
      const cleanId = typeof selectedDocId === 'object' && selectedDocId !== null
        ? (selectedDocId.doc_id || selectedDocId.id)
        : selectedDocId;
      setSelectedDocIds(cleanId ? [cleanId] : []);
    } else {
      setSelectedDocIds([]);
    }
  }, [selectedDocId]);

  // Load message history when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      setActiveCitations([]);
      setActiveTrace(null);
      return;
    }

    async function loadHistory() {
      try {
        const history = await fetchSessionMessages(activeSessionId);
        if (history && history.length > 0) {
          setMessages(
            history.map((m) => ({
              id: m.id,
              sender: m.sender,
              text: m.text,
              citations: m.citations || [],
              trace: m.retrieval_trace || {},
              feedback_rating: m.feedback_rating,
              timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }))
          );
          // Set citations from last assistant message
          const lastAssistant = [...history].reverse().find((m) => m.sender === 'assistant');
          if (lastAssistant) {
            setActiveCitations(lastAssistant.citations || []);
            setActiveTrace(lastAssistant.retrieval_trace || null);
          }
        } else {
          setMessages([]);
        }
      } catch (err) {
        console.warn('Failed to load session messages:', err);
      }
    }
    loadHistory();
  }, [activeSessionId]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, streamingStage]);

  // Feedback handler
  const handleFeedback = async (messageId, rating) => {
    try {
      await recordMessageFeedback(messageId, rating);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, feedback_rating: rating } : m))
      );
    } catch (err) {
      console.error('Failed to record feedback:', err);
    }
  };

  // Copy handler
  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Stop generation
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setStreamingStage('');
    }
  };

  // Send or Stream question
  const handleSend = async (overrideText = null) => {
    const q = (overrideText || inputQuestion).trim();
    if (!q || isLoading) return;

    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      try {
        const newSess = await createChatSession(q.slice(0, 32) + '...');
        targetSessionId = newSess.id;
        if (onSessionCreated) onSessionCreated(newSess.id);
      } catch (err) {
        console.error('Could not create session:', err);
      }
    }

    const userMsgId = `user_${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    setIsLoading(true);
    setStreamingStage('Resolving query & context...');

    const assistantMsgId = `ai_${Date.now()}`;
    let accumulatedTokens = '';
    let citationsFound = [];
    let latencyTrace = null;

    abortControllerRef.current = new AbortController();

    const cleanDocIds = selectedDocIds
      .map((d) => (typeof d === 'object' && d !== null ? (d.doc_id || d.id) : d))
      .filter(Boolean);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          question: q,
          session_id: targetSessionId,
          doc_ids: cleanDocIds.length > 0 ? cleanDocIds : null,
          chat_history: messages.slice(-4),
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          sender: 'assistant',
          text: '',
          citations: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const payload = JSON.parse(line.replace('data: ', ''));

            if (payload.event === 'status') {
              setStreamingStage(payload.message || '');
            } else if (payload.event === 'retrieval') {
              citationsFound = payload.citations || [];
              latencyTrace = payload.trace || null;
              setActiveCitations(citationsFound);
              setActiveTrace(latencyTrace);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, citations: citationsFound, trace: latencyTrace }
                    : m
                )
              );
            } else if (payload.event === 'token') {
              accumulatedTokens += payload.token;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, text: accumulatedTokens } : m
                )
              );
            } else if (payload.event === 'done') {
              accumulatedTokens = payload.full_text || accumulatedTokens;
              latencyTrace = payload.trace || latencyTrace;
              setActiveCitations(citationsFound);
              setActiveTrace(latencyTrace);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        text: accumulatedTokens,
                        citations: citationsFound,
                        trace: latencyTrace,
                      }
                    : m
                )
              );
            }
          } catch (e) {
            console.warn('Error parsing stream chunk:', e);
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => [
          ...prev,
          {
            id: `err_${Date.now()}`,
            sender: 'assistant',
            text: `Error generating response: ${err.message}`,
            citations: [],
            isError: true,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } finally {
      setIsLoading(false);
      setStreamingStage('');
      abortControllerRef.current = null;
    }
  };

  // Regenerate last response
  const handleRegenerate = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.sender === 'user');
    if (lastUserMsg) {
      handleSend(lastUserMsg.text);
    }
  };

  // Click citation in message or right panel
  const handleCitationClick = ({ filename, page_number }) => {
    const doc = documents.find(
      (d) =>
        d.filename.toLowerCase() === filename.toLowerCase() ||
        d.filename.toLowerCase().includes(filename.toLowerCase())
    );
    if (doc) {
      onOpenViewer(doc, page_number || 1);
    } else if (documents.length > 0) {
      onOpenViewer(documents[0], page_number || 1);
    }
  };

  const isEmpty = messages.length === 0;

  const suggestedPrompts = [
    { title: 'Summarize documents', desc: 'Synthesize executive takeaways and core findings', icon: '📑', prompt: 'Summarize my uploaded documents with key takeaways and conclusions.' },
    { title: 'Find key findings', desc: 'Identify primary discoveries, results, and claims', icon: '🔍', prompt: 'Find the most important findings and core conclusions across the uploaded documents.' },
    { title: 'Compare documents', desc: 'Highlight agreements, divergences, and contradictions', icon: '⚖️', prompt: 'Compare two research papers or documents, highlighting agreements and contradictions.' },
    { title: 'Explain simply', desc: 'Break down complex concepts into accessible terms', icon: '💡', prompt: 'Explain this document in simple language for a general audience.' },
    { title: 'Extract statistics', desc: 'Extract percentages, metrics, benchmarks, and data', icon: '📊', prompt: 'Extract key statistics, quantitative metrics, and performance data from the documents.' },
    { title: 'Generate report', desc: 'Create a comprehensive cited research briefing', icon: '📝', prompt: 'Generate a structured report with methodology, findings, and page citations.' },
  ];

  return (
    <div className="flex-1 flex h-[calc(100vh-3.5rem)] md:h-screen overflow-hidden bg-[#101214] text-[#F2F3F4]">
      {/* CENTER: Main Conversation View */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Bar */}
        <div className="h-13 border-b border-[#30353A] px-4 md:px-6 flex items-center justify-between bg-[#17191B]/90 backdrop-blur z-10 flex-shrink-0">
          <div className="flex items-center gap-2 truncate">
            <span className="text-xs font-mono uppercase tracking-wider text-[#A2A9B0]">
              Scope:
            </span>
            {selectedDocIds.length === 0 ? (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#1A1D20] border border-[#30353A] text-[#F2F3F4]">
                All Documents ({documents.length})
              </span>
            ) : (
              <div className="flex items-center gap-1">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#F5C542]/15 border border-[#F5C542]/50 text-[#F5C542] truncate max-w-xs">
                  {documents.find((d) => (d.doc_id || d.id) === selectedDocIds[0])?.filename || '1 Document'}
                </span>
                <button
                  onClick={() => {
                    setSelectedDocIds([]);
                    onSelectDocId(null);
                  }}
                  className="text-xs text-[#A2A9B0] hover:text-[#F2F3F4] p-0.5"
                  title="Clear document filter"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium border transition ${
                rightPanelOpen
                  ? 'bg-[#1A1D20] text-[#F5C542] border-[#F5C542]/60'
                  : 'bg-[#1A1D20] text-[#A2A9B0] border-[#30353A] hover:text-[#F2F3F4]'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Research Context</span>
              {activeCitations.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-[#F5C542] text-[#101214] font-bold rounded-full text-[10px]">
                  {activeCitations.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Message Feed / Empty State */}
        <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6 space-y-6">
          {isEmpty ? (
            /* ChatGPT-Inspired Centered Empty State */
            <div className="max-w-2xl mx-auto h-full flex flex-col items-center justify-center text-center py-10">
              <div className="w-12 h-12 rounded-2xl bg-[#F5C542]/10 border border-[#F5C542]/30 flex items-center justify-center text-[#F5C542] mb-4 shadow-sm">
                <Sparkles className="w-6 h-6 text-[#F5C542]" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-[#F2F3F4] mb-2 tracking-tight">
                Your documents. Your knowledge. One intelligent workspace.
              </h2>
              <p className="text-xs md:text-sm text-[#A2A9B0] max-w-md mb-8">
                Ask questions, explore research, compare documents, and turn information into insights.
              </p>

              {/* Prompt Suggestions Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                {suggestedPrompts.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(item.prompt)}
                    className="p-3.5 bg-[#17191B] hover:bg-[#1A1D20] border border-[#30353A] hover:border-[#F5C542]/60 rounded-xl transition text-left group shadow-sm"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-base">{item.icon}</span>
                      <span className="text-xs font-semibold text-[#F2F3F4] group-hover:text-[#F5C542] transition">
                        {item.title}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#A2A9B0] line-clamp-2 leading-relaxed">
                      {item.desc}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Conversation Messages Feed */
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${
                    msg.sender === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  {/* Message Bubble Container */}
                  <div
                    className={`relative rounded-2xl p-4 md:p-5 max-w-[92%] sm:max-w-[85%] text-sm ${
                      msg.sender === 'user'
                        ? 'bg-[#191C1F] border border-[#343A3F] text-[#F0F1F2] rounded-br-sm'
                        : 'bg-[#191C1F]/60 border border-[#343A3F]/80 text-[#F0F1F2] rounded-bl-sm w-full'
                    }`}
                  >
                    {/* Header info */}
                    <div className="flex items-center justify-between text-[11px] text-[#A0A6AC] mb-2 font-mono">
                      <span className="font-semibold text-[#E5B83D]">
                        {msg.sender === 'user' ? 'YOU' : 'DOCNEST RESEARCH AI'}
                      </span>
                      <span>{msg.timestamp}</span>
                    </div>

                    {/* Content */}
                    {msg.sender === 'user' ? (
                      <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    ) : (
                      <div className="prose prose-invert max-w-none text-sm">
                        <MarkdownRenderer
                          content={msg.text}
                          onCitationClick={handleCitationClick}
                        />
                      </div>
                    )}

                    {/* Citations Preview Strip for Assistant Message */}
                    {msg.sender === 'assistant' && msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-[#343A3F]/60 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] uppercase font-mono tracking-wider text-[#A0A6AC]">
                          Sources:
                        </span>
                        {msg.citations.map((cite, cIdx) => (
                          <button
                            key={cIdx}
                            onClick={() => handleCitationClick(cite)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#22262A] hover:bg-[#343A3F] border border-[#343A3F] rounded text-[11px] text-[#F0F1F2] transition"
                            title={`Relevance score: ${(cite.relevance_score * 100).toFixed(0)}%`}
                          >
                            <FileText className="w-3 h-3 text-[#E5B83D]" />
                            <span className="truncate max-w-[120px]">{cite.filename}</span>
                            <span className="text-[#A0A6AC] font-mono">p.{cite.page_number}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Action Bar for Assistant Message */}
                    {msg.sender === 'assistant' && msg.text && (
                      <div className="mt-3 pt-2 flex items-center justify-between text-xs text-[#A0A6AC]">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopy(msg.id, msg.text)}
                            className="p-1 hover:text-[#F0F1F2] rounded transition flex items-center gap-1"
                            title="Copy response"
                          >
                            {copiedId === msg.id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.id, 1)}
                            className={`p-1 rounded transition hover:text-[#E5B83D] ${
                              msg.feedback_rating === 1 ? 'text-[#E5B83D]' : ''
                            }`}
                            title="Helpful response"
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.id, -1)}
                            className={`p-1 rounded transition hover:text-rose-400 ${
                              msg.feedback_rating === -1 ? 'text-rose-400' : ''
                            }`}
                            title="Unhelpful response"
                          >
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => {
                              setActiveCitations(msg.citations || []);
                              setActiveTrace(msg.trace || null);
                              setRightPanelOpen(true);
                            }}
                            className="text-[11px] hover:text-[#E5B83D] ml-1 transition"
                          >
                            Inspect Evidence
                          </button>
                        </div>

                        {msg.trace?.retrieval_ms && (
                          <span className="text-[10px] font-mono text-[#A0A6AC]/70">
                            Latency: {msg.trace.retrieval_ms}ms retrieval
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming Indicator */}
              {isLoading && (
                <div className="flex items-center gap-3 p-3.5 bg-[#191C1F] border border-[#343A3F] rounded-xl text-xs text-[#A0A6AC] max-w-md animate-pulse">
                  <Loader2 className="w-4 h-4 animate-spin text-[#E5B83D]" />
                  <span>{streamingStage || 'Synthesizing response...'}</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* BOTTOM: Sticky Prompt Input Bar */}
        <div className="border-t border-[#30353A] p-4 bg-[#101214] flex-shrink-0">
          <div className="max-w-3xl mx-auto">
            {/* Active Document Scope Indicator */}
            {selectedDocIds.length > 0 && (
              <div className="mb-2 flex items-center justify-between px-3 py-1.5 bg-[#17191B] border border-[#F5C542]/40 rounded-xl text-xs text-[#F2F3F4]">
                <div className="flex items-center gap-2 truncate">
                  <span className="w-2 h-2 rounded-full bg-[#F5C542] animate-ping" />
                  <span className="text-[#A2A9B0]">Scoped to:</span>
                  <span className="font-semibold text-[#F5C542] truncate">
                    {selectedDocIds.length === 1
                      ? documents.find((d) => (d.doc_id || d.id) === selectedDocIds[0])?.filename || '1 document'
                      : `${selectedDocIds.length} documents`}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedDocIds([]);
                    onSelectDocId(null);
                  }}
                  className="flex items-center gap-1 text-[11px] text-[#A2A9B0] hover:text-[#F2F3F4] px-2 py-0.5 rounded hover:bg-[#1A1D20] transition"
                >
                  <X className="w-3 h-3" />
                  <span>Search All Documents</span>
                </button>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="relative flex items-end bg-[#17191B] border border-[#30353A] focus-within:border-[#F5C542] rounded-2xl p-2.5 transition shadow-xl"
            >
              <textarea
                ref={textareaRef}
                value={inputQuestion}
                onChange={(e) => {
                  setInputQuestion(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask anything about your documents... (Enter to send, Shift+Enter for newline)"
                rows={1}
                className="w-full bg-transparent border-none text-sm text-[#F2F3F4] placeholder-[#A2A9B0]/60 px-3 py-1.5 focus:outline-none resize-none max-h-52 leading-relaxed"
              />

              <div className="flex items-center gap-2 flex-shrink-0 pr-1 pb-0.5">
                {isLoading ? (
                  <button
                    type="button"
                    onClick={handleStopGeneration}
                    className="p-2.5 bg-[#1A1D20] hover:bg-[#22262B] text-rose-400 rounded-xl transition border border-[#30353A]"
                    title="Stop generation"
                  >
                    <Square className="w-4 h-4 fill-rose-400" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!inputQuestion.trim()}
                    className="p-2.5 bg-[#F5C542] hover:bg-[#FFD358] disabled:opacity-40 text-[#101214] rounded-xl font-bold transition shadow-sm"
                    title="Send question"
                  >
                    <Send className="w-4 h-4 stroke-[2.5]" />
                  </button>
                )}
              </div>
            </form>
            <p className="text-[10px] text-center text-[#A2A9B0]/60 mt-2 font-mono">
              Grounded in local ChromaDB vectors with Ollama Llama 3.2. Every factual claim contains page-level citations.
            </p>
          </div>
        </div>
      </div>

      {/* RIGHT CONTEXTUAL RESEARCH PANEL */}
      <ContextualResearchPanel
        isOpen={rightPanelOpen}
        onClose={() => setRightPanelOpen(false)}
        activeTab={rightPanelTab}
        setActiveTab={setRightPanelTab}
        citations={activeCitations}
        trace={activeTrace}
        documents={documents}
        selectedDocIds={selectedDocIds}
        onToggleDocScope={(id) => {
          setSelectedDocIds((prev) =>
            prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
          );
        }}
        onSelectAllDocs={() => {
          setSelectedDocIds([]);
          onSelectDocId(null);
        }}
        onCitationClick={handleCitationClick}
      />
    </div>
  );
}
