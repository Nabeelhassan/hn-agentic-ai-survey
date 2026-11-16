import { useMemo, useState } from "react";

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
import type { PlanRow, ProviderCatalog, SubscriptionsData } from "@/lib/types";

const VIEWS = [
  { value: "providers", label: "Providers" },
  { value: "plans", label: "Plans & prices" },
  { value: "spend", label: "Spend" },
];

const METHOD_LABEL: Record<string, string> = {
  unspecified: "no tier stated",
  no_match: "not in catalog",
  ambiguous_price: "ambiguous price",
  unknown_provider: "provider not in catalog",
};

const VERIFICATION_TONE: Record<string, string> = {
  verified: "text-accent",
  partial: "text-amber-300",
  unverified: "text-muted",
};

const SYMBOLS: Record<string, string> = { USD: "$", EUR: "€", GBP: "£" };

const AUDIENCE_ORDER: Record<string, number> = { individual: 0, team: 1, enterprise: 2 };

function money(currency: string, amount: number | null): string {
  if (amount === null) return "—";
  if (amount === 0) return "free";
  const symbol = SYMBOLS[currency] ?? "";
  return `${symbol}${amount.toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1")}`;
}

function planPrice(plan: PlanRow): string {
  const monthly = money(plan.currency, plan.price_monthly);
  if (plan.annual_monthly !== null && plan.price_monthly !== null) {
    return `${monthly} · ${money(plan.currency, plan.annual_monthly)}/mo annual`;
  }
  return monthly;
}

