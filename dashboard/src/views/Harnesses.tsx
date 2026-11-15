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
          data.migration_edges.length > 0
            ? `${moves} stated moves. The diagram shows net flows after reciprocal moves are cancelled and ${data.suppressed_migration_edges} net move(s) are suppressed to keep it acyclic; the table below lists every stated move.`
            : "No respondent stated a harness they moved away from in this snapshot."
        }
      >
        {data.migration_edges.length > 0 ? (
          <div className="card p-3">
            <Chart
              option={sankeyOption(data.migration_edges)}
              height={Math.max(280, data.migration_edges.length * 18)}
              ariaLabel="Net harness migrations from previous tool to current tool"
            />
          </div>
        ) : (
          <Callout>Nothing to draw yet. The table below lists every stated switch reason.</Callout>
        )}
        {data.migration_pairs.length ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-line text-left">
                  {["From", "To", "Respondents", "Evidence"].map((header) => (
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
                {data.migration_pairs.map((pair) => (
                  <tr key={`${pair.from}-${pair.to}`} className="border-b border-line/60">
                    <td className="py-2 pr-4">{pair.from_label}</td>
                    <td className="py-2 pr-4">{pair.to_label}</td>
                    <td className="num py-2 pr-4">{pair.count}</td>
                    <td className="py-2">
                      <Evidence ids={pair.comment_ids} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <Callout>
          Arrows are only drawn from explicit statements such as “switched from Cursor”. Silence about
          a previous tool is not treated as a migration, and two people swapping tools in opposite
          directions cancel out rather than forming a cycle.
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
