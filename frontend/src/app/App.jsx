import React, { useState, useEffect } from 'react';
import AppShell from '../components/layout/AppShell';
import DocumentLibrary from './pages/DocumentLibrary';
import ChatWorkspace from './pages/ChatWorkspace';
import ResearchStudio from './pages/ResearchStudio';
import Settings from './pages/Settings';
import UploadModal from '../components/documents/UploadModal';
import DocumentViewer from '../components/documents/DocumentViewer';
import {
  fetchHealth,
  fetchDocuments,
  deleteDocumentById,
  fetchChatSessions,
  createChatSession,
  updateChatSession,
  deleteChatSession,
} from '../services/api';

export default function App() {
  // Conversation-first experience
  const [activeTab, setActiveTab] = useState('chat');
  const [documents, setDocuments] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);

  // Persistent Sessions
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);

  // Modals & Overlays
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState(null);
  const [viewingPage, setViewingPage] = useState(1);

  // Initial data loading
  const loadInitialData = async () => {
    try {
      const [healthData, docsData, sessionsData] = await Promise.all([
        fetchHealth().catch((e) => ({ status: 'error', error: e.message })),
        fetchDocuments().catch(() => ({ total_documents: 0, total_chunks: 0, documents: [] })),
        fetchChatSessions().catch(() => []),
      ]);

      setSystemStatus(healthData);
      setDocuments(docsData.documents || []);
      setTotalChunks(docsData.total_chunks || 0);
      setSessions(sessionsData || []);

      if (sessionsData && sessionsData.length > 0 && !activeSessionId) {
        setActiveSessionId(sessionsData[0].id);
      }
    } catch (err) {
      console.error('Data initialization error:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleUploadSuccess = () => {
    loadInitialData();
  };

  const handleDeleteDocument = async (docId) => {
    try {
      await deleteDocumentById(docId);
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
      loadInitialData();
    } catch (err) {
      alert(`Could not delete document: ${err.message}`);
    }
  };

  const handleOpenViewer = (doc, page = 1) => {
    setViewingDocument(doc);
    setViewingPage(page);
  };

  const handleQueryDocument = (docOrId) => {
    const docId = typeof docOrId === 'object' && docOrId !== null
      ? (docOrId.doc_id || docOrId.id)
      : docOrId;
    setSelectedDocId(docId);
    setActiveTab('chat');
  };

  // Session Handlers
  const handleNewSession = async () => {
    try {
      const newSession = await createChatSession('New Research');
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleRenameSession = async (sessionId, newTitle) => {
    try {
      const updated = await updateChatSession(sessionId, { title: newTitle });
      setSessions((prev) => prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s)));
    } catch (err) {
      console.error('Failed to rename session:', err);
    }
  };

  const handlePinSession = async (sessionId, isPinned) => {
    try {
      const updated = await updateChatSession(sessionId, { is_pinned: isPinned });
      setSessions((prev) =>
        prev
          .map((s) => (s.id === sessionId ? { ...s, is_pinned: updated.is_pinned } : s))
          .sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0))
      );
    } catch (err) {
      console.error('Failed to pin session:', err);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteChatSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId);
        setActiveSessionId(remaining[0]?.id || null);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  return (
    <>
      <AppShell
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemStatus={systemStatus}
        onOpenUpload={() => setIsUploadOpen(true)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={(id) => setActiveSessionId(id)}
        onNewSession={handleNewSession}
        onRenameSession={handleRenameSession}
        onPinSession={handlePinSession}
        onDeleteSession={handleDeleteSession}
      >
        {activeTab === 'chat' && (
          <ChatWorkspace
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDocId={setSelectedDocId}
            onOpenViewer={handleOpenViewer}
            activeSessionId={activeSessionId}
            onSessionCreated={(newId) => {
              setActiveSessionId(newId);
              loadInitialData();
            }}
          />
        )}

        {activeTab === 'library' && (
          <DocumentLibrary
            documents={documents}
            onDeleteDocument={handleDeleteDocument}
            onViewDocument={(doc) => handleOpenViewer(doc, 1)}
            onQueryDocument={handleQueryDocument}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        )}

        {activeTab === 'research' && (
          <ResearchStudio
            documents={documents}
            onOpenViewer={handleOpenViewer}
          />
        )}

        {activeTab === 'settings' && (
          <Settings
            systemStatus={systemStatus}
            onRefreshStatus={loadInitialData}
          />
        )}
      </AppShell>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Document Viewer Modal */}
      {viewingDocument && (
        <DocumentViewer
          document={viewingDocument}
          initialPage={viewingPage}
          onClose={() => setViewingDocument(null)}
        />
      )}
    </>
  );
}
