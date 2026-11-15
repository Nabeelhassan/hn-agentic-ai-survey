import type { BreakdownRow } from "./types";

export const SMALL_N = 10;

export function showPct(denominator: number): boolean {
  return denominator >= SMALL_N;
}

export function formatPct(value: number | null, denominator: number): string {
  if (!showPct(denominator) || value === null) {
    return "count only";
  }
  return `${value.toFixed(1)}%`;
}

export function formatRowPct(row: BreakdownRow): string {
  return formatPct(row.pct, row.n_denominator);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
}

export function formatDate(iso: string | null): string {
  if (!iso) return "unknown";
  return new Date(iso).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}

export function humanizeNode(node: string): string {
  return node.replace(/^other:/, "");
}
