import type { EChartsCoreOption } from "echarts/core";

import type { BreakdownRow, CooccurrenceData, Migration } from "@/lib/types";

export const PALETTE = [
  "#d6f36a",
  "#7dd3fc",
  "#f9a8d4",
  "#c4b5fd",
  "#fcd34d",
  "#5eead4",
  "#fca5a5",
  "#a3e635",
  "#93c5fd",
  "#fdba74",
];

const FONT = "ui-monospace, SFMono-Regular, Menlo, monospace";
const MUTED = "#8b93a1";
const LINE = "#262b33";

export function barOption(rows: BreakdownRow[], { unit = "respondents" } = {}): EChartsCoreOption {
  const filtered = rows.filter((row) => row.count > 0);
  const ordered = [...filtered].sort((a, b) => a.count - b.count);
  return {
    backgroundColor: "transparent",
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      splitLine: { lineStyle: { color: LINE } },
      axisLabel: { color: MUTED, fontFamily: FONT, fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: ordered.map((row) => row.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#e4e4e7", fontFamily: FONT, fontSize: 11 },
    },
    tooltip: {
      backgroundColor: "#181b20",
      borderColor: LINE,
      textStyle: { color: "#f4f4f5", fontFamily: FONT, fontSize: 12 },
      formatter: (params: { dataIndex: number }) => {
        const row = ordered[params.dataIndex];
        return `<strong>${row.label}</strong><br/>${row.count} ${unit} of ${row.n_denominator}`;
      },
    },
    series: [
      {
        type: "bar",
        data: ordered.map((row, index) => ({
          value: row.count,
          itemStyle: { color: row.node === "unstated" ? "#3f4652" : PALETTE[index % PALETTE.length] },
        })),
        barMaxWidth: 14,
        label: {
          show: true,
          position: "right",
          color: "#d4d4d8",
          fontFamily: FONT,
          fontSize: 10,
        },
      },
    ],
  };
}

export function sankeyOption(migrations: Migration[]): EChartsCoreOption {
  const links = new Map<string, { source: string; target: string; value: number }>();
  for (const migration of migrations) {
    const key = `${migration.from_label}→${migration.to_label}`;
    const existing = links.get(key);
    if (existing) existing.value += 1;
    else links.set(key, { source: migration.from_label, target: migration.to_label, value: 1 });
  }
  const names = new Set<string>();
  for (const link of links.values()) {
    names.add(link.source);
    names.add(link.target);
  }
  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#181b20",
      borderColor: LINE,
      textStyle: { color: "#f4f4f5", fontFamily: FONT, fontSize: 12 },
    },
    series: [
      {
        type: "sankey",
        left: 8,
        right: 120,
        top: 16,
        bottom: 16,
        nodeGap: 12,
        nodeWidth: 10,
        emphasis: { focus: "adjacency" },
        label: { color: "#d4d4d8", fontFamily: FONT, fontSize: 11 },
        lineStyle: { color: "gradient", opacity: 0.28, curveness: 0.5 },
        itemStyle: { borderWidth: 0 },
        data: [...names].map((name) => ({
          name,
          itemStyle: { color: PALETTE[[...names].indexOf(name) % PALETTE.length] },
        })),
        links: [...links.values()],
      },
    ],
  };
}

export function heatmapOption(cooccurrence: CooccurrenceData, limit = 12): EChartsCoreOption {
  const nodes = cooccurrence.nodes.slice(0, limit);
  const index = new Map(nodes.map((node, position) => [node.node, position]));
  const pairs = cooccurrence.edges.filter((edge) => index.has(edge.a) && index.has(edge.b));
  const data: [number, number, number][] = pairs.map((edge) => [
    index.get(edge.a) ?? 0,
    index.get(edge.b) ?? 0,
    edge.count,
  ]);
  return {
    backgroundColor: "transparent",
    grid: { left: 8, right: 16, top: 8, bottom: 40, containLabel: true },
    xAxis: {
      type: "category",
      data: nodes.map((node) => node.label),
      axisLabel: { color: MUTED, fontFamily: FONT, fontSize: 10, rotate: 35 },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: LINE } },
    },
    yAxis: {
      type: "category",
      data: nodes.map((node) => node.label),
      axisLabel: { color: MUTED, fontFamily: FONT, fontSize: 10 },
      axisLine: { lineStyle: { color: LINE } },
    },
    tooltip: {
      backgroundColor: "#181b20",
      borderColor: LINE,
      textStyle: { color: "#f4f4f5", fontFamily: FONT, fontSize: 12 },
      formatter: (params: { data: [number, number, number] }) => {
        const [x, y, value] = params.data;
        return `${nodes[y].label} + ${nodes[x].label}: ${value} respondents`;
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(2, ...data.map(([, , value]) => value)),
      show: false,
      inRange: { color: ["#1b1f26", "#4d5a2a", "#d6f36a"] },
    },
    series: [
      {
        type: "heatmap",
        data,
        itemStyle: { borderColor: "#0a0b0d", borderWidth: 2, borderRadius: 2 },
        emphasis: { itemStyle: { borderColor: "#d6f36a" } },
      },
    ],
  };
}
