import { Card, CardContent } from "@/components/ui/Card";
import { MoodSlider } from "./MoodSelector";
import { JournalTextEditor } from "./JournalTextEditor";

interface CreateJournalFormProps {
  entry: string;
  setEntry: (entry: string) => void;
  mood: number;
  setMood: (mood: number) => void;
  onSubmit: (e: React.FormEvent) => void;
  isSubmitting: boolean;
  error: string | null;
}

export function CreateJournalForm({
  entry,
  setEntry,
  mood,
  setMood,
  onSubmit,
  isSubmitting,
  error,
}: CreateJournalFormProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <form onSubmit={onSubmit} className="space-y-6">
          {/* Error Message */}
          {error && (
            <div className="alert-error">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Mood Slider (1-10) */}
          <MoodSlider value={mood} onValueChange={setMood} />

          {/* Journal Text Editor */}
          <JournalTextEditor value={entry} onChange={setEntry} />

          {/* Submit Buttons */}
          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={isSubmitting || !entry.trim()}
              className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isSubmitting ? "Saving..." : "Save Entry"}
            </button>

            <button
              type="button"
              onClick={() => {
                setEntry("");
                setMood(5);
              }}
              className="btn-outline"
            >
              Clear
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
