import { useState } from "react";
import { useRouter } from "next/navigation";
import { createJournalEntry } from "@/lib/api/journals";
import { moodToInt } from "@/utils/moodMapping"; // ← Add this import

export function useCreateJournal() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState("neutral");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

  const resetForm = () => {
    setEntry("");
    setMood("neutral");
    setSuccess(false);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!entry.trim()) {
      setError("Please write something in your journal entry.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // ✅ Convert mood string to integer before sending
      await createJournalEntry({
        entry,
        mood: moodToInt(mood), // ← Changed this line
      });
      setSuccess(true);

      setTimeout(() => {
        router.push("/journal/home");
      }, 2000);
    } catch (error) {
      console.error("Failed to submit journal entry:", error);
      setError("Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    entry,
    setEntry,
    mood,
    setMood,
    isSubmitting,
    success,
    error,
    handleSubmit,
    resetForm,
  };
}
