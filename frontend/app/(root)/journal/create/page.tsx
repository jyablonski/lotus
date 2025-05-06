"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import FormCreateJournalEntry from "@/components/FormCreateJournalEntry";

export default function CreateJournalEntry() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState(5);
  const [success, setSuccess] = useState(false);
  const { data: session } = useSession();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Access the userId from the session
    const userId = session?.user?.id;

    if (!userId) {
      console.error("User ID not found in session.");
      alert("User not authenticated. Please try again.");
      return;
    }

    try {
      const response = await fetch("http://localhost:8080/v1/journals", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          journal_text: entry,
          user_mood: mood.toString(),
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${response.status} ${errorText}`);
      }

      setSuccess(true);
      setEntry("");
      setMood(5);

    } catch (error) {
      console.error("Failed to submit journal entry:", error);
      alert("Something went wrong. Please try again.");
    }
  };

  return (
    <FormCreateJournalEntry
      onSubmit={handleSubmit}
      success={success}
      entry={entry}
      setEntry={setEntry}
      mood={mood}
      setMood={setMood}
    />
  );
}