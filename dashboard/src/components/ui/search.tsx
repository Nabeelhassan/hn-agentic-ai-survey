import { Input } from "@ui-sdk/react/input";

export function SearchField({
  value,
  onChange,
  placeholder,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label: string;
}) {
  return (
    <Input
      type="search"
      aria-label={label}
      placeholder={placeholder}
      value={value}
      onValueChange={(next) => onChange(next)}
      className="w-64 rounded-md border border-line bg-panel px-3 py-1.5 font-mono text-xs text-fg placeholder:text-muted focus:border-accent-dim focus:outline-none"
    />
  );
}