function ProviderCard({ provider }: { provider: ProviderCatalog }) {
  const sorted = useMemo(
    () =>
      [...provider.plans].sort((a, b) => {
        const audience = (AUDIENCE_ORDER[a.audience] ?? 9) - (AUDIENCE_ORDER[b.audience] ?? 9);
        if (audience !== 0) return audience;
        const price = (p: PlanRow) => (p.price_monthly === null ? Number.MAX_SAFE_INTEGER : p.price_monthly);
        return price(a) - price(b) || a.plan_label.localeCompare(b.plan_label);
      }),
    [provider.plans],
  );

  return (
    <div className="card flex flex-col gap-2 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">{provider.provider_label}</h3>
          <span className={`font-mono text-[10px] uppercase tracking-[0.1em] ${VERIFICATION_TONE[provider.verification]}`}>
            {provider.verification}
          </span>
        </div>
        <span className="font-mono text-[10px] text-muted">
          n = {formatNumber(provider.n_provider_denominator)}
          {provider.source_url ? (
            <>
              {" · "}
              <a
                href={provider.source_url}
                target="_blank"
                rel="noreferrer"
                className="underline decoration-line underline-offset-2 hover:text-accent"
              >
                source
              </a>
            </>
          ) : null}
        </span>
      </div>
      {provider.notes ? <p className="text-[11px] leading-relaxed text-muted">{provider.notes}</p> : null}
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-line text-left">
            {["Plan", "List price", "Respondents", "As written"].map((header) => (
              <th
                key={header}
                className="py-1.5 pr-3 font-mono text-[10px] font-normal uppercase tracking-[0.1em] text-muted"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((plan) => (
            <tr key={plan.plan_id} className="border-b border-line/50 align-top">
              <td className="py-1.5 pr-3">
                <span className={plan.price_monthly === 0 ? "text-muted" : ""}>{plan.plan_label}</span>
                {plan.audience !== "individual" ? (
                  <span className="ml-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-muted">
                    {plan.audience}
                  </span>
                ) : null}
                {plan.list_price_monthly !== null ? (
                  <span className="ml-1.5 text-[10px] text-muted line-through">
                    {money(plan.currency, plan.list_price_monthly)}
                  </span>
                ) : null}
                {plan.note ? <p className="text-[10px] text-muted">{plan.note}</p> : null}
              </td>
              <td className="num whitespace-nowrap py-1.5 pr-3 text-xs text-zinc-300">{planPrice(plan)}</td>
              <td className="py-1.5 pr-3">
                <span className="num text-sm">{formatNumber(plan.count)}</span>
                {plan.n_provider_denominator >= 10 && plan.pct_of_provider !== null ? (
                  <span className="ml-2 text-[10px] text-muted" title="share of that provider's respondents">
                    {plan.pct_of_provider.toFixed(0)}% of provider
                  </span>
                ) : null}
              </td>
              <td className="py-1.5">
                {plan.raw_variants.length ? (
                  <details>
                    <summary className="cursor-pointer font-mono text-[10px] text-muted hover:text-accent">
                      {plan.raw_variants.length} {plan.raw_variants.length === 1 ? "form" : "forms"}
                    </summary>
                    <ul className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5">
                      {plan.raw_variants.map((variant) => (
                        <li key={variant.tier_raw} className="font-mono text-[10px] text-zinc-400">
                          {variant.tier_raw}
                          {variant.count > 1 ? ` ×${variant.count}` : ""}
                        </li>
                      ))}
                    </ul>
                  </details>
                ) : null}
                {plan.comment_ids.length ? <Evidence ids={plan.comment_ids} /> : null}
                {!plan.raw_variants.length && !plan.comment_ids.length ? (
                  <span className="text-[10px] text-muted">—</span>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Subscriptions({ data }: { data: SubscriptionsData }) {
  const [view, setView] = useState("providers");
  const multi = data.multi_subscription;
  const { matching } = data;

  const observed = useMemo(
    () =>
      [...data.catalog]
        .filter((provider) => provider.plans.length > 0)
        .sort(
          (a, b) =>
            b.n_provider_denominator - a.n_provider_denominator ||
            a.provider_label.localeCompare(b.provider_label),
        ),
    [data.catalog],
  );
  const emptyCatalog = data.catalog.filter((provider) => provider.plans.length === 0);
  const unmatched = data.unmatched_tiers;
  const unspecified = unmatched.filter((row) => row.method === "unspecified");
  const unresolved = unmatched.filter((row) => row.method !== "unspecified");

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
        description="Only plans the author pays for themselves. Employer-provided seats and trials are excluded, and two plans from one provider count as two subscriptions. The plans view includes free tiers so every written tier string has somewhere to land."
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

        {view === "plans" ? (
          <div className="flex flex-col gap-4">
            <Callout>
              {formatNumber(matching.matched_assignments)} of {formatNumber(matching.assignments)} tier
              strings resolved to a catalog plan
              {Object.entries(matching.methods).length
                ? ` (${Object.entries(matching.methods)
                    .filter(([method]) => method !== "unspecified")
                    .map(([method, count]) => `${count} ${method.replace(/_/g, " ")}`)
                    .join(", ")})`
                : ""}
              . {formatNumber(matching.unmatched_assignments)} did not resolve, including{" "}
              {formatNumber(unspecified.reduce((sum, row) => sum + row.count, 0))} that stated no tier at
              all.
            </Callout>

            <div className="grid gap-3">
              {observed.map((provider) => (
                <ProviderCard key={provider.provider} provider={provider} />
              ))}
            </div>

            {emptyCatalog.length ? (
              <p className="text-[11px] text-muted">
                No catalog entries for {emptyCatalog.map((provider) => provider.provider_label).join(", ")}.
              </p>
            ) : null}

            {unresolved.length ? (
              <div className="card p-3">
                <details>
                  <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.1em] text-muted hover:text-accent">
                    {unresolved.length} tier strings could not be matched
                  </summary>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-line text-left">
                          {["Provider", "As written", "Respondents", "Why", "Evidence"].map((header) => (
                            <th
                              key={header}
                              className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {unresolved.map((row) => (
                          <tr key={`${row.provider_label}-${row.tier_raw}`} className="border-b border-line/60">
                            <td className="py-2 pr-4">{row.provider_label}</td>
                            <td className="py-2 pr-4 font-mono text-xs text-zinc-300">{row.tier_raw}</td>
                            <td className="num py-2 pr-4">{row.count}</td>
                            <td className="py-2 pr-4 text-xs text-muted">
                              {METHOD_LABEL[row.method] ?? row.method}
                            </td>
                            <td className="py-2">
                              <Evidence ids={row.comment_ids} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              </div>
            ) : null}
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

        {view === "spend" ? (
          <Callout tone="warn">
            Spend is only counted when an author stated a monthly figure. Annual plans, credits, and
            per-token billing are recorded in the tier text, not converted into a monthly number.
            {data.spend.values.length < 10
              ? " Fewer than 10 people stated a figure, so these are counts, not a distribution."
              : null}
          </Callout>
        ) : null}

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
