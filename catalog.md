# Editorial PPTX Charts — 图型目录与分阶段路线图

本目录沿用 `lieflat-charts` 的视觉家族（**Lupi Basics / Lupi Editorial / Glance**）与数据形状主键，全部重构为**纯静态、自定义 2–3 主题色、兼容 `ppt-master` 的原生 SVG**。

---

## Phase 1 · 核心高频组（已实现 · 12 款）

覆盖商务汇报、经营复盘、调研与产品分析中 85% 的高频数据形状：

| 编号 | `type` Key | 风格系 | 数据形状 | 最佳场景 | 色彩语义 |
|---|---|---|---|---|---|
| F1 | `rung_bars` | Lupi Basics | 少类目竖向比较（≤8） | 收入/指标对比，可数横档 + 每 5 档点标 | `c1` 主柱 + `c3/c2` 冠军高亮（可选 `ramp` / `categorical`） |
| F5 | `tick_rows` | Lupi Basics | 横向排名比较（≤8，长/中文标签友好） | 团队产出、渠道排行、调研选项 | `c1` 主队列 + `c3/c2` 头名高亮 |
| F2 | `hairline_line` | Lupi Basics | 连续/日序列趋势（≤45 期） | 日活、签约、营收趋势 + 日历地板 + 空心标记 + 可选对比线 | `c1` 主线 + `c2` 虚线对比 + `c3` 峰值标注 |
| F3 | `hairline_area` | Lupi Basics | 时期量级形态（20–60 期） | 并发量、流量波形，由垂直发丝构成的诚实面积 | `c1→c2` 时间色相渐变发丝 + `c3` 峰值 |
| F4 | `tick_donut` | Lupi Basics | 100% 构成（≤6 段） | 流量/营收结构，100 根钟表刻度（1 tick = 1%） | 2–3 主题色及其明度派生分段 |
| F6 | `paired_rungs` | Lupi Basics | 两系列并肩对比（同比 / 计划 vs 实际） | YoY 对比、两版本表现，双梯并列可数 | `c2` 左梯（对照） vs `c1` 右梯（当期） |
| F7 | `stacked_rungs` | Lupi Basics | 堆叠构成（≤5 类 × 2–4 段） | 区域×产品线结构，段间留 1 档呼吸空隙 | `c1 / c2 / c3` 自下而上分段 |
| F12 | `dumbbell_queue` | Lupi Basics | 前后变化对比（≤7 类） | 优化前后耗时/指标对比，串珠 = 精确变化单位 | `c2` 空心前值 + `c1` 实心后值 + `c3` 串珠 |
| F10 | `dot_heat` | Lupi Basics | 二维矩阵密度（星期×小时 / 维度×维度） | 工单波峰、使用时段分布，点面积 ∝ 数值 | 序数明度梯 + `c3` 峰值虚线圈 |
| L2 | `dot_cascade` | Lupi Editorial | 升序点阵阶梯排行（6–18 项） | 故障根因、长尾排行，斜坡虚线基线 + 堆叠点阵（支持 `--dark` 暗卡） | 主题序数梯 + `c3` 最高项高亮 |
| G10 | `diverging_bar` | Glance | 带正负的净增减 / 差异对比 | 客户净增减、预算偏差、NPS 净值 | `c1` 正向向右 + `c3/c2` 负向向左 |
| G4 | `dot_waffle` | Glance | 100% 占比快读（饼图默认替代） | 汇报 3 秒看懂占比，10×10 百点阵列 + 右侧大数图例 | 2–3 主题色及其派生明度色块 |

---

## Phase 2 · Lupi Editorial 深度叙事与高级基础组（已实现 · 15 款）

沿用 `lieflat-charts` 公开库与 GitHub 主页样张中的标志性高密度编辑图表，全部纯静态矢量重构并支持自定义 2–3 主题色：

