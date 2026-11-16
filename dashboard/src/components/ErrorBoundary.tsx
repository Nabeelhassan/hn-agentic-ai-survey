import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("dashboard render failed", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="card m-6 flex flex-col gap-2 border-amber-500/40 bg-amber-500/5 p-5">
          <span className="kicker">Render failed</span>
          <p className="text-sm text-fg">{this.state.error.message}</p>
          <pre className="overflow-x-auto rounded bg-ink p-3 font-mono text-[11px] text-muted">
            {this.state.error.stack?.split("\n").slice(0, 6).join("\n")}
          </pre>
          <button
            type="button"
            className="w-fit rounded-md border border-line px-3 py-1 font-mono text-[11px] text-fg"
            onClick={() => this.setState({ error: null })}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
