---
name: editorial-pptx-charts
description: >
  Pure-static, custom-colored editorial data visualization skill inspired by
  lieflat-charts aesthetics and engineered specifically to integrate with
  ppt-master. Renders deterministic, ppt-master-canonical SVG charts using any
  2-3 custom theme colors matched to the active ppt-master template or brand
  palette (no hardcoded preset themes required). Outputs work in dual mode:
  natively compiled into editable PowerPoint DrawingML shapes via ppt-master
  svg_to_pptx.py, or inserted as crisp vector SVG / PNG assets into slides.
---

# Editorial PPTX Charts — Pure-Static Color Chart Skill for `ppt-master`

本 Skill 沿用 `lieflat-charts` 的编辑叙事视觉语法（可数单位、发丝线、账本导轨、结论先行标题、旁注与克制留白），面向 **PPT 演示与 `ppt-master` 工作流** 重构：

1. **彩色优先 · 自定义 2–3 主题色**：不依赖预置固定主题，直接读取 `ppt-master` 模板的 `design_spec.md` / `spec_lock.md`，或接收 2–3 个自定义 `#RRGGBB` 主题色与底色（支持透明底 `transparent` 与暗底 `dark`），自动派生明度梯、分类色与结构线，并执行 WCAG 对比度保护。
2. **纯静态零依赖**：零 JavaScript、零 `<style>`、零 `class`、零 `<animate*>`、零外部字体/CDN，100% 确定性渲染。
3. **双模原生兼容 `ppt-master`**：
   - **整页模式 (`--mode slide`, `1280×720`)**：直接符合 `ppt-master` `shared-standards-core.md` 合同，可直接放入 `svg_output/` 经 `svg_to_pptx.py` 编译为**原生可编辑 PowerPoint DrawingML 形状与文本框**。
   - **卡片/插图模式 (`--mode card`, 自定义宽高 + 可选透明底)**：可作为独立矢量图片 `<image href="../images/chart.svg" .../>` 插入 `ppt-master` 多栏页面，或提取 `<g id="chart-area">` 直接并入页面 SVG。

---

## 一、快速工作流（与 `ppt-master` 配合的 5 步）

1. **锁定配色来源**：
   - 若正在运行 `ppt-master` 项目：直接指向当前项目的 `spec_lock.md` 或品牌/风格模板的 `design_spec.md`（使用 `--from-ppt-master <path>` 自动提取 2–3 个主题色、底色与字体栈）。
   - 若用户指定主题色：使用 `--colors "#HEX1,#HEX2"` 或 `--colors "#HEX1,#HEX2,#HEX3"`，并按页面背景设置 `--bg "#FFFFFF"` / `--bg transparent` / `--dark`。
2. **按数据形状选图**：查阅 [`catalog.md`](./catalog.md) 的数据形状决策表，锁定具体图型（Phase 1–3 全量 37 款图型已就绪，完整覆盖 Lupi Basics F1–F17、Lupi Editorial 经典与主页样张、Glance 快读与流向）。
3. **编写图表 JSON 规格**：提供真实数据、结论式标题（不写“柱状图”等图型名）、含图例与时间范围的副标题、诚实的单位说明与来源行。
4. **调用确定性渲染引擎生成静态 SVG**：
   ```bash
   python "${SKILL_DIR}/scripts/render.py" <chart_spec.json> \
     --from-ppt-master <ppt_master_design_spec_or_spec_lock.md> \
     --mode slide \
     -o <project_path>/svg_output/04_chart.svg
   ```
   或生成卡片插图放进 `ppt-master` 项目的 `images/`：
   ```bash
   python "${SKILL_DIR}/scripts/render.py" <chart_spec.json> \
     --colors "#051C2C,#2251FF,#D97706" \
     --bg transparent --mode card --width 600 --height 440 \
     -o <project_path>/images/revenue_chart.svg
   ```
5. **校验并编译 PPTX**：
   - `render.py` 默认运行内置 `validator.py` 校验 `ppt-master` SVG 合同（全大写 `#RRGGBB`、无 `rgba()`、无 CSS/JS、`font-size >= 12`、顶层 `data-pptx-bounds` 无重叠）。
   - 使用 `ppt-master` 的 `svg_quality_checker.py` 与 `svg_to_pptx.py`（或 `${SKILL_DIR}/scripts/pptx_bridge.py`）编译输出可编辑 `.pptx`。

---

## 二、2–3 主题色语义映射规则

| 传入颜色数 | 角色映射 | 说明 |
|---|---|---|
| **2 色** (`c1, c2`) | `c1` = 主数据色；`c2` = 对比序列 / 强调焦点 | 自动从 `c1`/`c2` 与底色派生柔和中间调与明度梯，绝不偷渡无关色相 |
| **3 色** (`c1, c2, c3`) | `c1` = 主数据色；`c2` = 次序列 / 对比组；`c3` = 唯一主角强调（峰值 / 冠军 / 负向警示 / 关键标注） | 同一张图只保留一个强调焦点，避免三色平均乱撒 |

**暗底支持**：需要暗底衬托的图型（如 `dot_cascade`）或在深色 PPT 模板上出图时，传入 `--dark`（或深色 `--bg`），引擎会自动反转文字、结构线与序数梯并保证可读对比度。

---

## 三、双模插入 `ppt-master` 的选择原则

| 场景 | 推荐模式 | 接入 `ppt-master` 方式 |
|---|---|---|
| 整页核心数据页、需要客户在 PowerPoint 中微调每个文字和图形 | `--mode slide` (`1280×720`) | 直接放入 `svg_output/`，走 `ppt-master` `svg_to_pptx.py` 生成原生可编辑 DrawingML |
| 多栏布局中的半页/局部图表、高密度点阵图（避免单页过多 PPT 形状） | `--mode card --bg transparent` | 保存至 `images/<name>.svg`，在页面 SVG 中用 `<image href="../images/<name>.svg" x="..." y="..." width="..." height="..." preserveAspectRatio="xMidYMid meet"/>` 嵌入 |

---

## 四、硬性纪律（交付前必查）

1. **标题写结论，不写图型名**：例如“企业版与专业版贡献超七成增量”，而非“各版本收入柱状图”。
2. **单位诚实、绝不断轴**：柱状/横档图从 0 起步；面积编码使用 `sqrt(value)`；数值较大时自动缩放单位并在底注如实写明 `ONE RUNG = ...`。
3. **同一套 PPT 锁定同一组 2–3 个主题色**：禁止同份演示文稿里不同页混搭不相关色板。
4. **纯静态 XML 合规**：禁止 `<style>`、`class`、`<script>`、`<animate*>`、`rgba()`、HTML 命名实体（`&nbsp;` 等）与 `< 12px` 字号。
