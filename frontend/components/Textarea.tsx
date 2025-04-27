import React from "react";

interface TextareaProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const Textarea: React.FC<TextareaProps> = ({ value, onChange }) => (
  <textarea
    className="border rounded-lg p-3 resize-none h-40"
    placeholder="Write your journal entry..."
    value={value}
    onChange={onChange}
    required
  />
);

export default Textarea;