import {
  SegmentedControl,
  SegmentedControlIndicator,
  SegmentedControlItem,
} from "@ui-sdk/react/segmented-control";

export interface SegmentOption {
  value: string;
  label: string;
}

export function Segmented({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: SegmentOption[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <SegmentedControl
      aria-label={label}
      value={value}
      onValueChange={(next) => {
        if (next !== null) onChange(next);
      }}
      className="relative inline-flex gap-1 rounded-lg border border-line bg-panel p-1"
    >
      <SegmentedControlIndicator className="absolute inset-y-1 rounded-md bg-panel2" />
      {options.map((option) => (
        <SegmentedControlItem
          key={option.value}
          value={option.value}
          className="relative z-10 rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-[0.08em] text-muted data-[checked]:text-accent"
        >
          {option.label}
        </SegmentedControlItem>
      ))}
    </SegmentedControl>
  );
}
