import { Chart } from "@/components/charts/Chart";
import { barOption, sankeyOption } from "@/components/charts/options";
import {
  BreakdownTable,
  Callout,
  Denominator,
  Evidence,
  Section,
} from "@/components/primitives";
import { formatNumber } from "@/lib/format";
import type { HarnessesData } from "@/lib/types";

export function Harnesses({ data }: { data: HarnessesData }) {
  const moves = data.migrations.length;
  const reasons = data.switch_reasons;

  return (
    <div className="flex flex-col gap-8">
      <Section
        kicker="Q3"
        title="Harnesses people actually drive"
        description="A harness is the interface, not the model: Claude Code, Codex CLI, Cursor, Aider, OpenCode, a custom front end. Someone running Claude through Cursor counts for both."
        aside={<Denominator n={data.n_denominator} />}
      >
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="card p-3">
            <Chart
              option={barOption(data.adoption)}
              height={Math.max(240, data.adoption.length * 26)}
              ariaLabel="Respondents using each coding harness"
            />
          </div>
          <BreakdownTable rows={data.adoption} />
        </div>
      </Section>

      <Section
        kicker="Primary"
        title="The one they call their main setup"
        description="One primary harness per respondent where they said which one leads. Secondary tools stay in the adoption table above."
        aside={<Denominator n={data.primary.reduce((max, row) => Math.max(max, row.n_denominator), 0)} />}
      >
        <BreakdownTable rows={data.primary} />
      </Section>

      <Section
        kicker="Migration"
        title="What they moved away from"
        description={
          moves > 0
            ? `${moves} respondents named a harness they left. Width is respondents, not mentions.`
            : "No respondent stated a harness they moved away from in this snapshot."
        }
      >
        {moves > 0 ? (
          <div className="card p-3">
            <Chart
              option={sankeyOption(data.migrations)}
              height={Math.max(280, moves * 14)}
              ariaLabel="Harness migrations from previous tool to current tool"
            />
          </div>
        ) : (
          <Callout>Nothing to draw yet. The table below lists every stated switch reason.</Callout>
        )}
        <Callout>
          Arrows are only drawn from explicit statements such as “switched from Cursor”. Silence about
          a previous tool is not treated as a migration.
        </Callout>
      </Section>

      <Section
        kicker="Why"
        title="Reasons for switching"
        description="Quoted only from respondents who stated a reason, not inferred from the direction of the move."
        aside={<span className="text-xs text-muted">{formatNumber(reasons.length)} stated reasons</span>}
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-left">
                <th className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Harness
                </th>
                <th className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Reason, in their words
                </th>
                <th className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Author
                </th>
                <th className="py-2 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Evidence
                </th>
              </tr>
            </thead>
            <tbody>
              {reasons.map((reason, index) => (
                <tr key={`${reason.author}-${index}`} className="border-b border-line/60 align-top">
                  <td className="py-2 pr-4 font-mono text-xs text-zinc-300">{reason.node}</td>
                  <td className="max-w-xl py-2 pr-4 text-zinc-200">{reason.reason}</td>
                  <td className="py-2 pr-4 text-xs text-muted">{reason.author}</td>
                  <td className="py-2">
                    <Evidence ids={reason.comment_ids} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}
