import { useTheme } from "@/lib/theme";
import { MoonIcon, SunIcon } from "@/components/ui/icons";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
      className="flex h-7 w-7 items-center justify-center rounded-md border border-line text-muted transition-colors hover:border-accent-dim hover:text-accent"
    >
      {theme === "dark" ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
    </button>
  );
}
