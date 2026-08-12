---
date: 2026-08-11
slug: fitness-data-viz
authors: [minke]
categories: [MkDocs, 健身]
---

# 用 ECharts 给 MkDocs 健身页加数据可视化

健身记录页用 FastAPI（`api_server.py`）+ JSON 文件记录训练和身体指标，但一直只有表格，看不出趋势。这周给两个 tab 都加了 ECharts 折线图。

## 现状

- **训练记录**：日期、训练日、动作（组/次/重量）、感受、有氧
- **身体指标**：日期、体重、腰围、臂围、血压、力量数据

数据通过 `/fitness/training-records`、`/fitness/body-metrics` 两个 API 存取。

## 加图表

MkDocs 的 `md_in_html` 允许在 Markdown 里内嵌 HTML + `<script>`，于是：

1. 引入 ECharts（CDN）
2. 加一个 `div` 容器
3. 从 API 拉数据，`echarts.init` + `setOption` 画折线

训练 tab 用双轴：感受（左轴 0-10，面积线）+ 总组数（右轴，柱状）。身体指标 tab 画体重 / 腰围趋势。

```javascript
const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
chart.setOption({
  xAxis: { type: 'category', data: sorted.map(d => d.date) },
  series: [{ name: '体重 (kg)', type: 'line', data: sorted.map(d => d.weight) }]
});
```

## 踩到的坑

- **tab 切换要 resize**：图表在隐藏的 tab 里 `init` 时容器尺寸为 0，切过去要 `chart.resize()`，否则是空白。
- **数据先排序**：API 返回不保证按日期有序，先排好再画。
- **空值用 `connectNulls`**：漏记的日期不会把折线断开。

现在每次训练或称重后，趋势自动更新，一眼看出体重和训练量的走向。
