interface JournalTextEditorProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
}

export function JournalTextEditor({
    value,
    onChange,
    placeholder = "What's on your mind today? Share your thoughts, experiences, or anything you'd like to remember..."
}: JournalTextEditorProps) {
    const wordCount = value.trim().split(/\s+/).filter(word => word.length > 0).length;
    const charCount = value.length;

    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
                Your Journal Entry
            </label>
            <div className="relative">
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    rows={12}
                    className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                />
                <div className="absolute bottom-3 right-3 text-xs text-gray-500 bg-white px-2 py-1 rounded">
                    {wordCount} words • {charCount} characters
                </div>
            </div>
        </div>
    );
}