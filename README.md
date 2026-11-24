# Editorial PPTX Charts

一套独立、纯静态、自定义 2–3 主题色的编辑风格数据可视化引擎与 Agent Skill：沿用 [`lieflat-charts`](https://github.com/larashero3-dotcom/lieflat-charts) 的设计美学与图型谱系，专为无缝整合 [`ppt-master`](https://github.com/hugohe3/ppt-master) 生成可编辑 `.pptx` 而打造。

> **Phase 1–3 全量 37 款图表已交付**（Phase 1 核心高频 12 款 + Phase 2 Lupi Editorial 深度叙事 15 款 + Phase 3 分布/流向/金融/层级补全 10 款），全部通过 `ppt-master` 官方 `svg_quality_checker.py`（37/37，0 error / 0 warning），并经 `svg_to_pptx.py` 编译为原生可编辑 DrawingML 形状。
>
> **全量总览演示（37 页，一份文件看全部图型）**：[`editorial_charts_37.pptx`](./examples/demo/editorial_charts_37.pptx)
> 分期演示：[`phase1`](./examples/demo/operating_review_phase1.pptx)（12 页） · [`phase2`](./examples/demo/operating_review_phase2.pptx)（15 页） · [`phase3`](./examples/demo/operating_review_phase3.pptx)（10 页）

## 全量总览

[![全部 37 款图表总览](./docs/previews/all-37-contact-sheet.png)](./examples/demo/editorial_charts_37.pptx)


## 预览

### Phase 1 · 核心高频组（12 款）

| | |
|---|---|
| ![Rung Bars](./docs/previews/01_rung_bars.png) | ![Tick Rows](./docs/previews/02_tick_rows.png) |
| **F1 `rung_bars`** — 可数横档柱 | **F5 `tick_rows`** — 刻度队列条形 |
| ![Hairline Line](./docs/previews/03_hairline_line.png) | ![Hairline Area](./docs/previews/04_hairline_area.png) |
| **F2 `hairline_line`** — 发丝折线 + 日历地板 | **F3 `hairline_area`** — 发丝面积 |
| ![Tick Donut](./docs/previews/05_tick_donut.png) | ![Paired Rungs](./docs/previews/06_paired_rungs.png) |
| **F4 `tick_donut`** — 100 刻度环形 | **F6 `paired_rungs`** — 双梯并肩对比 |
| ![Stacked Rungs](./docs/previews/07_stacked_rungs.png) | ![Dumbbell Queue](./docs/previews/08_dumbbell_queue.png) |
| **F7 `stacked_rungs`** — 呼吸堆叠横档 | **F12 `dumbbell_queue`** — 串珠哑铃 |
| ![Dot Heat](./docs/previews/09_dot_heat.png) | ![Dot Cascade](./docs/previews/10_dot_cascade.png) |
| **F10 `dot_heat`** — 面积编码点阵热力 | **L2 `dot_cascade`** — 升序点阵阶梯 |
| ![Diverging Bar](./docs/previews/11_diverging_bar.png) | ![Dot Waffle](./docs/previews/12_dot_waffle.png) |
| **G10 `diverging_bar`** — 正负双向胶囊 | **G4 `dot_waffle`** — 百点华夫占比 |

### Phase 2 · Lupi Editorial 深度叙事与高级基础组（15 款）

| | |
|---|---|
| ![Plumb Scatter](./docs/previews/13_plumb_scatter.png) | ![Rung Waterfall](./docs/previews/14_rung_waterfall.png) |
| **F8 `plumb_scatter`** — 铅垂线散点 | **F9 `rung_waterfall`** — 横档瀑布 |
| ![Tick Gauge](./docs/previews/15_tick_gauge.png) | ![Launch Fan](./docs/previews/16_launch_fan.png) |
| **F11 `tick_gauge`** — 210° 刻度仪表盘 | **L1 `launch_fan`** — 扇形放射时间轴 |
| ![Barcode Lollipop](./docs/previews/17_barcode_lollipop.png) | ![Arc Matrix](./docs/previews/18_arc_matrix.png) |
| **L3 `barcode_lollipop`** — 90 天条码棒棒糖 | **L4 `arc_matrix`** — 弧形地平线气泡矩阵 |
| ![Hourglass Stream](./docs/previews/19_hourglass_stream.png) | ![Hundred Field](./docs/previews/20_hundred_field.png) |
| **L13 `hourglass_stream`** — 漏斗沙漏流 | **L14 `hundred_field`** — 黄金角百点星团 |
| ![Ballot Tally](./docs/previews/21_ballot_tally.png) | ![Calendar Heat](./docs/previews/22_calendar_heat.png) |
| **L15 `ballot_tally`** — 多选百格选票队列 | **L17 `calendar_heat`** — 全年 52×7 日历热力 |
| ![Parallel Coords](./docs/previews/23_parallel_coords.png) | ![Radial Patchwork](./docs/previews/24_radial_patchwork.png) |
| **L20 `parallel_coords`** — 多维平行坐标 | **L-EX1 `radial_patchwork`** — 24h 叠加扇片 |
| ![Trend Lineage](./docs/previews/25_trend_lineage.png) | ![Type Colonnade](./docs/previews/26_type_colonnade.png) |
| **L-EX2 `trend_lineage`** — 垂直生命周期谱系 | **L-EX3 `type_colonnade`** — 多对一发丝归属 |
| ![Radial Convergence](./docs/previews/27_radial_convergence.png) | |
| **L-EX4 `radial_convergence`** — 放射收敛图 | |

### Phase 3 · 分布、流向与 Glance 快读补全组（10 款）

| | |
|---|---|
| ![Nested Treemap](./docs/previews/28_nested_treemap.png) | ![Rung Histogram](./docs/previews/29_rung_histogram.png) |
| **F13 `nested_treemap`** — 纯静态两层嵌套矩形树图 | **F14 `rung_histogram`** — 连续分箱横档直方图 |
| ![Tick Box](./docs/previews/30_tick_box.png) | ![Stream Ribbon](./docs/previews/31_stream_ribbon.png) |
| **F15 `tick_box`** — 胶囊五数概括箱线图 | **F16 `stream_ribbon`** — 对称中轴流图 |
| ![Candlestick](./docs/previews/32_candlestick.png) | ![Big Slice](./docs/previews/33_big_slice.png) |
| **F17 `candlestick`** — 编辑部风格 K 线图 | **G13 `big_slice`** — 角度×半径双编码扇图 |
| ![Violin](./docs/previews/34_violin.png) | ![Matrix Heat](./docs/previews/35_matrix_heat.png) |
| **G19 `violin`** — 静态 KDE 小提琴分布 | **G20 `matrix_heat`** — 圆角直读热力矩阵 |
| ![Rank Strip](./docs/previews/36_rank_strip.png) | ![Aggregate Sankey](./docs/previews/37_aggregate_sankey.png) |
| **G21 `rank_strip`** — 静态排名胶片条带 | **G22 `aggregate_sankey`** — 两端聚合流向桑基 |

## 核心特点

- **彩色优先 · 自定义 2–3 主题色**：无需内置固定主题；传入任意 2–3 个 `#RRGGBB` 主题色，或直接用 `--from-ppt-master` 从 `ppt-master` 的 `design_spec.md` / `spec_lock.md` 自动读取模板配色，派生完整色阶与结构线并自动守护 WCAG 对比度。
- **100% 纯静态矢量 SVG**：零 JS、零 CSS `<style>`、零 `class`、零动效、零外部字体或 CDN，完全确定性输出。
- **双模原生兼容 `ppt-master`**：
  - `--mode slide`（`1280×720`）：严格通过 `ppt-master` 的 `svg_quality_checker.py`，经 `svg_to_pptx.py` 直接编译为**原生可编辑 PowerPoint DrawingML 形状与文本**。
  - `--mode card`（自定义尺寸 + `--bg transparent`）：作为独立矢量图放入 `ppt-master` 项目的 `images/`，嵌入任意多栏幻灯片版式。
- **全谱系覆盖**：Phase 1（12 款）+ Phase 2（15 款）+ Phase 3（10 款）共 **37 款图表**全部落地（详见 [`catalog.md`](./catalog.md)）。

## 快速开始

只需要 Python 3.10+（零第三方依赖即可生成与校验 SVG）。

### 1. 列出已支持图型

```bash
python scripts/render.py --list
```

### 2. 用自定义 2–3 主题色渲染单张图表

```bash
# 整页 1280x720（可直接交给 ppt-master 编译为原生 PPTX）
python scripts/render.py examples/phase1_specs/01_rung_bars.json \
  --colors "#051C2C,#2251FF,#E65100" \
  --bg "#FFFFFF" \
  --mode slide \
  -o examples/out/01_rung_bars.svg

# 透明底卡片模式（供 ppt-master 多栏页面作为矢量插图嵌入）
python scripts/render.py examples/phase1_specs/05_tick_donut.json \
  --colors "#0F766E,#D97706,#1E3A8A" \
  --bg transparent \
  --mode card --width 600 --height 440 \
  -o examples/out/05_tick_donut_card.svg
```

### 3. 直接读取 `ppt-master` 模板配色批量出图并导出可编辑 PPTX

```bash
python scripts/gallery.py \
  --specs-dir examples/phase1_specs \
  --out-dir examples/out/mckinsey \
  --from-ppt-master /path/to/ppt-master/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md \
  --ppt-master /path/to/ppt-master \
  --export-pptx examples/out/mckinsey_phase1_charts.pptx
```

### 4. 一次合成全部 37 页总览（单份 PPTX + 单页画廊）

`build_showcase.py` 按给定顺序把多个 spec 目录合成一套页码连续的幻灯片，并输出一份 HTML 画廊和一份原生可编辑 PPTX：

```bash
python scripts/build_showcase.py \
  --spec-dirs examples/phase1_specs examples/phase2_specs examples/phase3_specs \
  --out-dir examples/out/showcase \
  --from-ppt-master /path/to/ppt-master/skills/ppt-master/templates/styles/operating-review/templates/design_spec.md \
  --ppt-master /path/to/ppt-master \
  --export-pptx examples/demo/editorial_charts_37.pptx
```

本仓库的 [`editorial_charts_37.pptx`](./examples/demo/editorial_charts_37.pptx) 与 [总览画廊](./examples/out/showcase/index.html) 即由该命令产出。

## 目录结构

```text
editorial-pptx-charts/
├── SKILL.md                  # 独立 Agent Skill 规范（可安装至 ~/.claude/skills/ 等）
├── catalog.md                # 37 款图型完整目录（Phase 1–3 分阶段）
├── README.md                 # 项目说明
├── scripts/
│   ├── palette.py            # 2-3 自定义主题色引擎 + ppt-master 配色解析器
│   ├── svg_builder.py        # ppt-master 规范纯静态 SVG 构建器
│   ├── validator.py          # 内置 ppt-master SVG 合同校验器
│   ├── pptx_bridge.py        # 联动 ppt-master checker & svg_to_pptx 导出器
│   ├── render.py             # 单图 CLI
│   ├── gallery.py            # 单目录批量生成 + HTML 预览 + 可选导出 PPTX
│   ├── build_showcase.py     # 多目录合成全量总览 + 单份 PPTX
│   └── charts/               # 37 款图表渲染模块
├── docs/previews/            # 37 张逐图预览 + 全量总览拼接图
└── examples/
    ├── phase1_specs/         # Phase 1 · 12 份 JSON 数据样例
    ├── phase2_specs/         # Phase 2 · 15 份 JSON 数据样例
    ├── phase3_specs/         # Phase 3 · 10 份 JSON 数据样例
    └── demo/                 # ppt-master 编译出的原生可编辑 PPTX（全量 + 分期）
```

## 作为 Agent Skill 安装

```bash
# Claude Code
git clone https://github.com/seva324/editorial-pptx-charts.git ~/.claude/skills/editorial-pptx-charts

# 或任意支持 SKILL.md 的 Agent 运行时
git clone https://github.com/seva324/editorial-pptx-charts.git ~/.agents/skills/editorial-pptx-charts
```

安装后 Agent 会依据 [`SKILL.md`](./SKILL.md) 自动选择图型、锁定 `ppt-master` 模板配色并调用 `scripts/render.py` 出图。

## 验证状态

| 检查项 | 结果 |
|---|---|
| 内置 `validator.py` 合同校验 | 37/37 PASS |
| `ppt-master` 官方 `svg_quality_checker.py` | 37/37 PASS（0 error / 0 warning） |
| `ppt-master` `svg_to_pptx.py` 原生编译 | Phase 1 (12 页) + Phase 2 (15 页) + Phase 3 (10 页)，`skipped 0`，每页 3 个可编辑分组 |
| 全量单文件总览 `editorial_charts_37.pptx` | 37 页 / 16:9 / 每页 3 个命名可编辑组（`header` · 图表 · `footer`），244 KB |
| 透明底卡片模式（`--mode card --bg transparent`） | 37/37 PASS |

## 致谢

- 设计美学与图型谱系源自 [`lieflat-charts`](https://github.com/larashero3-dotcom/lieflat-charts)
- PPTX 编译与 SVG 合同校验依赖 [`ppt-master`](https://github.com/hugohe3/ppt-master)

## License

MIT

