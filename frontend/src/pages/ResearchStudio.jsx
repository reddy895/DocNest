import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  FileText,
  Sparkles,
  GitCompare,
  HelpCircle,
  Layers,
  Bookmark,
  Download,
  Copy,
  Check,
  Plus,
  Trash2,
  Edit2,
  RefreshCw,
  Loader2,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Search,
  Tag,
} from 'lucide-react';
import MarkdownRenderer from '../components/MarkdownRenderer';
import {
  summarizeResearch,
  compareDocuments,
  generateResearchQuiz,
  generateResearchFlashcards,
  fetchResearchNotes,
  createResearchNote,
  deleteResearchNote,
} from '../services/api';

export default function ResearchStudio({ documents = [], onOpenViewer = () => {} }) {
  const [activeTab, setActiveTab] = useState('summarize'); // summarize | compare | quiz | flashcards | notes

  // Summarize state
  const [summaryType, setSummaryType] = useState('executive');
  const [summaryDocIds, setSummaryDocIds] = useState([]);
  const [summaryResult, setSummaryResult] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryCopied, setSummaryCopied] = useState(false);

  // Compare state
  const [compareDocIds, setCompareDocIds] = useState([]);
  const [compareResult, setCompareResult] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Quiz state
  const [quizDocIds, setQuizDocIds] = useState([]);
  const [quizDifficulty, setQuizDifficulty] = useState('medium');
  const [quizCount, setQuizCount] = useState(4);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizLoading, setQuizLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState({});

  // Flashcards state
  const [fcDocIds, setFcDocIds] = useState([]);
  const [fcCount, setFcCount] = useState(6);
  const [flashcards, setFlashcards] = useState([]);
  const [fcCurrentIdx, setFcCurrentIdx] = useState(0);
  const [fcFlipped, setFcFlipped] = useState(false);
  const [fcLoading, setFcLoading] = useState(false);

  // Notes state
  const [notes, setNotes] = useState([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState('');
  const [newNoteContent, setNewNoteContent] = useState('');
  const [newNoteTags, setNewNoteTags] = useState('');
  const [isCreatingNote, setIsCreatingNote] = useState(false);
  const [notesSearch, setNotesSearch] = useState('');

  // Auto-select first two docs for compare if available
  useEffect(() => {
    if (documents.length >= 2 && compareDocIds.length === 0) {
      const d0 = documents[0].doc_id || documents[0].id;
      const d1 = documents[1].doc_id || documents[1].id;
      setCompareDocIds([d0, d1]);
    }
  }, [documents]);

  // Load notes when notes tab opens
  useEffect(() => {
    if (activeTab === 'notes') {
      loadNotes();
    }
  }, [activeTab]);

  const loadNotes = async () => {
    setNotesLoading(true);
    try {
      const data = await fetchResearchNotes();
      setNotes(data || []);
    } catch (e) {
      console.warn('Could not load notes:', e);
    } finally {
      setNotesLoading(false);
    }
  };

  // Run Summarize
  const handleSummarize = async () => {
    setSummaryLoading(true);
    try {
      const res = await summarizeResearch({
        doc_ids: summaryDocIds.length > 0 ? summaryDocIds : null,
        summary_type: summaryType,
      });
      setSummaryResult(res);
    } catch (e) {
      alert(`Summarization failed: ${e.message}`);
    } finally {
      setSummaryLoading(false);
    }
  };

  // Run Compare
  const handleCompare = async () => {
    if (compareDocIds.length < 2) {
      alert('Please select at least two documents to compare.');
      return;
    }
    setCompareLoading(true);
    try {
      const res = await compareDocuments({ doc_ids: compareDocIds });
      setCompareResult(res);
    } catch (e) {
      alert(`Comparison failed: ${e.message}`);
    } finally {
      setCompareLoading(false);
    }
  };

  // Run Quiz Generator
  const handleGenerateQuiz = async () => {
    setQuizLoading(true);
    setSelectedAnswers({});
    try {
      const res = await generateResearchQuiz({
        doc_ids: quizDocIds.length > 0 ? quizDocIds : null,
        question_count: quizCount,
        difficulty: quizDifficulty,
      });
      setQuizQuestions(res.quiz || []);
    } catch (e) {
      alert(`Quiz generation failed: ${e.message}`);
    } finally {
      setQuizLoading(false);
    }
  };

  // Run Flashcard Generator
  const handleGenerateFlashcards = async () => {
    setFcLoading(true);
    setFcCurrentIdx(0);
    setFcFlipped(false);
    try {
      const res = await generateResearchFlashcards({
        doc_ids: fcDocIds.length > 0 ? fcDocIds : null,
        card_count: fcCount,
      });
      setFlashcards(res.flashcards || []);
    } catch (e) {
      alert(`Flashcards generation failed: ${e.message}`);
    } finally {
      setFcLoading(false);
    }
  };

  // Create Note
  const handleCreateNote = async (e) => {
    e.preventDefault();
    if (!newNoteTitle.trim() || !newNoteContent.trim()) return;

    const tagsList = newNoteTags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    try {
      await createResearchNote({
        title: newNoteTitle.trim(),
        content: newNoteContent.trim(),
        tags: tagsList,
      });
      setNewNoteTitle('');
      setNewNoteContent('');
      setNewNoteTags('');
      setIsCreatingNote(false);
      loadNotes();
    } catch (err) {
      alert(`Failed to save note: ${err.message}`);
    }
  };

  // Delete Note
  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Delete this research note permanently?')) return;
    try {
      await deleteResearchNote(noteId);
      setNotes((prev) => prev.filter((n) => n.id !== noteId));
    } catch (err) {
      alert(`Failed to delete note: ${err.message}`);
    }
  };

  // Save summary directly as note
  const handleSaveSummaryAsNote = async () => {
    if (!summaryResult) return;
    try {
      await createResearchNote({
        title: `${summaryType.toUpperCase()} Summary — ${new Date().toLocaleDateString()}`,
        content: summaryResult.content,
        tags: ['summary', summaryType],
      });
      alert('Summary saved to Research Notes binder!');
    } catch (e) {
      alert(`Could not save note: ${e.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-[#F5C542]/10 text-[#F5C542] border border-[#F5C542]/30 rounded-lg">
              <Sparkles className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-[#F0F2F5] tracking-tight">
              Research Studio
            </h1>
          </div>
          <p className="text-xs text-[#8E95A0] mt-1">
            NotebookLM-style grounded document synthesis: executive summaries, comparative matrices, active recall quizzes, flashcards, and notes.
          </p>
        </div>

        {/* Studio Subtabs */}
        <div className="flex items-center gap-1 bg-[#121417] border border-[#20242A] p-1 rounded-xl text-xs overflow-x-auto">
          {[
            { id: 'summarize', label: 'Summarize', icon: FileText },
            { id: 'compare', label: 'Compare Docs', icon: GitCompare },
            { id: 'quiz', label: 'Active Quizzes', icon: HelpCircle },
            { id: 'flashcards', label: 'Flashcards', icon: Layers },
            { id: 'notes', label: 'Research Notes', icon: Bookmark },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition whitespace-nowrap ${
                  active
                    ? 'bg-[#F5C542] text-[#0C0D0E] font-bold shadow-sm'
                    : 'text-[#8E95A0] hover:text-[#F0F2F5] hover:bg-[#181B1F]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ---------------- 1. SUMMARIZE VIEW ---------------- */}
      {activeTab === 'summarize' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Column */}
          <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5 space-y-5 h-fit">
            <div>
              <label className="text-xs font-semibold text-[#F0F2F5] block mb-2 font-mono">
                SUMMARY MODE
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'executive', label: 'Executive Brief' },
                  { id: 'detailed', label: 'Analytical Breakdown' },
                  { id: 'key_findings', label: 'Key Findings' },
                  { id: 'terms', label: 'Domain Glossary' },
                ].map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSummaryType(m.id)}
                    className={`p-2.5 rounded-lg border text-left text-xs transition ${
                      summaryType === m.id
                        ? 'bg-[#181B1F] border-[#F5C542] text-[#F5C542] font-bold'
                        : 'border-[#20242A] text-[#8E95A0] hover:text-[#F0F2F5]'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#F0F2F5] block mb-2 font-mono">
                SELECT DOCUMENTS (OR ALL)
              </label>
              <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                {documents.map((d) => {
                  const did = d.doc_id || d.id;
                  const isChecked = summaryDocIds.includes(did);
                  return (
                    <label
                      key={did}
                      className="flex items-center gap-2 p-2 bg-[#181B1F] rounded-lg text-xs text-[#F0F2F5] cursor-pointer hover:border-[#20242A] border border-transparent"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) setSummaryDocIds([...summaryDocIds, did]);
                          else setSummaryDocIds(summaryDocIds.filter((id) => id !== did));
                        }}
                        className="rounded border-[#20242A] text-[#F5C542] focus:ring-0"
                      />
                      <span className="truncate">{d.filename}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            <button
              onClick={handleSummarize}
              disabled={summaryLoading}
              className="w-full py-2.5 bg-[#F5C542] hover:bg-[#FFD358] disabled:opacity-40 text-[#0C0D0E] font-bold text-xs rounded-lg flex items-center justify-center gap-2 transition shadow-sm"
            >
              {summaryLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Synthesizing with Llama 3.2...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Grounded Summary</span>
                </>
              )}
            </button>
          </div>

          {/* Results Column */}
          <div className="lg:col-span-2 bg-[#121417] border border-[#20242A] rounded-xl p-6 min-h-[420px] flex flex-col justify-between">
            {summaryResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#20242A]">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-[#181B1F] text-[#F5C542] border border-[#20242A] rounded text-[11px] font-mono uppercase">
                      {summaryResult.summary_type}
                    </span>
                    <span className="text-[11px] text-[#8E95A0] font-mono">
                      {summaryResult.sources_used} sources • {summaryResult.processing_time_seconds}s
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(summaryResult.content);
                        setSummaryCopied(true);
                        setTimeout(() => setSummaryCopied(false), 2000);
                      }}
                      className="p-1.5 text-[#8E95A0] hover:text-[#F0F2F5] rounded hover:bg-[#181B1F] transition"
                      title="Copy Summary"
                    >
                      {summaryCopied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={handleSaveSummaryAsNote}
                      className="flex items-center gap-1 px-2.5 py-1 bg-[#181B1F] hover:bg-[#20242A] border border-[#20242A] text-[11px] text-[#F0F2F5] rounded-lg transition"
                    >
                      <Bookmark className="w-3 h-3 text-[#F5C542]" />
                      <span>Save as Note</span>
                    </button>
                  </div>
                </div>

                <div className="prose prose-invert max-w-none text-sm leading-relaxed">
                  <MarkdownRenderer content={summaryResult.content} />
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#8E95A0]">
                <FileText className="w-12 h-12 opacity-30 mb-3" />
                <h3 className="text-sm font-semibold text-[#F0F2F5]">No Summary Generated Yet</h3>
                <p className="text-xs text-[#8E95A0] max-w-sm mt-1">
                  Select your desired summary mode and documents on the left, then click Generate to synthesize a fully cited briefing.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------- 2. COMPARE VIEW ---------------- */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-[#F0F2F5]">
                  Select 2 or More Documents to Compare
                </h3>
                <p className="text-xs text-[#8E95A0]">
                  Analyze points of convergence, technical divergence, and generate a side-by-side comparison table.
                </p>
              </div>
              <button
                onClick={handleCompare}
                disabled={compareLoading || compareDocIds.length < 2}
                className="px-4 py-2 bg-[#F5C542] hover:bg-[#FFD358] disabled:opacity-40 text-[#0C0D0E] font-bold text-xs rounded-lg flex items-center gap-2 transition"
              >
                {compareLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
                <span>Execute Comparative Analysis</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {documents.map((d) => {
                const did = d.doc_id || d.id;
                const isSelected = compareDocIds.includes(did);
                return (
                  <button
                    key={did}
                    onClick={() => {
                      if (isSelected) setCompareDocIds(compareDocIds.filter((id) => id !== did));
                      else setCompareDocIds([...compareDocIds, did]);
                    }}
                    className={`p-3 rounded-lg border text-left text-xs transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#181B1F] border-[#F5C542] text-[#F0F2F5]'
                        : 'border-[#20242A] text-[#8E95A0] hover:text-[#F0F2F5]'
                    }`}
                  >
                    <span className="truncate">{d.filename}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-[#F5C542] shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>

          {compareResult && (
            <div className="space-y-4">
              {/* Overview & Synthesis */}
              <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5">
                <h4 className="text-xs font-mono font-bold text-[#F5C542] uppercase mb-2">
                  SYNTHESIS OVERVIEW
                </h4>
                <p className="text-xs text-[#F0F2F5] leading-relaxed">
                  {compareResult.overview}
                </p>
              </div>

              {/* Agreements vs Contradictions Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#121417] border border-emerald-500/30 rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Points of Agreement & Consensus</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-[#F0F2F5]">
                    {(compareResult.agreements || []).map((ag, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{ag}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-[#121417] border border-rose-500/30 rounded-xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                    <AlertCircle className="w-4 h-4" />
                    <span>Divergences & Contradictions</span>
                  </div>
                  <ul className="space-y-1.5 text-xs text-[#F0F2F5]">
                    {(compareResult.contradictions || []).length > 0 ? (
                      compareResult.contradictions.map((ct, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-rose-400 font-bold">•</span>
                          <span>{ct}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-[#8E95A0] italic">No direct factual contradictions detected.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* Markdown Matrix */}
              {compareResult.matrix && (
                <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-mono font-bold text-[#F0F2F5] uppercase">
                    COMPARISON MATRIX
                  </h4>
                  <div className="prose prose-invert max-w-none text-xs overflow-x-auto">
                    <MarkdownRenderer content={compareResult.matrix} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ---------------- 3. QUIZ VIEW ---------------- */}
      {activeTab === 'quiz' && (
        <div className="space-y-6">
          <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-[#F0F2F5]">
                Active Recall Document Quiz
              </h3>
              <p className="text-xs text-[#8E95A0]">
                Generate multiple-choice verification questions with grounded explanations.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={quizDifficulty}
                onChange={(e) => setQuizDifficulty(e.target.value)}
                className="bg-[#181B1F] border border-[#20242A] rounded-lg px-2.5 py-1.5 text-xs text-[#F0F2F5] focus:border-[#F5C542] focus:outline-none"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>

              <button
                onClick={handleGenerateQuiz}
                disabled={quizLoading}
                className="px-4 py-2 bg-[#F5C542] hover:bg-[#FFD358] disabled:opacity-40 text-[#0C0D0E] font-bold text-xs rounded-lg flex items-center gap-1.5 transition"
              >
                {quizLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HelpCircle className="w-4 h-4" />}
                <span>Generate Quiz</span>
              </button>
            </div>
          </div>

          {quizQuestions.length > 0 ? (
            <div className="space-y-4">
              {quizQuestions.map((q, qIdx) => {
                const userChoice = selectedAnswers[q.id];
                const isAnswered = !!userChoice;

                return (
                  <div
                    key={q.id || qIdx}
                    className="bg-[#121417] border border-[#20242A] rounded-xl p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono text-[#F5C542]">QUESTION {qIdx + 1}</span>
                      {q.citation && (
                        <span className="text-[10px] font-mono text-[#8E95A0] bg-[#181B1F] px-2 py-0.5 rounded">
                          {q.citation}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-[#F0F2F5]">{q.question}</p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {q.options.map((opt, oIdx) => {
                        const isCorrect = opt === q.correct_answer;
                        const isSelected = userChoice === opt;

                        let btnStyle = 'bg-[#181B1F] border-[#20242A] text-[#F0F2F5] hover:border-[#F5C542]';
                        if (isAnswered) {
                          if (isCorrect) {
                            btnStyle = 'bg-emerald-950/40 border-emerald-500 text-emerald-300 font-bold';
                          } else if (isSelected && !isCorrect) {
                            btnStyle = 'bg-rose-950/40 border-rose-500 text-rose-300';
                          } else {
                            btnStyle = 'bg-[#181B1F]/40 border-[#20242A]/40 text-[#8E95A0]/40';
                          }
                        }

                        return (
                          <button
                            key={oIdx}
                            disabled={isAnswered}
                            onClick={() => setSelectedAnswers({ ...selectedAnswers, [q.id]: opt })}
                            className={`p-3 rounded-lg border text-left text-xs transition flex items-center justify-between ${btnStyle}`}
                          >
                            <span>{opt}</span>
                            {isAnswered && isCorrect && <Check className="w-4 h-4 text-emerald-400 shrink-0" />}
                          </button>
                        );
                      })}
                    </div>

                    {isAnswered && (
                      <div className="p-3 bg-[#181B1F] border border-[#20242A] rounded-lg text-xs space-y-1 animate-fade-in">
                        <span className="font-semibold text-[#F5C542]">Explanation:</span>
                        <p className="text-[#8E95A0] leading-relaxed">{q.explanation}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-[#121417] border border-[#20242A] rounded-xl p-12 text-center text-[#8E95A0]">
              <HelpCircle className="w-10 h-10 opacity-30 mx-auto mb-2" />
              <p className="text-xs">Click Generate Quiz to create active recall test questions.</p>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 4. FLASHCARDS VIEW ---------------- */}
      {activeTab === 'flashcards' && (
        <div className="space-y-6">
          <div className="bg-[#121417] border border-[#20242A] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-[#F0F2F5]">
                Interactive Concept Flashcards
              </h3>
              <p className="text-xs text-[#8E95A0]">
                Master core definitions, key metrics, and architectures with 2-sided study cards.
              </p>
            </div>

            <button
              onClick={handleGenerateFlashcards}
              disabled={fcLoading}
              className="px-4 py-2 bg-[#F5C542] hover:bg-[#FFD358] disabled:opacity-40 text-[#0C0D0E] font-bold text-xs rounded-lg flex items-center gap-1.5 transition"
            >
              {fcLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
              <span>Generate Flashcards</span>
            </button>
          </div>

          {flashcards.length > 0 ? (
            <div className="max-w-xl mx-auto space-y-4">
              {/* Card Container */}
              <div
                onClick={() => setFcFlipped(!fcFlipped)}
                className="bg-[#121417] border-2 border-[#20242A] hover:border-[#F5C542] rounded-2xl p-8 min-h-[260px] flex flex-col justify-between cursor-pointer transition shadow-xl text-center select-none"
              >
                <div className="flex items-center justify-between text-[11px] text-[#8E95A0] font-mono">
                  <span className="px-2 py-0.5 bg-[#181B1F] rounded text-[#F5C542]">
                    {flashcards[fcCurrentIdx]?.category || 'Key Concept'}
                  </span>
                  <span>CARD {fcCurrentIdx + 1} OF {flashcards.length}</span>
                </div>

                <div className="py-6 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#8E95A0]">
                    {fcFlipped ? 'ANSWER / DEFINITION' : 'PROMPT / CONCEPT'}
                  </span>
                  <p className="text-base md:text-lg font-semibold text-[#F0F2F5] leading-relaxed">
                    {fcFlipped ? flashcards[fcCurrentIdx]?.back : flashcards[fcCurrentIdx]?.front}
                  </p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#8E95A0]">
                  <span className="font-mono text-[10px]">
                    {flashcards[fcCurrentIdx]?.citation || ''}
                  </span>
                  <span className="text-[#F5C542] text-xs">Click to Flip ↺</span>
                </div>
              </div>

              {/* Navigation Controls */}
              <div className="flex items-center justify-center gap-4 pt-2">
                <button
                  disabled={fcCurrentIdx === 0}
                  onClick={() => {
                    setFcFlipped(false);
                    setFcCurrentIdx(fcCurrentIdx - 1);
                  }}
                  className="p-2 bg-[#121417] border border-[#20242A] rounded-xl text-[#F0F2F5] disabled:opacity-30 hover:border-[#F5C542] transition"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <span className="text-xs font-mono text-[#8E95A0]">
                  {fcCurrentIdx + 1} / {flashcards.length}
                </span>
                <button
                  disabled={fcCurrentIdx === flashcards.length - 1}
                  onClick={() => {
                    setFcFlipped(false);
                    setFcCurrentIdx(fcCurrentIdx + 1);
                  }}
                  className="p-2 bg-[#121417] border border-[#20242A] rounded-xl text-[#F0F2F5] disabled:opacity-30 hover:border-[#F5C542] transition"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-[#121417] border border-[#20242A] rounded-xl p-12 text-center text-[#8E95A0]">
              <Layers className="w-10 h-10 opacity-30 mx-auto mb-2" />
              <p className="text-xs">Click Generate Flashcards to build interactive 2-sided cards.</p>
            </div>
          )}
        </div>
      )}

      {/* ---------------- 5. NOTES VIEW ---------------- */}
      {activeTab === 'notes' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative">
              <Search className="w-4 h-4 text-[#8E95A0] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search research notes..."
                value={notesSearch}
                onChange={(e) => setNotesSearch(e.target.value)}
                className="pl-9 pr-3 py-1.5 text-xs w-64 bg-[#121417] border border-[#20242A] rounded-lg text-[#F0F2F5] focus:border-[#F5C542] focus:outline-none"
              />
            </div>

            <button
              onClick={() => setIsCreatingNote(!isCreatingNote)}
              className="px-3.5 py-1.5 bg-[#F5C542] hover:bg-[#FFD358] text-[#0C0D0E] font-bold text-xs rounded-lg flex items-center gap-1.5 transition shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>{isCreatingNote ? 'Close Form' : 'New Research Note'}</span>
            </button>
          </div>

          {/* Create Note Form */}
          {isCreatingNote && (
            <form
              onSubmit={handleCreateNote}
              className="bg-[#121417] border border-[#F5C542]/40 rounded-xl p-5 space-y-3 animate-fade-in"
            >
              <h4 className="text-xs font-mono font-bold text-[#F5C542] uppercase">
                CREATE RESEARCH NOTE
              </h4>
              <input
                type="text"
                placeholder="Note Title (e.g. RAG Embedding Tradeoffs)"
                value={newNoteTitle}
                onChange={(e) => setNewNoteTitle(e.target.value)}
                required
                className="w-full bg-[#181B1F] border border-[#20242A] rounded-lg px-3 py-2 text-xs text-[#F0F2F5] focus:border-[#F5C542] focus:outline-none"
              />
              <textarea
                placeholder="Write your research notes, findings, and Markdown thoughts here..."
                rows={5}
                value={newNoteContent}
                onChange={(e) => setNewNoteContent(e.target.value)}
                required
                className="w-full bg-[#181B1F] border border-[#20242A] rounded-lg p-3 text-xs text-[#F0F2F5] focus:border-[#F5C542] focus:outline-none"
              />
              <input
                type="text"
                placeholder="Tags (comma separated, e.g. rag, nomic, reranker)"
                value={newNoteTags}
                onChange={(e) => setNewNoteTags(e.target.value)}
                className="w-full bg-[#181B1F] border border-[#20242A] rounded-lg px-3 py-2 text-xs text-[#F0F2F5] focus:border-[#F5C542] focus:outline-none"
              />
              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setIsCreatingNote(false)}
                  className="px-3 py-1.5 text-xs text-[#8E95A0] hover:text-[#F0F2F5]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#F5C542] hover:bg-[#FFD358] text-[#0C0D0E] font-bold text-xs rounded-lg transition"
                >
                  Save Note
                </button>
              </div>
            </form>
          )}

          {/* Notes Grid */}
          {notes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {notes
                .filter((n) => n.title.toLowerCase().includes(notesSearch.toLowerCase()) || n.content.toLowerCase().includes(notesSearch.toLowerCase()))
                .map((note) => (
                  <div
                    key={note.id}
                    className="bg-[#121417] border border-[#20242A] hover:border-[#F5C542]/50 rounded-xl p-5 flex flex-col justify-between space-y-3 transition"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="text-sm font-semibold text-[#F0F2F5] line-clamp-1">
                          {note.title}
                        </h4>
                        <div className="flex items-center gap-1">
                          <a
                            href={`/api/research/notes/${note.id}/export`}
                            download
                            className="p-1 text-[#8E95A0] hover:text-[#F5C542] rounded transition"
                            title="Export as Markdown (.md)"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                          <button
                            onClick={() => handleDeleteNote(note.id)}
                            className="p-1 text-[#8E95A0] hover:text-rose-400 rounded transition"
                            title="Delete Note"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      <p className="text-xs text-[#8E95A0] line-clamp-4 leading-relaxed whitespace-pre-wrap">
                        {note.content}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-[#20242A]/50 flex items-center justify-between text-[10px] text-[#8E95A0] font-mono">
                      <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                      {note.tags && note.tags.length > 0 && (
                        <span className="text-[#F5C542]">#{note.tags[0]}</span>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="bg-[#121417] border border-[#20242A] rounded-xl p-12 text-center text-[#8E95A0]">
              <Bookmark className="w-10 h-10 opacity-30 mx-auto mb-2" />
              <p className="text-xs">No research notes created yet. Click New Research Note to start documenting your findings.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
