"use client";

import { useState } from "react";
import Textarea from "@/components/Textarea";
import MoodSlider from "@/components/MoodSlider";

export default function CreateJournalEntry() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState(5);
  const [success, setSuccess] = useState(false); // <--- NEW success state

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const userId = "123e4567-e89b-12d3-a456-426614174000"; // Example UUID

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

      setSuccess(true); // Set success to true if everything went well
      setEntry(""); // Clear the form
      setMood(5);   // Reset mood slider if you want

    } catch (error) {
      console.error("Failed to submit journal entry:", error);
      alert("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md">
      <h1 className="text-2xl font-bold mb-6 text-center">Create a Journal Entry</h1>

      {success ? (
        <div className="text-green-600 text-center font-semibold">
          🎉 Thank you for submitting your journal entry!
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Textarea value={entry} onChange={(e) => setEntry(e.target.value)} />
          <MoodSlider value={mood} onChange={(e) => setMood(Number(e.target.value))} />
          <button
            type="submit"
            className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Save Entry
          </button>
        </form>
      )}
    </div>
  );
}
