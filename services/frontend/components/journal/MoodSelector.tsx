interface MoodSliderProps {
  value: number;
  onValueChange: (value: number) => void;
  min?: number;
  max?: number;
}

export function MoodSlider({
  value,
  onValueChange,
  min = 1,
  max = 10,
}: MoodSliderProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-dark-200 mb-3">
        How are you feeling? (1-10)
      </label>
      <div className="flex items-center gap-4">
        <span className="text-sm text-dark-400 w-6">{min}</span>
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onValueChange(parseInt(e.target.value, 10))}
          className="flex-1 h-3 rounded-lg appearance-none cursor-pointer bg-dark-600 accent-lotus-500"
        />
        <span className="text-sm text-dark-400 w-6">{max}</span>
      </div>
      <p className="text-sm text-dark-400 mt-1">Mood: {value}</p>
    </div>
  );
}
