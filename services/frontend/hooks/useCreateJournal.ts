import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { createJournal } from "@/actions/journals";
import { moodToInt } from "@/utils/moodMapping";

export function useCreateJournal() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState("neutral");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

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

    setError(null);

    startTransition(async () => {
      try {
        const result = await createJournal({
          journalText: entry,
          moodScore: moodToInt(mood),
        });

        if (result.success) {
          setSuccess(true);
          setTimeout(() => {
            router.push("/journal/home");
          }, 2000);
        } else {
          setError(result.error || "Something went wrong. Please try again.");
        }
      } catch (err) {
        console.error("Failed to submit journal entry:", err);
        setError("Something went wrong. Please try again.");
      }
    });
  };

  return {
    entry,
    setEntry,
    mood,
    setMood,
    isSubmitting: isPending,
    success,
    error,
    handleSubmit,
    resetForm,
  };
}
