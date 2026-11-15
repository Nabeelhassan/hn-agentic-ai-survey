import { useEffect, useState } from "react";

import { Callout } from "@/components/primitives";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ViewTabs } from "@/components/ui/tabs";
import { loadDataset } from "@/lib/data";
import { formatNumber } from "@/lib/format";
import type { Dataset } from "@/lib/types";
import { Explorer } from "@/views/Explorer";
import { Harnesses } from "@/views/Harnesses";
import { Methodology } from "@/views/Methodology";
import { Models } from "@/views/Models";
import { Overview } from "@/views/Overview";
import { Platforms } from "@/views/Platforms";
import { Subscriptions } from "@/views/Subscriptions";

export function App() {
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDataset()
      .then(setDataset)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, []);

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 p-8">
        <span className="kicker">Dashboard</span>
        <h1 className="text-2xl font-medium">The aggregate data is missing.</h1>
        <Callout tone="warn">{error}</Callout>
        <p className="text-sm text-muted">
          Run <code className="font-mono text-zinc-200">make aggregate &amp;&amp; make dashboard-data</code> from
          the repository root, then reload.
        </p>
      </main>
    );
  }

  if (!dataset) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted">loading snapshot…</span>
      </main>
    );
  }

  const { overview } = dataset;

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-5 py-8 lg:px-8">
      <header className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex flex-col gap-2">
            <span className="kicker">Ask HN · November 2026 · snapshot {overview.snapshot_id}</span>
            <h1 className="max-w-2xl text-3xl font-medium tracking-tight text-zinc-50">
              What Hacker News actually runs for AI agents
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-muted">
              Subscriptions, models outside those subscriptions, coding harnesses, orchestration, and
              agent platforms — extracted from {formatNumber(overview.comments)} comments, counted per
              respondent rather than per mention.
            </p>
          </div>
          <div className="card flex max-w-xs flex-col gap-2 p-4 text-xs">
            <span className="kicker">Thread</span>
            <a
              href="https://news.ycombinator.com/item?id=50366117"
              target="_blank"
              rel="noreferrer"
              className="text-sm text-sky-300 underline decoration-line underline-offset-2 hover:text-accent"
            >
              Ask HN: What&rsquo;s your current AI agentic setup?
            </a>
            <span className="text-muted">
              {formatNumber(overview.respondents)} respondents ·{" "}
              {formatNumber(overview.commenters)} commenters
            </span>
            <span className="text-muted">
              The thread is live. Later comments are not in this snapshot.
            </span>
          </div>
        </div>

        <ErrorBoundary>
          <ViewTabs
          defaultValue="overview"
          items={[
            { value: "overview", label: "Overview", content: <Overview data={overview} /> },
            {
              value: "subscriptions",
              label: "Subscriptions",
              content: <Subscriptions data={dataset.subscriptions} />,
            },
            { value: "models", label: "Models", content: <Models data={dataset.models} /> },
            {
              value: "harnesses",
              label: "Harnesses",
              content: <Harnesses data={dataset.harnesses} />,
            },
            {
              value: "platforms",
              label: "Platforms",
              content: (
                <Platforms
                  orchestration={dataset.orchestration}
                  themes={dataset.themes}
                />
              ),
            },
            { value: "explorer", label: "Explorer", content: <Explorer data={dataset.explorer} /> },
            {
              value: "method",
              label: "Method",
              content: <Methodology data={dataset.methodology} />,
            },
          ]}
          />
        </ErrorBoundary>
      </header>

      <footer className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4 text-[11px] text-muted">
        <span>
          Data from the HN Firebase and Algolia APIs, frozen as snapshot{" "}
          <span className="font-mono">{overview.snapshot_id}</span>.
        </span>
        <span className="font-mono">
          Every number links to the comments behind it.
        </span>
      </footer>
    </div>
  );
}
