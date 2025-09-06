"use client";

import { useCreateJournal } from '@/hooks/useCreateJournal';
import { JournalHeader } from '@/components/journal/JournalHeader';
import { CreateJournalForm } from '@/components/journal/CreateJournalForm';
import { SuccessMessage } from '@/components/journal/SuccessMessage';

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
      <JournalHeader totalEntries={0} />

      {success ? (
        <SuccessMessage />
      ) : (
        <CreateJournalForm
          entry={entry}
          setEntry={setEntry}
          mood={mood}
          setMood={setMood}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          error={error}
        />
      )}
    </div>
  );
}
