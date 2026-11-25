import React, { useState, useEffect, useRef } from 'react';
import ChatHeader from '../../components/chat/ChatHeader';
import ChatContainer from '../../components/chat/ChatContainer';
import WelcomeScreen from '../../components/chat/WelcomeScreen';
import ChatComposer from '../../components/chat/ChatComposer';
import ContextualResearchPanel from '../../components/chat/ContextualResearchPanel';
import {
  fetchSessionMessages,
  recordMessageFeedback,
  createChatSession,
  uploadDocumentFile,
  createResearchNote,
  autoTitleChatSession,
} from '../../services/api';

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
  const [isUploading, setIsUploading] = useState(false);
  const [currentStageKey, setCurrentStageKey] = useState('rewriting');
  const [activeTrace, setActiveTrace] = useState(null);
  const [activeCitations, setActiveCitations] = useState([]);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('citations');
  const [selectedDocIds, setSelectedDocIds] = useState(selectedDocId ? [selectedDocId] : []);
  const [attachments, setAttachments] = useState([]);
  const [selectedModel, setSelectedModel] = useState('llama3.2');
  const [searchMode, setSearchMode] = useState('hybrid');
  const [highlightedCitationId, setHighlightedCitationId] = useState(null);

  const abortControllerRef = useRef(null);

  useEffect(() => {
    if (selectedDocId) {
      const cleanId =
        typeof selectedDocId === 'object' && selectedDocId !== null
          ? selectedDocId.doc_id || selectedDocId.id
          : selectedDocId;
      setSelectedDocIds(cleanId ? [cleanId] : []);
    } else {
      setSelectedDocIds([]);
    }
  }, [selectedDocId]);

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
              timestamp: new Date(m.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
            }))
          );
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

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  const handleAddAttachments = (files) => {
    if (files.length > 0) {
      setAttachments((prev) => [...prev, ...files]);
    }
  };

  const handleRemoveAttachment = (indexToRemove) => {
    setAttachments((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handleSend = async (overrideText = null) => {
    const q = (overrideText !== null ? overrideText : inputQuestion).trim();
    if ((!q && attachments.length === 0) || isLoading || isUploading) return;

    const pendingAttachments = [...attachments];
    if (pendingAttachments.length > 0) {
      setIsUploading(true);
      for (const file of pendingAttachments) {
        try {
          await uploadDocumentFile(file);
        } catch (uploadErr) {
          console.error('Failed to upload attachment:', uploadErr);
        }
      }
      setAttachments([]);
      setIsUploading(false);
    }

    const effectiveQuestion = q || 'Summarize the attached document.';

    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      try {
        const newSess = await createChatSession(effectiveQuestion.slice(0, 32));
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
      text: effectiveQuestion,
      attachments: pendingAttachments.map((f) => ({ name: f.name, size: f.size })),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    setIsLoading(true);
    setCurrentStageKey('rewriting');

    const assistantMsgId = `ai_${Date.now()}`;
    let accumulatedTokens = '';
    let citationsFound = [];
    let latencyTrace = null;

    abortControllerRef.current = new AbortController();

    const cleanDocIds = selectedDocIds
      .map((d) => (typeof d === 'object' && d !== null ? d.doc_id || d.id : d))
      .filter(Boolean);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          question: effectiveQuestion,
          session_id: targetSessionId,
          doc_ids: cleanDocIds.length > 0 ? cleanDocIds : null,
          chat_history: messages.slice(-4),
          model: selectedModel,
          search_mode: searchMode,
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
              if (payload.stage) setCurrentStageKey(payload.stage);
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
              setCurrentStageKey('generating');
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

              if (targetSessionId && messages.length <= 1) {
                autoTitleChatSession(targetSessionId)
                  .then(() => {
                    if (onSessionCreated) onSessionCreated(targetSessionId);
                  })
                  .catch((e) => console.debug('Auto-title skipped:', e));
              }
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
      abortControllerRef.current = null;
    }
  };

  const handleRegenerate = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.sender === 'user');
    if (lastUserMsg) {
      handleSend(lastUserMsg.text);
    }
  };

  const handleEditUserMessage = (msgId, newText) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx !== -1) {
      setMessages((prev) => prev.slice(0, idx));
      handleSend(newText);
    }
  };

  const handleSaveNote = async (msg) => {
    try {
      await createResearchNote({
        title: `Research Note: ${msg.text.slice(0, 40)}...`,
        content: msg.text,
        session_id: activeSessionId,
        tags: ['chat-saved'],
        citations: msg.citations || [],
      });
    } catch (err) {
      console.error('Failed to save note:', err);
    }
  };

  const handleCitationClick = ({ filename, page_number, source_id }) => {
    if (source_id) {
      setHighlightedCitationId(source_id);
    }
    setRightPanelTab('citations');
    setRightPanelOpen(true);

    const doc = documents.find(
      (d) =>
        d.filename.toLowerCase() === (filename || '').toLowerCase() ||
        d.filename.toLowerCase().includes((filename || '').toLowerCase())
    );
    if (doc) {
      onOpenViewer(doc, page_number || 1);
    } else if (documents.length > 0) {
      onOpenViewer(documents[0], page_number || 1);
    }
  };

  const handleInspectSources = (msg) => {
    setActiveCitations(msg.citations || []);
    setActiveTrace(msg.trace || null);
    setRightPanelTab('citations');
    setRightPanelOpen(true);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-[#212121] text-[#ECECEC]">
      <div className="relative flex flex-1 flex-col h-full overflow-hidden">
        <ChatHeader
          documents={documents}
          selectedDocIds={selectedDocIds}
          onClearScope={() => {
            setSelectedDocIds([]);
            onSelectDocId(null);
          }}
          rightPanelOpen={rightPanelOpen}
          onToggleRightPanel={() => setRightPanelOpen((prev) => !prev)}
          citationCount={activeCitations.length}
        />

        <div className="flex-1 overflow-y-auto px-4 pt-6 sm:px-6">
          {isEmpty ? (
            <WelcomeScreen onPrompt={(prompt) => handleSend(prompt)} />
          ) : (
            <ChatContainer
              messages={messages}
              isLoading={isLoading}
              currentStageKey={currentStageKey}
              onEditUserMessage={handleEditUserMessage}
              onRegenerate={handleRegenerate}
              onFeedback={handleFeedback}
              onSaveNote={handleSaveNote}
              onCitationClick={handleCitationClick}
              onInspectSources={handleInspectSources}
            />
          )}
        </div>

        <div className="flex-shrink-0 bg-[#212121] px-4 pb-4 pt-2 sm:px-6">
          <ChatComposer
            value={inputQuestion}
            onChange={setInputQuestion}
            onSubmit={() => handleSend()}
            isLoading={isLoading}
            isUploading={isUploading}
            onStop={handleStopGeneration}
            attachments={attachments}
            onAddAttachments={handleAddAttachments}
            onRemoveAttachment={handleRemoveAttachment}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            searchMode={searchMode}
            onSelectSearchMode={setSearchMode}
          />
        </div>
      </div>

      {rightPanelOpen && (
        <ContextualResearchPanel
          activeCitations={activeCitations}
          activeTrace={activeTrace}
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleDoc={(docId) => {
            setSelectedDocIds((prev) =>
              prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
            );
          }}
          onClearScope={() => {
            setSelectedDocIds([]);
            onSelectDocId(null);
          }}
          onCitationClick={handleCitationClick}
          highlightedCitationId={highlightedCitationId}
          activeTab={rightPanelTab}
          setActiveTab={setRightPanelTab}
          onClose={() => setRightPanelOpen(false)}
        />
      )}
    </div>
  );
}
