# DocNest Frontend Architecture Audit & ChatGPT UI Transformation Plan

## 1. Existing Frontend Stack & Structure
- **Framework**: React 18 (`^18.3.1`) + Vite (`^6.0.0`) + Tailwind CSS (`^3.4.15`)
- **Icons**: `lucide-react`
- **Entry**: `frontend/src/main.jsx` -> `frontend/src/app/App.jsx` -> `frontend/src/components/layout/AppShell.jsx`
- **Pages**:
  - `ChatWorkspace.jsx`: Main SSE chat interface (`/api/chat/stream`), citations, scope selection, attachments
  - `DocumentLibrary.jsx`: Multi-format document repository (PDF, DOCX, TXT, MD, CSV), upload, reindex, preview, raw text inspector
  - `ResearchStudio.jsx`: Summarize, compare, quiz, flashcards, notes
  - `SavedNotes.jsx`: Research notes management
  - `Settings.jsx`: System & user settings
- **API Layer**: `frontend/src/services/api.js` (REST endpoints for auth, health, models, documents, workspaces, chat sessions, eval, research)

## 2. Preserved Backend Contracts (Read-Only)
All backend endpoints and payloads remain strictly untouched:
- `POST /api/chat/stream` (SSE events: `status` with stages `rewriting`, `retrieving`, `reranking`, `generating`; `retrieval` with `citations` & `trace`; `token`; `done`)
- `GET/POST/PATCH/DELETE /api/chat/sessions` & `/api/chat/{id}/feedback`
- `GET/POST/PATCH/DELETE /api/documents`, `/api/documents/upload`, `/api/documents/{id}/preview`, `/api/documents/{id}/raw`, `/api/documents/{id}/reindex`
- `GET /api/health`, `/api/models`, `/api/workspaces`, `/api/research/*`

## 3. ChatGPT UI Transformation Plan
1. **Color Palette**: Neutral dark ChatGPT palette (`#212121` main, `#171717` sidebar, `#303030` composer, `#2A2A2A` secondary, `#3A3A3A` borders, `#ECECEC` primary text, `#A1A1A1` secondary text, `#F0F0F0`/`#171717` primary button). Remove yellow-heavy branding.
2. **Sidebar**: Date-grouped recent conversations (`Today`, `Yesterday`, `Previous 7 Days`, `Older`), three-dot menu (rename/delete), compact navigation, fixed bottom user/model/settings bar.
3. **Conversation Area**: Centered 800px column, right-aligned subtle dark-gray user bubbles, cardless natural AI prose, modular `CodeBlock`, `CitationChip`, `ThinkingIndicator`, `RetrievalStatus`.
4. **Composer & Welcome**: Centered `"What can I help you understand?"` welcome with 4 compact prompts; floating rounded `#303030` composer with disclaimer footer.
5. **Library, Studio, & Modals**: Consistent neutral dark theme, compact rows, responsive drawers.

## 4. Implemented Modular Components
- `Sidebar.jsx` & `ConversationList.jsx`
- `ChatHeader.jsx`, `ChatContainer.jsx`, `UserMessage.jsx`, `AssistantMessage.jsx`
- `MarkdownRenderer.jsx`, `CodeBlock.jsx`, `CitationChip.jsx`
- `ThinkingIndicator.jsx`, `RetrievalStatus.jsx`
- `ChatComposer.jsx`, `ModelSelector.jsx`, `WelcomeScreen.jsx`
- `ContextualResearchPanel.jsx`, `DocumentLibrary.jsx`, `ResearchStudio.jsx`, `SavedNotes.jsx`