| 编号 | `type` Key | 风格系 | 数据形状与视觉特征 |
|---|---|---|---|
| F8 | `plumb_scatter` | Lupi Basics | 铅垂线散点图：每点垂发丝至底部条码刻度地板，标注最优/最差极值 |
| F9 | `rung_waterfall` | Lupi Basics | 增减分解横档瀑布图：实档加/总计、虚档扣减、虚线台阶衔接 |
| F11 | `tick_gauge` | Lupi Basics | 210° 刻度进度仪表盘（100 ticks，1 tick = 1% 目标，25/50/75/100 点标） |
| L1 | `launch_fan` | Lupi Editorial | 扇形放射时间轴：每条辐条=一个功能，大圆=上线周与当前规模（面积编码），小点=延续周次 |
| L3 | `barcode_lollipop` | Lupi Editorial | 90 天级条码棒棒糖通栏图：每天一根全高发丝 + 重力垂杆 + 周末空心点 + Top-3 峰值标注 |
| L4 | `arc_matrix` | Lupi Editorial | 弧形地平线气泡矩阵（分类×分类+量），每行微微上拱，Top 单元格高亮标数 |
| L13 | `hourglass_stream` | Lupi Editorial | 漏斗沙漏流：每阶段条码宽度=人数，贝塞尔发丝束向下汇流 + 左侧转化率 |
| L14 | `hundred_field` | Lupi Editorial | 黄金角向日葵百点群簇：100 个点分成 2–5 组星团 + 虚线星座连线 + 每 5 人辐条 |
| L15 | `ballot_tally` | Lupi Editorial | 多选题百格选票队列：每行 100 根竖线，勾选者加墨加高，每 10 人一个点标 |
| L17 | `calendar_heat` | Lupi Editorial | 全年 52×7 日历点阵热力墙 + 月份刻度 + 峰值虚线圈与斜体旁注引线 |
| L20 | `parallel_coords` | Lupi Editorial | 多维平行坐标发丝束：3–6 连续维度，贝塞尔光滑连线，综合最优上强调色 |
| L-EX1 | `radial_patchwork` | Lupi Editorial（主页样张） | 24 小时叠加扇片图：半透明层叠编码密度，异常/事故扇片加实线强调轮廓 |
| L-EX2 | `trend_lineage` | Lupi Editorial（主页样张） | 垂直生命周期谱系图：实心发布、空心重构、虚线休眠、底点标记存续状态 |
| L-EX3 | `type_colonnade` | Lupi Editorial（主页样张） | 多对一发丝归属图：左侧条目经平滑贝塞尔曲线汇入右侧按数量缩放的归属节点 |
| L-EX4 | `radial_convergence` | Lupi Editorial（主页样张） | 放射收敛图：外圈逐条记录节点经发丝束向内圈主题大圆聚拢 |

---

## Phase 3 · 分布、流向与 Glance 快读补全组（已实现 · 10 款）

| 编号 | `type` Key | 风格系 | 数据形状与视觉特征 |
|---|---|---|---|
| F13 | `nested_treemap` | Lupi Basics | 纯静态 SVG Squarified 两层嵌套矩形树图（零 ECharts 依赖，色相区分一级父组） |
| F14 | `rung_histogram` | Lupi Basics | 连续分箱横档直方图（箱界落于列间）+ 中位数虚线旗标 |
| F15 | `tick_box` | Lupi Basics | 分组五数概括胶囊箱线图 + 纸色中位横档 + 空心离群点 |
| F16 | `stream_ribbon` | Lupi Basics | 连续时间对称中轴多系列流图（Streamgraph / ThemeRiver）+ 条码时间地板 |
| F17 | `candlestick` | Lupi Basics | 编辑部风格胶囊 K 线图（空心收涨 / 实心收跌 + 发丝上下影线 + 极值标注） |
| G13 | `big_slice` | Glance | 角度（占比）× 半径（强度）双编码玫瑰扇图 + 同心虚线标尺环 |
| G19 | `violin` | Glance | 静态高斯核密度（KDE）小提琴分布轮廓 + 纸色中位横档 |
| G20 | `matrix_heat` | Glance | 大圆角直接读数热力矩阵（每格自动对比度标数 + 峰值强调） |
| G21 | `rank_strip` | Glance | 静态可印刷排名胶片条带图（#1 穿强调色 + 行末 ▲/▼ 净变动旗标） |
| G22 | `aggregate_sankey` | Glance | 两端聚合半透明宽带流向桑基图（颜色随源渠道，交叉清晰可读） |
