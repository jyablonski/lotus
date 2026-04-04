"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { deleteJournal, updateJournal } from "@/actions/journals";
import { JournalEntry } from "@/types/journal";
import { CreateJournalForm } from "./CreateJournalForm";
import { getMoodConfigByInt } from "@/lib/utils/moodMapping";
import { formatEntryDate } from "@/lib/utils/datetime";
import { ROUTES } from "@/lib/routes";
import { Card } from "@/components/ui/Card";

type JournalEntryDetailClientProps = {
  entry: JournalEntry;
  timezone: string;
};

export function JournalEntryDetailClient({
  entry,
  timezone,
}: JournalEntryDetailClientProps) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(entry.journalText);
  const [mood, setMood] = useState(entry.userMood);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!editing) {
      setText(entry.journalText);
      setMood(entry.userMood);
    }
  }, [entry.journalText, entry.userMood, editing]);

  const moodConfig = getMoodConfigByInt(entry.userMood);
  const formattedDate = formatEntryDate(entry.createdAt, timezone);

  const handleCancelEdit = () => {
    setEditing(false);
    setText(entry.journalText);
    setMood(entry.userMood);
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const result = await updateJournal(entry.journalId, {
        journalText: text,
        moodScore: mood,
      });
      if (result.success) {
        setEditing(false);
        router.refresh();
      } else {
        setError(result.error ?? "Update failed");
      }
    });
  };

  const handleDelete = () => {
    setError(null);
    startTransition(async () => {
      const result = await deleteJournal(entry.journalId);
      if (result.success) {
        router.replace(ROUTES.journal.home);
      } else {
        setError(result.error ?? "Delete failed");
        setDeleteConfirm(false);
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <Link
          href={ROUTES.journal.home}
          className="text-sm text-dark-400 hover:text-lotus-400 transition-colors"
        >
          ← Back to journal
        </Link>
      </div>

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="heading-1">Journal entry</h1>
          <p className="text-sm text-dark-400 mt-1">{formattedDate}</p>
        </div>
        {!editing && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="btn-outline px-4 py-2 text-sm"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                setDeleteConfirm(true);
              }}
              className="px-4 py-2 text-sm rounded-lg border border-red-500/40 text-red-300 hover:bg-red-500/10 transition-colors"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {deleteConfirm && (
        <div className="mb-6 p-4 rounded-lg border border-red-500/30 bg-red-950/20">
          {error && (
            <p className="text-sm text-red-300 mb-3" role="alert">
              {error}
            </p>
          )}
          <p className="text-dark-200 text-sm mb-4">
            Delete this entry permanently? This cannot be undone.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setDeleteConfirm(false);
                setError(null);
              }}
              className="btn-outline px-4 py-2 text-sm"
              disabled={isPending}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={isPending}
              className="px-4 py-2 text-sm rounded-lg bg-red-600 hover:bg-red-500 text-white disabled:opacity-50"
            >
              {isPending ? "Deleting…" : "Delete entry"}
            </button>
          </div>
        </div>
      )}

      {editing ? (
        <CreateJournalForm
          entry={text}
          setEntry={setText}
          mood={mood}
          setMood={setMood}
          onSubmit={handleSubmit}
          isSubmitting={isPending}
          error={error}
          submitLabel="Save changes"
          showClearButton={false}
        />
      ) : (
        <Card>
          <div className="p-6 space-y-4">
            <div className="flex justify-between items-start gap-4">
              <span
                className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded-full ${moodConfig.color}`}
              >
                Mood {moodConfig.label}
              </span>
            </div>
            <div className="prose prose-sm max-w-none">
              <p className="text-dark-200 whitespace-pre-wrap leading-relaxed">
                {entry.journalText}
              </p>
            </div>
            {entry.topicNames && entry.topicNames.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2" aria-label="Topics">
                {[...new Set(entry.topicNames)].map((name) => (
                  <span
                    key={name}
                    className="inline-flex items-center rounded-md bg-dark-700 px-2.5 py-1 text-xs font-medium text-dark-200 ring-1 ring-dark-600"
                  >
                    {name.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {editing && (
        <div className="mt-4">
          <button
            type="button"
            onClick={handleCancelEdit}
            className="text-sm text-dark-400 hover:text-dark-200"
            disabled={isPending}
          >
            Cancel editing
          </button>
        </div>
      )}
    </div>
  );
}
