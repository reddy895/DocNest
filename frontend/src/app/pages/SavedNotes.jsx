import React, { useEffect, useMemo, useState } from 'react';
import { Bookmark, Search, Trash2, Copy, Check, RefreshCw, BookOpen, AlertCircle } from 'lucide-react';
import { fetchResearchNotes, deleteResearchNote } from '../../services/api';
import { useToast } from '../../components/ui/ToastProvider';
import Spinner from '../../components/ui/Spinner';
import Badge from '../../components/ui/Badge';

function formatDate(value) {
  if (!value) return 'Unknown date';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown date';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function SavedNotes({ onOpenResearchStudio }) {
  const [notes, setNotes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const { showToast } = useToast();

  const loadNotes = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await fetchResearchNotes();
      setNotes(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Could not load saved notes.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadNotes();
  }, []);

  const filteredNotes = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return notes;
    return notes.filter((note) => {
      const haystack = [note.title, note.content, ...(note.tags || [])].join(' ').toLowerCase();
      return haystack.includes(search);
    });
  }, [notes, query]);

  const handleCopy = async (note) => {
    try {
      await navigator.clipboard.writeText(`${note.title}\n\n${note.content}`);
      setCopiedId(note.id);
      setTimeout(() => setCopiedId(null), 1800);
    } catch {
      showToast('Could not copy note to clipboard.', 'error');
    }
  };

  const handleDelete = async (noteId) => {
    setDeletingId(noteId);
    try {
      await deleteResearchNote(noteId);
      setNotes((prev) => prev.filter((note) => note.id !== noteId));
      showToast('Note deleted.', 'success');
    } catch (err) {
      showToast(err.message || 'Could not delete note.', 'error');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-border px-4 py-4 md:flex-row md:items-center md:justify-between md:px-6">
        <div>
          <div className="flex items-center gap-2">
            <Bookmark className="h-4 w-4 text-brand" />
            <h1 className="text-lg font-semibold tracking-tight">Saved Notes</h1>
            <Badge variant="neutral">{notes.length}</Badge>
          </div>
          <p className="mt-0.5 text-xs text-muted-dim">
            Research notes captured from conversations and the Research Studio.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-dim" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search notes..."
              className="dn-input w-full py-2 pl-8 pr-3 text-xs md:w-56"
              aria-label="Search saved notes"
            />
          </div>
          <button
            type="button"
            onClick={onOpenResearchStudio}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-2 text-xs font-bold text-brand-foreground transition-colors hover:bg-brand-hover"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Research Studio</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 md:px-6">
        {isLoading ? (
          <div className="flex h-40 items-center justify-center gap-2 text-sm text-muted">
            <Spinner /> Loading notes...
          </div>
        ) : error ? (
          <div className="mx-auto max-w-md rounded-xl border border-rose-500/30 bg-rose-500/5 p-5 text-center">
            <AlertCircle className="mx-auto mb-2 h-5 w-5 text-rose-300" />
            <p className="text-sm text-foreground">Could not load saved notes</p>
            <p className="mt-1 text-xs text-muted">{error}</p>
            <button
              type="button"
              onClick={loadNotes}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-surface"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="mx-auto flex max-w-md flex-col items-center justify-center py-16 text-center">
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl border border-brand/20 bg-brand/10 text-brand">
              <Bookmark className="h-5 w-5" />
            </div>
            <h2 className="text-sm font-semibold text-foreground">
              {notes.length === 0 ? 'No saved notes yet' : 'No matching notes'}
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-muted-dim">
              {notes.length === 0
                ? 'Save an assistant response from a conversation, or generate research in the Research Studio.'
                : 'Try a different search term.'}
            </p>
          </div>
        ) : (
          <div className="mx-auto grid max-w-4xl grid-cols-1 gap-3 lg:grid-cols-2">
            {filteredNotes.map((note) => (
              <article
                key={note.id}
                className="group flex flex-col rounded-xl border border-border bg-surface-raised p-4 transition-colors hover:border-border/80"
              >
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-sm font-semibold text-foreground">{note.title}</h2>
                  <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
                    <button
                      type="button"
                      onClick={() => handleCopy(note)}
                      className="rounded p-1 text-muted-dim hover:bg-surface hover:text-foreground"
                      aria-label="Copy note"
                    >
                      {copiedId === note.id ? (
                        <Check className="h-3.5 w-3.5 text-emerald-300" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(note.id)}
                      disabled={deletingId === note.id}
                      className="rounded p-1 text-muted-dim hover:bg-rose-500/10 hover:text-rose-300 disabled:opacity-40"
                      aria-label="Delete note"
                    >
                      {deletingId === note.id ? <Spinner size={14} /> : <Trash2 className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>
                <p className="mt-2 line-clamp-4 whitespace-pre-wrap text-xs leading-relaxed text-muted">
                  {note.content}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-border/60 pt-2.5">
                  {(note.tags || []).slice(0, 3).map((tag) => (
                    <Badge key={tag} variant="neutral">
                      {tag}
                    </Badge>
                  ))}
                  <span className="ml-auto font-mono text-[10px] text-muted-dim">
                    {formatDate(note.updated_at || note.created_at)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
