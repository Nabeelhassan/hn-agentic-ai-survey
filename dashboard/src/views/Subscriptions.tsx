import { useState } from "react";

import { Chart } from "@/components/charts/Chart";
import { barOption } from "@/components/charts/options";
import {
  BreakdownTable,
  Callout,
  Denominator,
  Evidence,
  Section,
  Stat,
} from "@/components/primitives";
import { Segmented } from "@/components/ui/segmented";
import { formatNumber, formatPct, formatRowPct, formatUsd } from "@/lib/format";
import type { SubscriptionsData } from "@/lib/types";

const VIEWS = [
  { value: "providers", label: "Providers" },
  { value: "tiers", label: "Tiers" },
  { value: "spend", label: "Spend" },
];

export function Subscriptions({ data }: { data: SubscriptionsData }) {
  const [view, setView] = useState("providers");
  const multi = data.multi_subscription;

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <Stat
          label="Paid a subscription"
          value={formatNumber(data.n_with_subscription)}
          detail={`of ${formatNumber(data.n_denominator)} respondents`}
        />
        {multi.map((row) => (
          <Stat
            key={row.node}
            label={row.label}
            value={formatNumber(row.count)}
            detail={`${formatRowPct(row)} of ${formatNumber(row.n_denominator)}`}
          />
        ))}
      </div>

      <Section
        kicker="Q1"
        title="What people personally pay for"
        description="Only plans the author pays for themselves. Employer-provided seats, free tiers, and trials are excluded, and two plans from one provider count as two subscriptions."
        aside={<Denominator n={data.n_denominator} />}
      >
        <Segmented label="Subscription view" options={VIEWS} value={view} onChange={setView} />

        {view === "providers" ? (
          <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
            <div className="card p-3">
              <Chart
                option={barOption(data.providers)}
                height={Math.max(240, data.providers.length * 26)}
                ariaLabel="Respondents paying for each subscription provider"
              />
            </div>
            <BreakdownTable rows={data.providers} />
          </div>
        ) : null}

        {view === "tiers" ? (
          <div className="card overflow-hidden">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-line text-left">
                  <th className="p-3 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                    Provider
                  </th>
                  <th className="p-3 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                    Tier as stated
                  </th>
                  <th className="p-3 text-right font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                    Respondents
                  </th>
                  <th className="p-3 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                    Evidence
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.tiers.map((row) => (
                  <tr key={`${row.node}-${row.tier_raw}`} className="border-b border-line/60">
                    <td className="p-3">{row.label}</td>
                    <td className="p-3 font-mono text-xs text-zinc-300">{row.tier_raw}</td>
                    <td className="num p-3 text-right">{formatNumber(row.count)}</td>
                    <td className="p-3">
                      <Evidence ids={row.comment_ids} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {view === "spend" ? (
          <div className="flex flex-col gap-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="card p-3">
                <Chart
                  option={barOption(
                    data.spend.buckets.map((bucket, index) => ({
                      node: `bucket-${index}`,
                      label: bucket.label,
                      count: bucket.count,
                      pct: bucket.n_denominator ? (100 * bucket.count) / bucket.n_denominator : null,
                      n_denominator: bucket.n_denominator,
                      comment_ids: bucket.comment_ids,
                    })),
                    { unit: "respondents stating spend" },
                  )}
                  height={260}
                  ariaLabel="Monthly AI spend buckets among respondents who stated a figure"
                />
              </div>
              <BreakdownTable
                rows={data.spend.buckets.map((bucket, index) => ({
                  node: `bucket-${index}`,
                  label: bucket.label,
                  count: bucket.count,
                  pct: bucket.n_denominator ? (100 * bucket.count) / bucket.n_denominator : null,
                  n_denominator: bucket.n_denominator,
                  comment_ids: bucket.comment_ids,
                }))}
                unit="respondents"
              />
            </div>
            <div className="card p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="kicker">Stated monthly totals</span>
                <span className="text-xs text-muted">{data.spend.stated} respondents</span>
              </div>
              <ul className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
                {data.spend.values.map((value) => (
                  <li
                    key={`${value.author}-${value.usd}`}
                    className="flex items-center justify-between gap-2 border-b border-line/50 py-1 text-sm"
                  >
                    <span className="truncate">{value.author}</span>
                    <span className="flex items-center gap-3">
                      <span className="num text-accent">{formatUsd(value.usd)}</span>
                      <Evidence ids={value.comment_ids} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
        <Callout tone="warn">
          Spend is only counted when an author stated a monthly figure. Annual plans, credits, and
          per-token billing are recorded in the tier text, not converted into a monthly number.
          {data.spend.values.length < 10
            ? " Fewer than 10 people stated a figure, so these are counts, not a distribution."
            : null}
        </Callout>
        <p className="text-xs text-muted">
          Multi-subscription split:{" "}
          {multi
            .map((row) => `${row.label.toLowerCase()} ${formatNumber(row.count)} (${formatPct(row.pct, row.n_denominator)})`)
            .join(" · ")}
        </p>
      </Section>
    </div>
  );
}
