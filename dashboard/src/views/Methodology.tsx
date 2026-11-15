import { useState } from "react";

import { Callout, Section, Stat } from "@/components/primitives";
import { Segmented } from "@/components/ui/segmented";
import { formatDate, formatNumber, formatUsd } from "@/lib/format";
import type { MethodologyData } from "@/lib/types";

const CATEGORIES = ["subscription", "harness", "orchestration", "platform", "model-source"];

export function Methodology({ data }: { data: MethodologyData }) {
  const [filter, setFilter] = useState("all");
  const nodes = data.taxonomy.nodes.filter((node) => filter === "all" || node.category === filter);
  const extraction = data.extraction;
  const evaluation = data.eval;

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Snapshot" value={data.snapshot_id} detail={formatDate(data.generated_at)} />
        <Stat
          label="Comments extracted"
          value={formatNumber(extraction?.comments_extracted ?? 0)}
          detail={`${formatNumber(extraction?.records ?? 0)} model records`}
        />
        <Stat
          label="Review queue"
          value={formatNumber(extraction?.review_items ?? 0)}
          detail="low confidence or model disagreement"
        />
        <Stat
          label="Extraction spend"
          value={formatUsd(extraction?.total_cost_usd ?? 0)}
          detail="actual token cost across both models"
        />
      </div>

      <Section
        kicker="Method"
        title="How a comment becomes a number"
        description="Fetch, normalize, extract with two models, canonicalize against a versioned taxonomy, merge per author, aggregate. Each step leaves a committed artifact."
      >
        <ol className="flex flex-col gap-3 text-sm">
          {[
            {
              title: "Fetch",
              body: "Algolia supplies comment text and parentage in one paged call; the Firebase API supplies the authoritative tree including dead and deleted comments. Both payloads are frozen under data/raw/<snapshot>/ and never refetched.",
            },
            {
              title: "Normalize",
              body: "HN HTML is converted to text, reply depth resolved, and every body hashed so an edit between snapshots is visible rather than silent.",
            },
            {
              title: "Extract",
              body: "Each comment is sent to two models with the same prompt and versioned taxonomy. Records carry model, prompt hash, taxonomy version, and content hash. Disagreements and low-confidence records go to a review queue.",
            },
            {
              title: "Merge",
              body: "Comment records are merged per author into respondents. Second-hand reports are excluded from setup counts. Conflicting statements are kept visible instead of overwritten.",
            },
            {
              title: "Aggregate",
              body: "Counts are unique HN accounts, not mentions. Every row keeps its denominator and the comment ids behind it, and “unstated” stays a row.",
            },
          ].map((step, index) => (
            <li key={step.title} className="card flex gap-4 p-4">
              <span className="num text-sm text-accent">{String(index + 1).padStart(2, "0")}</span>
              <div className="flex flex-col gap-1">
                <span className="font-medium">{step.title}</span>
                <span className="text-xs leading-relaxed text-muted">{step.body}</span>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      <Section
        kicker="Accuracy"
        title="Agreement with a hand-labelled sample"
        description="Gold labels are written by hand for a stratified sample of comments, then compared field by field against the primary model's extraction."
      >
        {evaluation ? (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Stat
                label="Answers classification"
                value={
                  evaluation.answers_questions_accuracy !== null
                    ? `${Math.round(evaluation.answers_questions_accuracy * 100)}%`
                    : "n/a"
                }
                detail={`${evaluation.evaluated} of ${evaluation.gold_cases} labelled`}
              />
              {Object.entries(evaluation.fields).map(([field, value]) => (
                <Stat
                  key={field}
                  label={value.label}
                  value={value.f1 !== null ? `F1 ${value.f1.toFixed(2)}` : "n/a"}
                  detail={`P ${value.precision ?? "–"} · R ${value.recall ?? "–"}`}
                />
              ))}
            </div>
            {evaluation.misses.length ? (
              <Callout tone="warn">
                {evaluation.misses.length} field mismatches are recorded in the report, each with the
                expected and predicted node ids. They stay visible rather than being smoothed away.
              </Callout>
            ) : null}
          </div>
        ) : (
          <Callout tone="warn">
            No gold set has been scored for this snapshot yet. The dashboard shows extraction output
            before validation rather than pretending the numbers are verified.
          </Callout>
        )}
      </Section>

      <Section
        kicker="Runs"
        title="Extraction runs"
        description="Each run records the model, prompt hash, taxonomy version, and token usage so a change in the data can be traced to a change in the method."
      >
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-line text-left">
                {["Model", "Records", "Input tokens", "Output tokens", "Cost"].map((header) => (
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
              {(extraction?.runs ?? []).map((run) => (
                <tr key={run.model} className="border-b border-line/60">
                  <td className="py-2 pr-4 font-mono text-xs">{run.model}</td>
                  <td className="num py-2 pr-4">{formatNumber(run.records_written)}</td>
                  <td className="num py-2 pr-4">{formatNumber(run.usage.input_tokens ?? 0)}</td>
                  <td className="num py-2 pr-4">{formatNumber(run.usage.output_tokens ?? 0)}</td>
                  <td className="num py-2 pr-4">{formatUsd(run.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        kicker="Vocabulary"
        title={`Taxonomy v${data.taxonomy.version}`}
        description="Canonical node ids the extraction is forced to choose from. Anything unlisted becomes other:<name> so a new tool shows up as itself instead of hiding in “other”."
        aside={
          <Segmented
            label="Taxonomy category"
            value={filter}
            onChange={setFilter}
            options={[{ value: "all", label: "All" }, ...CATEGORIES.map((category) => ({ value: category, label: category }))]}
          />
        }
      >
        <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
          {nodes.map((node) => (
            <div key={node.id} className="card flex flex-col gap-1 p-3">
              <span className="font-mono text-xs text-accent">{node.id}</span>
              <span className="text-sm">{node.label}</span>
              <span className="kicker">{node.category}</span>
              {node.aliases?.length ? (
                <span className="font-mono text-[10px] text-muted">{node.aliases.join(", ")}</span>
              ) : null}
            </div>
          ))}
        </div>
      </Section>

      <Section
        kicker="Rules"
        title="House rules this dashboard follows"
        description="These are enforced by the pipeline, not by the chart."
      >
        <ul className="flex flex-col gap-2 text-sm">
          {data.conventions.map((convention) => (
            <li key={convention} className="flex gap-3">
              <span className="text-accent">—</span>
              <span className="text-muted">{convention}</span>
            </li>
          ))}
        </ul>
        <Callout>
          Snapshot {data.snapshot_id} is immutable. Corrections produce a new snapshot; the numbers
          here will not silently change.
        </Callout>
      </Section>
    </div>
  );
}
