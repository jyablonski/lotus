import React from "react";

interface MoodSliderProps {
  value: number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const MoodSlider: React.FC<MoodSliderProps> = ({ value, onChange }) => (
  <div>
    <label className="block mb-2 font-medium">Mood (1-10)</label>
    <input
      type="range"
      min="1"
      max="10"
      value={value}
      onChange={onChange}
      className="w-full"
    />
    <div className="text-center mt-2">Mood: {value}</div>
  </div>
);

export default MoodSlider;