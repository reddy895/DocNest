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
  Plus,
  PanelLeftClose,
  PanelLeft,
  ChevronRight,
  BookOpen,
  Eye,
  Sliders,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import {
  fetchChatSessions,
  createChatSession,
  fetchSessionMessages,
  deleteChatSession,
  recordMessageFeedback,
} from '../services/api';
import RetrievalInspector from '../components/RetrievalInspector';

export default function ChatWorkspace({
  documents = [],
  selectedDocId = null,
  onSelectDocId,
  onOpenViewer,
}) {
  // Session State
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionSidebarOpen, setSessionSidebarOpen] = useState(true);

  // Chat Messages State
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
  const [streamingStage, setStreamingStage] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [copiedId, setCopiedId] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [activeTrace, setActiveTrace] = useState(null);
  const [evidencePanelOpen, setEvidencePanelOpen] = useState(false);

  const messagesEndRef = useRef(null);

  // 1. Load Sessions on Mount
  useEffect(() => {
    async function loadSessions() {
      try {
        const list = await fetchChatSessions();
        setSessions(list);
        if (list.length > 0 && !currentSessionId) {
          setCurrentSessionId(list[0].id);
        }
      } catch (err) {
        console.warn('Failed to load sessions:', err);
      }
    }
    loadSessions();
  }, []);

  // 2. Fetch Messages when Session Changes
  useEffect(() => {
    if (!currentSessionId) return;
    async function loadHistory() {
      try {
        const history = await fetchSessionMessages(currentSessionId);
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
        }
      } catch (err) {
        console.warn('Failed to load session messages:', err);
      }
    }
    loadHistory();
  }, [currentSessionId]);

  // 3. Dynamic Suggestions based on scope
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
  }, [messages, isLoading, streamingStage]);

  // 4. Create New Session
  const handleNewSession = async () => {
    try {
      const newSess = await createChatSession(`Chat ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
      setSessions((prev) => [newSess, ...prev]);
      setCurrentSessionId(newSess.id);
      setMessages([
        {
          id: 'welcome',
          sender: 'assistant',
          text: 'Started a new session. What would you like to explore in your documents?',
          citations: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };

  // 5. Delete Session
  const handleDeleteSession = async (e, sessId) => {
    e.stopPropagation();
    try {
      await deleteChatSession(sessId);
      const remaining = sessions.filter((s) => s.id !== sessId);
      setSessions(remaining);
      if (currentSessionId === sessId) {
        if (remaining.length > 0) {
          setCurrentSessionId(remaining[0].id);
        } else {
          setCurrentSessionId(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  // 6. Feedback Handler
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

  // 7. Send Message / Stream
  const handleSend = async (questionText = null) => {
    const q = (questionText || inputQuestion).trim();
    if (!q || isLoading) return;

    // Ensure session exists
    let activeSessionId = currentSessionId;
    if (!activeSessionId) {
      try {
        const created = await createChatSession(q.slice(0, 30) + '...');
        setSessions((prev) => [created, ...prev]);
        setCurrentSessionId(created.id);
        activeSessionId = created.id;
      } catch (err) {
        console.error('Session creation failed:', err);
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
    setIsLoading(true);
    setStreamingStage('Initializing hybrid retrieval...');

    const assistantMsgId = `ai_${Date.now()}`;
    let accumulatedTokens = '';
    let citationsFound = [];
    let latencyTrace = null;

    try {
      // Execute SSE streaming request
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          session_id: activeSessionId,
          doc_ids: selectedDocId ? [selectedDocId] : null,
          chat_history: messages.slice(-4),
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      // Initialize assistant placeholder
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
            console.warn('Error parsing SSE frame:', e);
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `Error connecting to generation service: ${err.message}`,
          citations: [],
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
      setStreamingStage('');
    }
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] md:h-[calc(100vh-3.5rem)] overflow-hidden bg-carbon-primary text-silver-primary">
      {/* PANE 1: Collapsible Session History Sidebar */}
      <div
        className={`${
          sessionSidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 ease-in-out border-r border-silver-border bg-carbon-deep flex flex-col shrink-0 overflow-hidden`}
      >
        <div className="p-3 border-b border-silver-border flex items-center justify-between">
          <button
            onClick={handleNewSession}
            className="flex-1 py-1.5 px-3 bg-signal-yellow hover:bg-signal-hover text-carbon-deep text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
          <button
            onClick={() => setSessionSidebarOpen(false)}
            className="p-1 text-silver-secondary hover:text-silver-light ml-2"
            title="Collapse Sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-silver-secondary text-center py-6 italic">No conversations yet.</p>
          ) : (
            sessions.map((sess) => {
              const isActive = sess.id === currentSessionId;
              return (
                <div
                  key={sess.id}
                  onClick={() => setCurrentSessionId(sess.id)}
                  className={`w-full group p-2.5 rounded-lg flex items-center justify-between text-xs cursor-pointer transition ${
                    isActive
                      ? 'bg-carbon-surface text-signal-yellow border border-silver-border font-semibold'
                      : 'text-silver-secondary hover:bg-carbon-secondary hover:text-silver-light'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{sess.title || 'Untitled Session'}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(e, sess.id)}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5 rounded transition"
                    title="Delete session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* PANE 2: Main AI Chat Stream */}
      <div className="flex-1 flex flex-col min-w-0 bg-carbon-primary relative">
        {/* Top Control Bar */}
        <div className="p-3 bg-carbon-deep border-b border-silver-border flex items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-3">
            {!sessionSidebarOpen && (
              <button
                onClick={() => setSessionSidebarOpen(true)}
                className="p-1.5 text-silver-secondary hover:text-silver-light bg-carbon-surface rounded-lg border border-silver-border transition"
                title="Expand History"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            )}

            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-signal-yellow" />
              <span className="text-xs text-silver-secondary font-mono">Scope:</span>
              <select
                value={selectedDocId || ''}
                onChange={(e) => onSelectDocId && onSelectDocId(e.target.value || null)}
                className="py-1 px-2.5 text-xs bg-carbon-surface border border-silver-border rounded-lg text-silver-light font-mono focus:border-signal-yellow focus:outline-none"
              >
                <option value="">Entire Library (All Documents)</option>
                {documents.map((doc) => (
                  <option key={doc.doc_id} value={doc.doc_id}>
                    {doc.filename} ({doc.page_count} p.)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setEvidencePanelOpen(!evidencePanelOpen)}
              className={`px-2.5 py-1 text-xs rounded-lg border transition flex items-center gap-1.5 ${
                evidencePanelOpen
                  ? 'bg-carbon-surface border-signal-yellow text-signal-yellow font-bold'
                  : 'bg-carbon-deep border-silver-border text-silver-secondary hover:text-silver-light'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Evidence Inspector</span>
            </button>
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-2xl rounded-xl p-4 text-sm leading-relaxed shadow-carbon-sm ${
                  msg.sender === 'user'
                    ? 'bg-carbon-surface text-silver-light border border-silver-border rounded-tr-none'
                    : msg.isError
                    ? 'bg-red-950/40 text-red-300 border border-red-800/60 rounded-tl-none'
                    : 'bg-carbon-secondary text-silver-light border border-silver-border rounded-tl-none'
                }`}
              >
                {/* Message Header */}
                <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-silver-border/40">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-signal-yellow font-bold">
                    {msg.sender === 'user' ? 'You' : 'DocNest Intelligence'}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-silver-secondary">{msg.timestamp}</span>
                    <button
                      onClick={() => handleCopy(msg.id, msg.text)}
                      className="text-silver-secondary hover:text-silver-light transition"
                      title="Copy response"
                    >
                      {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Message Body */}
                <div className="whitespace-pre-wrap">
                  {msg.text}
                  {isLoading && msg.sender === 'assistant' && msg.id === messages[messages.length - 1]?.id && (
                    <span className="inline-block w-2 h-4 ml-1 bg-signal-yellow animate-pulse align-middle" />
                  )}
                  {!msg.text && isLoading && msg.sender === 'assistant' && (
                    <span className="text-silver-secondary italic text-xs">Analyzing documents & synthesizing response...</span>
                  )}
                </div>

                {/* Inline Citations Pills */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3.5 pt-3 border-t border-silver-border/40 space-y-2">
                    <div className="text-[11px] font-mono uppercase text-silver-secondary flex items-center gap-1.5">
                      <BookOpen className="w-3 h-3 text-signal-yellow" />
                      <span>Retrieved Evidence ({msg.citations.length} sources):</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={c.source_id || cIdx}
                          onClick={() => {
                            setSelectedCitation(c);
                            setEvidencePanelOpen(true);
                          }}
                          className="px-2.5 py-1 bg-carbon-surface hover:bg-carbon-deep border border-silver-border rounded-lg text-xs font-mono flex items-center gap-1.5 text-silver-light hover:border-signal-yellow transition"
                        >
                          <FileText className="w-3 h-3 text-signal-yellow" />
                          <span>{c.filename}, p. {c.page_number}</span>
                          <span className="text-[10px] text-emerald-400 font-bold">
                            {Math.round(c.relevance_score * 100)}%
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Feedback rating for Assistant responses */}
                {msg.sender === 'assistant' && msg.id !== 'welcome' && (
                  <div className="mt-2.5 pt-2 flex items-center justify-between text-[11px] text-silver-secondary border-t border-silver-border/20">
                    <div className="flex items-center gap-1.5">
                      <span>Helpful?</span>
                      <button
                        onClick={() => handleFeedback(msg.id, 1)}
                        className={`p-1 rounded hover:bg-carbon-surface ${
                          msg.feedback_rating === 1 ? 'text-emerald-400 font-bold' : ''
                        }`}
                        title="Good answer"
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleFeedback(msg.id, -1)}
                        className={`p-1 rounded hover:bg-carbon-surface ${
                          msg.feedback_rating === -1 ? 'text-rose-400 font-bold' : ''
                        }`}
                        title="Inaccurate or ungrounded"
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {msg.trace?.total_ms && (
                      <span className="font-mono text-[10px]">
                        Latency: {msg.trace.total_ms}ms
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Live Streaming Stage Milestone Badge */}
          {isLoading && streamingStage && (
            <div className="flex items-center gap-2 p-3 bg-carbon-deep border border-silver-border/60 rounded-xl text-xs font-mono text-silver-secondary animate-pulse max-w-md">
              <Loader2 className="w-4 h-4 animate-spin text-signal-yellow shrink-0" />
              <span>{streamingStage}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        {suggestions.length > 0 && messages.length <= 2 && (
          <div className="px-6 pb-2 flex items-center gap-2 overflow-x-auto text-xs">
            <Sparkles className="w-3.5 h-3.5 text-signal-yellow shrink-0" />
            {suggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(s)}
                className="px-3 py-1 bg-carbon-surface border border-silver-border hover:border-signal-yellow rounded-full text-silver-light whitespace-nowrap text-xs transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 bg-carbon-deep border-t border-silver-border shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              placeholder="Ask a question grounded in your documents (e.g. 'What were Q3 revenue numbers?')..."
              disabled={isLoading}
              className="flex-1 py-2.5 px-4 bg-carbon-primary border border-silver-border rounded-xl text-sm text-silver-light placeholder-silver-secondary/50 focus:border-signal-yellow focus:outline-none"
            />
            <button
              type="submit"
              disabled={!inputQuestion.trim() || isLoading}
              className="p-2.5 bg-signal-yellow hover:bg-signal-hover text-carbon-deep font-bold rounded-xl transition disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* PANE 3: Evidence & Retrieval Inspector Drawer */}
      {evidencePanelOpen && (
        <div className="w-80 md:w-96 border-l border-silver-border bg-carbon-deep flex flex-col shrink-0 animate-fade-in overflow-hidden">
          <RetrievalInspector
            trace={activeTrace}
            citations={messages[messages.length - 1]?.citations || []}
            selectedCitation={selectedCitation}
            onSelectCitation={(c) => {
              setSelectedCitation(c);
              if (onOpenViewer) {
                const matchedDoc = documents.find((d) => d.filename === c.filename);
                if (matchedDoc) {
                  onOpenViewer(matchedDoc, c.page_number, c.content, c.section_heading, c.relevance_score);
                }
              }
            }}
            onClose={() => setEvidencePanelOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
