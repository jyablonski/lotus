interface JournalTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function JournalTextEditor({
  value,
  onChange,
  placeholder = "What's on your mind today? Share your thoughts, experiences, or anything you'd like to remember",
}: JournalTextEditorProps) {
  const wordCount = value
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0).length;
  const charCount = value.length;

  return (
    <div>
      <label className="label mb-3">Your Journal Entry</label>
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={12}
          className="textarea-primary"
          style={{ minHeight: "300px" }}
        />
        <div
          className="absolute bottom-3 right-3 text-xs text-muted-dark px-2 py-1 rounded"
          style={{ background: "rgba(30, 41, 59, 0.9)" }}
        >
          {wordCount} words &bull; {charCount} characters
        </div>
      </div>
    </div>
  );
}
