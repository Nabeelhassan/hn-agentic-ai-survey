# UI SDK for behaviour, ECharts for charts

`@ui-sdk/react` supplies interaction and accessibility (popups, selection, virtualized lists,
tabs) but has no chart primitives and no table component. Charts use ECharts because the two
charts that carry this analysis — the harness migration Sankey and the tool co-occurrence
heatmap — are weak or custom-D3 work elsewhere. UI SDK parts stay behind adapters in
`dashboard/src/components/ui/` so the beta's API churn is contained.
