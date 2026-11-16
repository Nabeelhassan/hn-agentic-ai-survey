import { useMemo, useRef, useState } from "react";

import { Callout, Evidence, Section } from "@/components/primitives";
import { SwitchRow } from "@/components/ui/switch";
import { PanelDialog } from "@/components/ui/dialog";
import { SearchField } from "@/components/ui/search";
import { commentUrl } from "@/lib/data";
import { formatNumber, formatUsd } from "@/lib/format";
import type { ExplorerData, ExplorerRow } from "@/lib/types";

const ROW_HEIGHT = 52;
const VIEWPORT = 560;

function matches(row: ExplorerRow, query: string): boolean {
  if (!query) return true;
  const needle = query.toLowerCase();
  const labels = [
    row.author,
    ...row.subscriptions.map((item) => `${item.label} ${item.tier_raw ?? ""}`),
    ...row.harnesses.map((item) => item.label),
    ...row.outside.map((item) => item.label),
    ...row.orchestration.map((item) => item.label),
    ...row.platforms.map((item) => item.label),
  ];
  return labels.some((label) => label.toLowerCase().includes(needle));
}

export function Explorer({ data }: { data: ExplorerData }) {
  const [query, setQuery] = useState("");
  const [conflictsOnly, setConflictsOnly] = useState(false);
  const [scrollTop, setScrollTop] = useState(0);
  const [selected, setSelected] = useState<ExplorerRow | null>(null);
  const viewport = useRef<HTMLDivElement>(null);

  const rows = useMemo(
    () => data.rows.filter((row) => matches(row, query) && (!conflictsOnly || row.has_conflict)),
    [data.rows, query, conflictsOnly],
  );

  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 4);
  const visible = rows.slice(start, start + Math.ceil(VIEWPORT / ROW_HEIGHT) + 8);

  return (
    <div className="flex flex-col gap-6">
      <Section
        kicker="Respondents"
        title="Everyone who stated a setup"
        description="One row per HN account. Click a row for the full setup and links back to the comments. Search matches author names and every tool or tier they named."
        aside={
          <div className="flex flex-wrap items-center gap-3">
            <SwitchRow label="Conflicts" checked={conflictsOnly} onChange={setConflictsOnly} />
            <SearchField
              label="Search respondents"
              placeholder="claude max, cursor, opencode…"
              value={query}
              onChange={setQuery}
            />
          </div>
        }
      >
        <div className="flex items-center justify-between">
          <span className="kicker">
            {formatNumber(rows.length)} of {formatNumber(data.rows.length)} respondents
          </span>
          <span className="text-xs text-muted">Rows are keyboard focusable; Enter opens the detail.</span>
        </div>

        <div className="card overflow-hidden">
          <div className="grid grid-cols-[minmax(8rem,1fr)_5rem_2fr_2fr_4rem] gap-3 border-b border-line px-3 py-2">
            {["Author", "Comments", "Subscriptions", "Harnesses", "Spend"].map((header) => (
              <span
                key={header}
                className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted"
              >
                {header}
              </span>
            ))}
          </div>
          <div
            ref={viewport}
            className="relative overflow-y-auto"
            style={{ height: VIEWPORT }}
            onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
          >
            <div style={{ height: rows.length * ROW_HEIGHT, position: "relative" }}>
              {visible.map((row, index) => {
                const position = start + index;
                return (
                  <button
                    key={row.author}
                    type="button"
                    onClick={() => setSelected(row)}
                    className="absolute inset-x-0 grid grid-cols-[minmax(8rem,1fr)_5rem_2fr_2fr_4rem] items-center gap-3 border-b border-line/50 px-3 text-left text-sm hover:bg-panel2 focus:bg-panel2 focus:outline-none"
                    style={{ top: position * ROW_HEIGHT, height: ROW_HEIGHT }}
                  >
                    <span className="flex items-center gap-1.5 truncate">
                      {row.author}
                      {row.has_conflict ? (
                        <span title="Conflicting statements in the thread" className="text-amber-400">
                          ·
                        </span>
                      ) : null}
                    </span>
                    <span className="num text-xs text-muted">{row.n_comments}</span>
                    <span className="truncate text-xs text-zinc-300">
                      {row.subscriptions.length
                        ? row.subscriptions
                            .map(
                              (item) =>
                                `${item.plan_label ?? item.label}${item.tier_raw ? ` (${item.tier_raw})` : ""}`,
                            )
                            .join(" · ")
                        : "—"}
                    </span>
                    <span className="truncate text-xs text-zinc-300">
                      {row.harnesses.length ? row.harnesses.map((item) => item.label).join(" · ") : "—"}
                    </span>
                    <span className="num text-xs text-accent">
                      {row.spend_monthly_usd !== null ? formatUsd(row.spend_monthly_usd) : "—"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        <Callout>
          Rows are virtualized, so only the visible slice is in the DOM. Filtering and search still
          apply to the whole respondent set.
        </Callout>
      </Section>

      <PanelDialog
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
        title={selected ? `${selected.author}` : ""}
        description={
          selected
            ? `${selected.n_comments} comments · ${selected.answers.full} full and ${selected.answers.partial} partial answers`
            : undefined
        }
      >
        {selected ? (
          <div className="flex flex-col gap-5 text-sm">
            <DetailGroup label="Subscriptions">
              {selected.subscriptions.length ? (
                selected.subscriptions.map((item) => (
                  <span key={item.node} className="text-zinc-200">
                    {item.label}
                    {item.plan_label ? <span className="text-accent"> · {item.plan_label}</span> : null}
                    {item.tier_raw ? <span className="text-muted"> · “{item.tier_raw}”</span> : null}
                  </span>
                ))
              ) : (
                <span className="text-muted">none stated</span>
              )}
            </DetailGroup>
            <DetailGroup label="Harnesses">
              {selected.harnesses.length ? (
                selected.harnesses.map((item) => (
                  <span key={item.node} className="text-zinc-200">
                    {item.label} <span className="font-mono text-[11px] text-muted">{item.role}</span>
                  </span>
                ))
              ) : (
                <span className="text-muted">none stated</span>
              )}
            </DetailGroup>
            <DetailGroup label="Outside models">
              {selected.outside.length ? (
                selected.outside.map((item) => (
                  <span key={item.node} className="text-zinc-200">
                    {item.label} <span className="font-mono text-[11px] text-muted">{item.access}</span>
                  </span>
                ))
              ) : (
                <span className="text-muted">none stated</span>
              )}
            </DetailGroup>
            <DetailGroup label="Orchestration">
              {selected.orchestration.length ? (
                selected.orchestration.map((item) => (
                  <span key={item.node} className="text-zinc-200">
                    {item.label}
                  </span>
                ))
              ) : (
                <span className="text-muted">none stated</span>
              )}
            </DetailGroup>
            <DetailGroup label="Platforms">
              {selected.platforms.length ? (
                selected.platforms.map((item) => (
                  <span key={item.node} className="text-zinc-200">
                    {item.label}
                  </span>
                ))
              ) : (
                <span className="text-muted">none stated</span>
              )}
            </DetailGroup>
            <DetailGroup label="Stated monthly spend">
              <span className="text-zinc-200">
                {selected.spend_monthly_usd !== null ? formatUsd(selected.spend_monthly_usd) : "not stated"}
              </span>
            </DetailGroup>
            <div className="flex flex-col gap-2">
              <span className="kicker">Comments</span>
              <ul className="flex flex-wrap gap-2">
                {selected.comment_ids.map((id) => (
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
              </ul>
              <span className="text-[11px] text-muted">
                Comments are quoted from the frozen snapshot and may have been edited on HN since.
              </span>
            </div>
            <Evidence ids={selected.comment_ids} label="comments" />
          </div>
        ) : null}
      </PanelDialog>
    </div>
  );
}

function DetailGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="kicker">{label}</span>
      <div className="flex flex-wrap gap-x-4 gap-y-1">{children}</div>
    </div>
  );
}
