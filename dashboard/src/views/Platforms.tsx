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
import { formatNumber } from "@/lib/format";
import type { OrchestrationData, ThemesData } from "@/lib/types";

export function Platforms({
  orchestration,
  themes,
}: {
  orchestration: OrchestrationData;
  themes: ThemesData;
}) {
  const users = orchestration.orchestration_users.length;

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <Stat
          label="Orchestrating agents"
          value={formatNumber(users)}
          detail={`of ${formatNumber(orchestration.n_denominator)} respondents`}
        />
        <Stat
          label="Named an orchestration tool"
          value={formatNumber(orchestration.orchestration.filter((row) => row.node !== "unstated").length)}
          detail="distinct tools or custom setups"
        />
        <Stat
          label="Using an agent platform"
          value={formatNumber(
            orchestration.platforms.reduce((sum, row) => sum + (row.node === "unstated" ? 0 : row.count), 0),
          )}
          detail="outside coding work"
        />
      </div>

      <Section
        kicker="Q4"
        title="Orchestration and swarms"
        description="Only tooling whose stated purpose is coordinating several agents or sessions. Running two terminals by hand is not orchestration, even when it is described enthusiastically."
        aside={<Denominator n={orchestration.n_denominator} />}
      >
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="card p-3">
            <Chart
              option={barOption(orchestration.orchestration)}
              height={Math.max(220, orchestration.orchestration.length * 26)}
              ariaLabel="Respondents using each orchestration tool"
            />
          </div>
          <BreakdownTable rows={orchestration.orchestration} />
        </div>
      </Section>

      <Section
        kicker="Q5"
        title="Broader agent platforms"
        description="Agent products used outside coding: personal assistants, browser agents, desktop agents. Use cases are the short phrases respondents attached."
        aside={<Denominator n={orchestration.n_denominator} />}
      >
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="card p-3">
            <Chart
              option={barOption(orchestration.platforms)}
              height={Math.max(220, orchestration.platforms.length * 26)}
              ariaLabel="Respondents using each agent platform"
            />
          </div>
          <BreakdownTable rows={orchestration.platforms} />
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {Object.entries(orchestration.platform_use_cases).map(([node, useCases]) => (
            <div key={node} className="card p-4">
              <span className="kicker">{node.replace(/^other:/, "")}</span>
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {useCases.map((useCase) => (
                  <li
                    key={useCase}
                    className="rounded-full border border-line px-2 py-0.5 font-mono text-[11px] text-fg-soft"
                  >
                    {useCase}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <Callout>
          A platform is counted per respondent regardless of how many use cases they list, so the
          platform totals add up to something and the use-case tags do not.
        </Callout>
      </Section>

      <Section
        kicker="Themes"
        title="What people complain about and praise"
        description="Short phrases extracted from the comments, grouped, and only shown once at least three respondents say the same thing."
        aside={<Denominator n={themes.n_denominator} />}
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-left">
                <th className="py-2 pr-4 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Theme
                </th>
                <th className="py-2 pr-4 text-right font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Respondents
                </th>
                <th className="py-2 font-mono text-[10px] font-normal uppercase tracking-[0.12em] text-muted">
                  Evidence
                </th>
              </tr>
            </thead>
            <tbody>
              {themes.themes.map((theme) => (
                <tr key={theme.theme} className="border-b border-line/60">
                  <td className="py-2 pr-4">{theme.theme}</td>
                  <td className="num py-2 pr-4 text-right">{formatNumber(theme.count)}</td>
                  <td className="py-2">
                    <Evidence ids={theme.comment_ids} />
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
