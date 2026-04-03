"use client";

import { useCreateJournal } from "@/hooks/useCreateJournal";
import { CreateJournalForm } from "@/components/journal/CreateJournalForm";
import { WritingPromptBox } from "@/components/journal/WritingPromptBox";
import { SuccessMessage } from "@/components/journal/SuccessMessage";

export default function CreateJournalPage() {
  const {
    entry,
    setEntry,
    mood,
    setMood,
    isSubmitting,
    success,
    error,
    handleSubmit,
  } = useCreateJournal();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="heading-1">New Entry</h1>
      </div>

      {success ? (
        <SuccessMessage />
      ) : (
        <div className="space-y-6">
          <WritingPromptBox
            onInsert={(text) => {
              setEntry((prev) => (prev.trim() ? `${prev}\n\n${text}` : text));
            }}
          />
          <CreateJournalForm
            entry={entry}
            setEntry={setEntry}
            mood={mood}
            setMood={setMood}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            error={error}
          />
        </div>
      )}
    </div>
  );
}
