// components/JournalForm.tsx
import React from "react";
import Textarea from "@/components/Textarea";
import MoodSlider from "@/components/MoodSlider";

interface JournalFormProps {
    onSubmit: (e: React.FormEvent) => void;
    success: boolean;
    entry: string;
    setEntry: React.Dispatch<React.SetStateAction<string>>;
    mood: number;
    setMood: React.Dispatch<React.SetStateAction<number>>;
}

const FormCreateJournalEntry: React.FC<JournalFormProps> = ({
    onSubmit,
    success,
    entry,
    setEntry,
    mood,
    setMood,
}) => {
    return (
        <div className="max-w-xl mx-auto mt-10 p-6 bg-black rounded-2xl shadow-md">
            <h1 className="text-2xl font-bold mb-6 text-center">Create a Journal Entry</h1>

            {success ? (
                <div className="text-green-600 text-center font-semibold">
                    🎉 Thank you for submitting your journal entry!
                </div>
            ) : (
                <form onSubmit={onSubmit} className="flex flex-col gap-4">
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
};

export default FormCreateJournalEntry;
