import type { EChartsCoreOption } from "echarts/core";

import type { BreakdownRow, CooccurrenceData, MigrationEdge } from "@/lib/types";

const FONT = "ui-monospace, SFMono-Regular, Menlo, monospace";

const DARK_PALETTE = [
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

interface ChartTokens {
  palette: string[];
  axis: string;
  line: string;
  strong: string;
  soft: string;
  tipBg: string;
  tipText: string;
  unstated: string;
  heat: [string, string, string];
  nodeBorder: string;
  accent: string;
}

function chartTokens(): ChartTokens {
  if (typeof document === "undefined") {
    return {
      palette: DARK_PALETTE,
      axis: "#8b93a1",
      line: "#262b33",
      strong: "#e4e4e7",
      soft: "#d4d4d8",
      tipBg: "#181b20",
      tipText: "#f4f4f5",
      unstated: "#3f4652",
      heat: ["#1b1f26", "#4d5a2a", "#d6f36a"],
      nodeBorder: "#0a0b0d",
      accent: "#d6f36a",
    };
  }
  const style = getComputedStyle(document.documentElement);
  const read = (name: string, fallback: string) => style.getPropertyValue(name).trim() || fallback;
  const palette = read("--chart-palette", DARK_PALETTE.join(", "))
    .split(",")
    .map((color) => color.trim())
    .filter(Boolean);
  return {
    palette: palette.length ? palette : DARK_PALETTE,
    axis: read("--chart-axis", "#8b93a1"),
    line: read("--chart-line", "#262b33"),
    strong: read("--chart-strong", "#e4e4e7"),
    soft: read("--chart-soft", "#d4d4d8"),
    tipBg: read("--chart-tip-bg", "#181b20"),
    tipText: read("--chart-tip-text", "#f4f4f5"),
    unstated: read("--chart-unstated", "#3f4652"),
    heat: [
      read("--chart-heat-1", "#1b1f26"),
      read("--chart-heat-2", "#4d5a2a"),
      read("--chart-heat-3", "#d6f36a"),
    ],
    nodeBorder: read("--chart-node-border", "#0a0b0d"),
    accent: read("--chart-accent", "#d6f36a"),
  };
}

export function barOption(rows: BreakdownRow[], { unit = "respondents" } = {}): EChartsCoreOption {
  const tokens = chartTokens();
  const filtered = rows.filter((row) => row.count > 0);
  const ordered = [...filtered].sort((a, b) => a.count - b.count);
  return {
    backgroundColor: "transparent",
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: {
      type: "value",
      splitLine: { lineStyle: { color: tokens.line } },
      axisLabel: { color: tokens.axis, fontFamily: FONT, fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: ordered.map((row) => row.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: tokens.strong, fontFamily: FONT, fontSize: 11 },
    },
    tooltip: {
      backgroundColor: tokens.tipBg,
      borderColor: tokens.line,
      textStyle: { color: tokens.tipText, fontFamily: FONT, fontSize: 12 },
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
          itemStyle: {
            color:
              row.node === "unstated"
                ? tokens.unstated
                : tokens.palette[index % tokens.palette.length],
          },
        })),
        barMaxWidth: 14,
        label: {
          show: true,
          position: "right",
          color: tokens.soft,
          fontFamily: FONT,
          fontSize: 10,
        },
      },
    ],
  };
}

export function sankeyOption(edges: MigrationEdge[]): EChartsCoreOption {
  const tokens = chartTokens();
  const names = new Set<string>();
  for (const edge of edges) {
    names.add(edge.from_label);
    names.add(edge.to_label);
  }
  const ordered = [...names];
  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: tokens.tipBg,
      borderColor: tokens.line,
      textStyle: { color: tokens.tipText, fontFamily: FONT, fontSize: 12 },
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
        label: { color: tokens.soft, fontFamily: FONT, fontSize: 11 },
        lineStyle: { color: "gradient", opacity: 0.28, curveness: 0.5 },
        itemStyle: { borderWidth: 0 },
        data: ordered.map((name) => ({
          name,
          itemStyle: { color: tokens.palette[ordered.indexOf(name) % tokens.palette.length] },
        })),
        links: edges.map((edge) => ({
          source: edge.from_label,
          target: edge.to_label,
          value: edge.count,
        })),
      },
    ],
  };
}

export function heatmapOption(cooccurrence: CooccurrenceData, limit = 12): EChartsCoreOption {
  const tokens = chartTokens();
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
      axisLabel: { color: tokens.axis, fontFamily: FONT, fontSize: 10, rotate: 35 },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: tokens.line } },
    },
    yAxis: {
      type: "category",
      data: nodes.map((node) => node.label),
      axisLabel: { color: tokens.axis, fontFamily: FONT, fontSize: 10 },
      axisLine: { lineStyle: { color: tokens.line } },
    },
    tooltip: {
      backgroundColor: tokens.tipBg,
      borderColor: tokens.line,
      textStyle: { color: tokens.tipText, fontFamily: FONT, fontSize: 12 },
      formatter: (params: { data: [number, number, number] }) => {
        const [x, y, value] = params.data;
        return `${nodes[y].label} + ${nodes[x].label}: ${value} respondents`;
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(2, ...data.map(([, , value]) => value)),
      show: false,
      inRange: { color: tokens.heat },
    },
    series: [
      {
        type: "heatmap",
        data,
        itemStyle: { borderColor: tokens.nodeBorder, borderWidth: 2, borderRadius: 2 },
        emphasis: { itemStyle: { borderColor: tokens.accent } },
      },
    ],
  };
}
