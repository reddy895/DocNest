import React, { useState, useEffect } from 'react';
import AppLayout from './layouts/AppLayout';
import Dashboard from './pages/Dashboard';
import DocumentLibrary from './pages/DocumentLibrary';
import ChatWorkspace from './pages/ChatWorkspace';
import Settings from './pages/Settings';
import UploadModal from './components/UploadModal';
import DocumentViewer from './components/DocumentViewer';
import { fetchHealth, fetchDocuments, deleteDocumentById } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [documents, setDocuments] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);

  // Modals & Overlays
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState(null);
  const [viewingPage, setViewingPage] = useState(1);

  // Initial data loading
  const loadInitialData = async () => {
    try {
      const [healthData, docsData] = await Promise.all([
        fetchHealth().catch((e) => ({ status: 'error', error: e.message })),
        fetchDocuments().catch(() => ({ total_documents: 0, total_chunks: 0, documents: [] })),
      ]);

      setSystemStatus(healthData);
      setDocuments(docsData.documents || []);
      setTotalChunks(docsData.total_chunks || 0);
    } catch (err) {
      console.error('Data initialization error:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleUploadSuccess = (newDoc) => {
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

  const handleQueryDocument = (docId) => {
    setSelectedDocId(docId);
    setActiveTab('chat');
  };

  return (
    <>
      <AppLayout
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemStatus={systemStatus}
        onOpenUpload={() => setIsUploadOpen(true)}
      >
        {activeTab === 'dashboard' && (
          <Dashboard
            documents={documents}
            totalChunks={totalChunks}
            systemStatus={systemStatus}
            onNavigate={(tab) => setActiveTab(tab)}
            onOpenUpload={() => setIsUploadOpen(true)}
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

        {activeTab === 'chat' && (
          <ChatWorkspace
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDocId={setSelectedDocId}
            onOpenViewer={handleOpenViewer}
          />
        )}

        {activeTab === 'settings' && (
          <Settings
            systemStatus={systemStatus}
            onRefreshStatus={loadInitialData}
          />
        )}
      </AppLayout>

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
