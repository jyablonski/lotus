import { useState, useTransition, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { createJournal } from "@/actions/journals";
import { moodToInt } from "@/lib/utils/moodMapping";
import { trackEvent, getTimeOfDay, countWords } from "@/lib/analytics";

export function useCreateJournal() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState("neutral");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const router = useRouter();
  const { data: session } = useSession();

  // --- Duration tracking (§4) ------------------------------------------------
  const editorOpenedAt = useRef(Date.now());

  // Track whether the entry was successfully saved (prevents abandon event
  // from firing after a successful save + redirect).
  const wasSaved = useRef(false);

  const resetForm = () => {
    setEntry("");
    setMood("neutral");
    setSuccess(false);
    setError(null);
    editorOpenedAt.current = Date.now();
    wasSaved.current = false;
  };

  // --- Abandon tracking (§3b: journal_entry_abandoned) -----------------------
  // Stable ref for the current entry text so the beforeunload handler always
  // sees the latest value without needing to re-register.
  const entryRef = useRef(entry);
  useEffect(() => {
    entryRef.current = entry;
  }, [entry]);

  const fireAbandonEvent = useCallback(() => {
    if (wasSaved.current) return;
    const text = entryRef.current;
    if (!text.trim()) return;

    const durationSeconds = Math.round(
      (Date.now() - editorOpenedAt.current) / 1000,
    );
    trackEvent("journal_entry_abandoned", {
      word_count: countWords(text),
      duration_seconds: durationSeconds,
    });
  }, []);

  useEffect(() => {
    const handleBeforeUnload = () => {
      fireAbandonEvent();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      // Also fire on unmount (e.g. client-side navigation away)
      fireAbandonEvent();
    };
  }, [fireAbandonEvent]);

  // --- Submit ----------------------------------------------------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!entry.trim()) {
      setError("Please write something in your journal entry.");
      return;
    }

    setError(null);

    // Capture pre-submit values for analytics
    const wordCount = countWords(entry);
    const durationSeconds = Math.round(
      (Date.now() - editorOpenedAt.current) / 1000,
    );
    const timeOfDay = getTimeOfDay();

    startTransition(async () => {
      try {
        const result = await createJournal({
          journalText: entry,
          moodScore: moodToInt(mood),
        });

        if (result.success) {
          wasSaved.current = true;

          // §3b: journal_entry_created
          trackEvent("journal_entry_created", {
            word_count: wordCount,
            entry_duration_seconds: durationSeconds,
            time_of_day: timeOfDay,
          });

          // §3b: first_entry_created — fires when total entries == 1
          if (result.totalCount === 1 && session?.user?.createdAt) {
            const signupDate = new Date(session.user.createdAt);
            const minutesSinceSignup = Math.floor(
              (Date.now() - signupDate.getTime()) / (1000 * 60),
            );
            trackEvent("first_entry_created", {
              minutes_since_signup: minutesSinceSignup,
            });
          }

          setSuccess(true);
          setTimeout(() => {
            router.push("/journal/home");
          }, 2000);
        } else {
          setError(result.error || "Something went wrong. Please try again.");
          trackEvent("error_encountered", {
            error_type: "save_failed",
            page: "journal_create",
          });
        }
      } catch (err) {
        console.error("Failed to submit journal entry:", err);
        setError("Something went wrong. Please try again.");
        trackEvent("error_encountered", {
          error_type: "save_failed",
          page: "journal_create",
        });
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
