import type { ReactNode } from "react";

import { commentUrl } from "@/lib/data";
import { formatNumber, formatPct, showPct } from "@/lib/format";
import type { BreakdownRow } from "@/lib/types";

export function Section({
  kicker,
  title,
  description,
  aside,
  children,
}: {
  kicker: string;
  title: string;
  description?: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="kicker">{kicker}</span>
          <h2 className="text-xl font-medium tracking-tight">{title}</h2>
          {description ? <p className="max-w-2xl text-sm text-muted">{description}</p> : null}
        </div>
        {aside}
      </div>
      {children}
    </section>
  );
}

export function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div className="card flex flex-col gap-1 p-4">
      <span className="kicker">{label}</span>
      <span className="num text-2xl text-zinc-50">{value}</span>
      {detail ? <span className="text-xs text-muted">{detail}</span> : null}
    </div>
  );
}

export function Evidence({ ids, label = "comments" }: { ids: string[]; label?: string }) {
  if (ids.length === 0) {
    return <span className="text-xs text-muted">no evidence ids</span>;
  }
  const singular = label.endsWith("s") ? label.slice(0, -1) : label;
  return (
    <details className="group">
      <summary className="cursor-pointer font-mono text-[11px] text-muted hover:text-accent">
        {ids.length} {ids.length === 1 ? singular : label}
      </summary>
      <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
        {ids.slice(0, 40).map((id) => (
          <li key={id}>
            <a
              href={commentUrl(id)}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[11px] text-sky-300 underline decoration-line underline-offset-2 hover:text-accent"
            >
              {id}
            </a>
          </li>
        ))}
        {ids.length > 40 ? <li className="text-[11px] text-muted">+{ids.length - 40} more</li> : null}
      </ul>
    </details>
  );
}

export function BreakdownTable({
  rows,
  unit = "respondents",
}: {
  rows: BreakdownRow[];
  unit?: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-line text-left">
            <th className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
              Item
            </th>
            <th className="py-2 pr-4 text-right font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
              {unit}
            </th>
            <th className="py-2 pr-4 text-right font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
              Share
            </th>
            <th className="py-2 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
              Evidence
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.node} className="border-b border-line/60 align-top">
              <td className={`py-2 pr-4 ${row.node === "unstated" ? "text-muted" : ""}`}>
                {row.label}
              </td>
              <td className="num py-2 pr-4 text-right">{formatNumber(row.count)}</td>
              <td className="py-2 pr-4 text-right font-mono text-xs text-muted">
                {showPct(row.n_denominator) ? formatPct(row.pct, row.n_denominator) : "—"}
              </td>
              <td className="py-2">
                <Evidence ids={row.comment_ids} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Callout({ children, tone = "note" }: { children: ReactNode; tone?: "note" | "warn" }) {
  const border = tone === "warn" ? "border-amber-500/40" : "border-line";
  const background = tone === "warn" ? "bg-amber-500/5" : "bg-panel2/60";
  return (
    <div className={`rounded-lg border ${border} ${background} p-3 text-xs leading-relaxed text-muted`}>
      {children}
    </div>
  );
}

export function Denominator({ n, label = "respondents" }: { n: number; label?: string }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted">
      n = {formatNumber(n)} {label}
    </span>
  );
}
