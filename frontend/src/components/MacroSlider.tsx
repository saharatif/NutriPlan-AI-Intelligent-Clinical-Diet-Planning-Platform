export default function MacroSlider({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return (
    <label className="slider-label">
      Serving {value.toFixed(2)}x
      <input type="range" min="0.5" max="3" step="0.25" value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}
