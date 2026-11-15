import { Chart } from "@/components/charts/Chart";
import { barOption } from "@/components/charts/options";
import {
  BreakdownTable,
  Callout,
  Denominator,
  Section,
  Stat,
} from "@/components/primitives";
import { formatNumber } from "@/lib/format";
import type { ModelsData } from "@/lib/types";

export function Models({ data }: { data: ModelsData }) {
  const local = data.local_share;

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <Stat
          label="Beyond subscriptions"
          value={formatNumber(data.sources.reduce((sum, row) => sum + (row.node === "unstated" ? 0 : row.count), 0))}
          detail="respondents using APIs, OpenRouter, or local models"
        />
        <Stat
          label="Locally hosted"
          value={formatNumber(local?.count ?? 0)}
          detail={local ? `of ${formatNumber(local.n_denominator)} respondents` : "unstated"}
        />
        <Stat
          label="Sources named"
          value={formatNumber(data.sources.filter((row) => row.node !== "unstated").length)}
          detail="distinct providers and routes"
        />
      </div>

      <Section
        kicker="Q2"
        title="Models outside the subscriptions"
        description="Pay-as-you-go APIs, OpenRouter, and locally hosted models. A respondent can appear in several rows; the denominator is respondents, not mentions."
        aside={<Denominator n={data.n_denominator} />}
      >
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="card p-3">
            <Chart
              option={barOption(data.sources)}
              height={Math.max(240, data.sources.length * 26)}
              ariaLabel="Respondents using each outside model source"
            />
          </div>
          <BreakdownTable rows={data.sources} />
        </div>
      </Section>

      <Section
        kicker="Models"
        title="Which models they name"
        description="Named model families used outside the subscription, or alongside one. Shares use all respondents as the denominator, so the rows do not add to 100%."
        aside={<Denominator n={data.n_denominator} />}
      >
        {data.models.length ? (
          <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
            <div className="card p-3">
              <Chart
                option={barOption(data.models)}
                height={Math.max(200, data.models.length * 26)}
                ariaLabel="Respondents naming each model family"
              />
            </div>
            <BreakdownTable rows={data.models} />
          </div>
        ) : (
          <Callout>No respondent named a specific model family outside their subscription.</Callout>
        )}
      </Section>

      <Section
        kicker="Route"
        title="How they reach those models"
        description="Access route, counted once per respondent even when they name several models."
        aside={<Denominator n={data.n_denominator} />}
      >
        <BreakdownTable rows={data.access} />
        <Callout>
          “Unstated” means the respondent described a subscription and harness but never said whether
          they also use an API, OpenRouter, or a local model. It is kept as a row so the total never
          silently equals zero.
        </Callout>
      </Section>
    </div>
  );
}
