"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Textarea from "@/components/Textarea";
import MoodSlider from "@/components/MoodSlider";

export default function CreateJournalEntry() {
  const [entry, setEntry] = useState("");
  const [mood, setMood] = useState(5);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Hardcoded UUID for now
    const userId = "123e4567-e89b-12d3-a456-426614174000"; // Example UUID

    // Send data to backend API
    await fetch("http://localhost:8080/v1/journals", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ entry, mood, userId }), // Include hardcoded userId
    });

    // After submitting, maybe redirect somewhere
    router.push("/journal");
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-md">
      <h1 className="text-2xl font-bold mb-6 text-center">Create a Journal Entry</h1>
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
    </div>
  );
}
