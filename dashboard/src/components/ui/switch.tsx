import { Switch, SwitchThumb } from "@ui-sdk/react/switch";

export function SwitchRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.08em] text-muted">
      {label}
      <Switch
        checked={checked}
        onCheckedChange={(next) => onChange(next)}
        className="relative h-5 w-9 rounded-full border border-line bg-panel2 data-[checked]:border-accent-dim data-[checked]:bg-accent/20"
      >
        <SwitchThumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-muted transition-transform data-[checked]:translate-x-[1.15rem] data-[checked]:bg-accent" />
      </Switch>
    </label>
  );
}
