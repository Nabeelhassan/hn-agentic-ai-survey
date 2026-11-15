import { Chart } from "@/components/charts/Chart";
import { barOption } from "@/components/charts/options";
import {
  BreakdownTable,
  Callout,
  Denominator,
  Section,
  Stat,
} from "@/components/primitives";
import { formatDate, formatNumber } from "@/lib/format";
import type { OverviewData } from "@/lib/types";

const ANSWER_LABELS: Record<string, string> = {
  full: "Answered 3+ questions",
  partial: "Answered 1–2 questions",
  none: "Discussed AI, no setup",
  meta: "About the thread",
  off_topic: "Off topic",
};

export function Overview({ data }: { data: OverviewData }) {
  const answered = data.answer_distribution
    .filter((row) => row.label === "full" || row.label === "partial")
    .reduce((total, row) => total + row.count, 0);
  const total = data.answer_distribution.reduce((sum, row) => sum + row.count, 0);
  const answerRows = data.answer_distribution.map((row) => ({
    ...row,
    label: ANSWER_LABELS[row.label] ?? row.label,
  }));

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat
          label="Respondents"
          value={formatNumber(data.respondents)}
          detail="authors who stated a setup"
        />
        <Stat
          label="Commenters"
          value={formatNumber(data.commenters)}
          detail={`${formatNumber(data.comments)} comments total`}
        />
        <Stat
          label="Answered a question"
          value={`${total ? Math.round((100 * answered) / total) : 0}%`}
          detail={`${formatNumber(answered)} of ${formatNumber(total)} comments with text`}
        />
        <Stat
          label="Top-level"
          value={formatNumber(data.top_level_comments)}
          detail="direct replies to the post"
        />
      </div>

      <Section
        kicker="Coverage"
        title="How much of the thread is actually an answer"
        description="A comment counts as a substantive answer when it says something about the author's own setup. Everything else is still counted, and still visible here."
        aside={<Denominator n={total} label="comments" />}
      >
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <div className="card p-3">
            <Chart
              option={barOption(answerRows, { unit: "comments" })}
              height={240}
              ariaLabel="Comments grouped by whether they answer the survey questions"
            />
          </div>
          <BreakdownTable rows={answerRows} unit="comments" />
        </div>
      </Section>

      <Section
        kicker="Provenance"
        title="What this snapshot is"
        description="One frozen fetch of the thread, with every derived number traceable to comment ids."
      >
        <div className="grid gap-3 md:grid-cols-2">
          <div className="card flex flex-col gap-2 p-4 text-sm">
            <span className="kicker">Source</span>
            <a
              className="text-sky-300 underline decoration-line underline-offset-2 hover:text-accent"
              href="https://news.ycombinator.com/item?id=50366117"
              target="_blank"
              rel="noreferrer"
            >
              Ask HN: What's your current AI agentic setup?
            </a>
            <span className="text-xs text-muted">
              {data.story ? `${formatNumber(data.story.score)} points · ` : ""}
              {formatNumber(data.comments)} comments fetched · snapshot{" "}
              <span className="font-mono">{data.snapshot_id}</span>
            </span>
            <span className="text-xs text-muted">
              Normalized {formatDate(data.generated_at)} UTC. The thread is live; later comments are
              not in this snapshot.
            </span>
          </div>
          <div className="card flex flex-col gap-2 p-4 text-sm">
            <span className="kicker">Gaps</span>
            <ul className="list-disc space-y-1 pl-4 text-xs text-muted">
              {data.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
              <li>
                {formatNumber(data.deleted)} deleted and {formatNumber(data.dead)} dead comments are
                retained in the dataset but cannot provide a setup.
              </li>
              <li>{formatNumber(data.second_hand_comments)} comments describe someone else's setup.</li>
            </ul>
          </div>
        </div>
        <Callout>
          Percentages appear only where the denominator is at least 10. Below that, tables show raw
          counts so a 2-of-3 split never reads as a trend.
        </Callout>
      </Section>
    </div>
  );
}
