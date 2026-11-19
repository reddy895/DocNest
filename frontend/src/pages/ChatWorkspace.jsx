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
    { title: 'Summarize Documents', desc: 'Synthesize key executive takeaways and core findings', icon: '📑', prompt: 'Please provide a comprehensive executive summary of the uploaded documents.' },
    { title: 'Extract Definitions', desc: 'Identify critical domain terms, metrics, and definitions', icon: '📖', prompt: 'Extract and define all important terms, technical concepts, and key metrics found across the documents.' },
    { title: 'Compare Key Findings', desc: 'Highlight agreements, differences, and contradictions', icon: '⚖️', prompt: 'Compare the primary arguments and findings across the documents, highlighting any contradictions.' },
    { title: 'Generate Exam Questions', desc: 'Create study and review questions with answers', icon: '❓', prompt: 'Generate 5 insightful conceptual and technical questions based on the uploaded document evidence.' },
  ];

  return (
    <div className="flex-1 flex h-[calc(100vh-3.5rem)] md:h-screen overflow-hidden bg-[#111315] text-[#F0F1F2]">
      {/* CENTER: Main Conversation View */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Header Bar */}
        <div className="h-13 border-b border-[#343A3F] px-4 md:px-6 flex items-center justify-between bg-[#111315]/80 backdrop-blur z-10 flex-shrink-0">
          <div className="flex items-center gap-2 truncate">
            <span className="text-xs font-mono uppercase tracking-wider text-[#A0A6AC]">
              Scope:
            </span>
            {selectedDocIds.length === 0 ? (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#191C1F] border border-[#343A3F] text-[#F0F1F2]">
                All Documents ({documents.length})
              </span>
            ) : (
              <div className="flex items-center gap-1">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#E5B83D]/15 border border-[#E5B83D]/50 text-[#E5B83D] truncate max-w-xs">
                  {documents.find((d) => d.doc_id === selectedDocIds[0])?.filename || '1 Document'}
                </span>
                <button
                  onClick={() => {
                    setSelectedDocIds([]);
                    onSelectDocId(null);
                  }}
                  className="text-xs text-[#A0A6AC] hover:text-[#F0F1F2] p-0.5"
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
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
                rightPanelOpen
                  ? 'bg-[#191C1F] text-[#E5B83D] border-[#E5B83D]/60'
                  : 'bg-[#191C1F] text-[#A0A6AC] border-[#343A3F] hover:text-[#F0F1F2]'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Research Context</span>
              {activeCitations.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-[#E5B83D] text-[#111315] font-bold rounded-full text-[10px]">
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
              <div className="w-12 h-12 rounded-xl bg-[#E5B83D]/10 border border-[#E5B83D]/30 flex items-center justify-center text-[#E5B83D] mb-4 shadow-sm">
                <Sparkles className="w-6 h-6 text-[#E5B83D]" />
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-[#F0F1F2] mb-2 tracking-tight">
                Where should we begin your research?
              </h2>
              <p className="text-xs md:text-sm text-[#A0A6AC] max-w-md mb-8">
                Ask questions across your uploaded documents. Answers are strictly grounded in document passages with page citations.
              </p>

              {/* Prompt Suggestions Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                {suggestedPrompts.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(item.prompt)}
                    className="p-3.5 bg-[#191C1F] hover:bg-[#22262A] border border-[#343A3F] hover:border-[#E5B83D]/60 rounded-xl transition text-left group"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-base">{item.icon}</span>
                      <span className="text-xs font-semibold text-[#F0F1F2] group-hover:text-[#E5B83D] transition">
                        {item.title}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#A0A6AC] line-clamp-2 leading-relaxed">
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
        <div className="border-t border-[#343A3F] p-4 bg-[#111315] flex-shrink-0">
          <div className="max-w-3xl mx-auto">
            {/* Active Document Scope Indicator */}
            {selectedDocIds.length > 0 && (
              <div className="mb-2 flex items-center justify-between px-3 py-1.5 bg-[#191C1F] border border-[#E5B83D]/40 rounded-xl text-xs text-[#F0F1F2]">
                <div className="flex items-center gap-2 truncate">
                  <span className="w-2 h-2 rounded-full bg-[#E5B83D] animate-ping" />
                  <span className="text-[#A0A6AC]">Scoped to:</span>
                  <span className="font-semibold text-[#E5B83D] truncate">
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
                  className="flex items-center gap-1 text-[11px] text-[#A0A6AC] hover:text-[#F0F1F2] px-2 py-0.5 rounded hover:bg-[#22262A] transition"
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
              className="relative flex items-end bg-[#191C1F] border border-[#343A3F] focus-within:border-[#E5B83D] rounded-2xl p-2 transition shadow-lg"
            >
              <textarea
                ref={textareaRef}
                value={inputQuestion}
                onChange={(e) => {
                  setInputQuestion(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask questions about your research documents... (Shift+Enter for newline)"
                rows={1}
                className="w-full bg-transparent border-none text-sm text-[#F0F1F2] placeholder-[#A0A6AC]/60 px-3 py-1.5 focus:outline-none resize-none max-h-44"
              />

              <div className="flex items-center gap-1.5 flex-shrink-0 pr-1 pb-0.5">
                {isLoading ? (
                  <button
                    type="button"
                    onClick={handleStopGeneration}
                    className="p-2 bg-[#22262A] hover:bg-[#343A3F] text-rose-400 rounded-xl transition"
                    title="Stop generation"
                  >
                    <Square className="w-4 h-4 fill-rose-400" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!inputQuestion.trim()}
                    className="p-2 bg-[#E5B83D] hover:bg-[#F2C64B] disabled:opacity-40 text-[#111315] rounded-xl font-bold transition shadow-sm"
                    title="Send question"
                  >
                    <Send className="w-4 h-4 stroke-[2.5]" />
                  </button>
                )}
              </div>
            </form>
            <p className="text-[10px] text-center text-[#A0A6AC]/60 mt-2 font-mono">
              Grounded in local ChromaDB vectors with Ollama LLM. Citations reference source document pages.
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
