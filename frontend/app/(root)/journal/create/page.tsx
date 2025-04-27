"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function CreateJournalEntry() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState(5);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Send data to backend API
    await fetch("/api/journal", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ entry, mood }),
    });

    // After submitting, maybe redirect somewhere
    router.push("/journal");
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md">
      <h1 className="text-2xl font-bold mb-6 text-center">Create a Journal Entry</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <textarea
          className="border rounded-lg p-3 resize-none h-40"
          placeholder="Write your journal entry..."
          value={entry}
          onChange={(e) => setEntry(e.target.value)}
          required
        />

        <div>
          <label className="block mb-2 font-medium">Mood (1-10)</label>
          <input
            type="range"
            min="1"
            max="10"
            value={mood}
            onChange={(e) => setMood(Number(e.target.value))}
            className="w-full"
          />
          <div className="text-center mt-2">Mood: {mood}</div>
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Save Entry
        </button>
      </form>
    </div>
  );
}
