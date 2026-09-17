# 风格比价温度计 + 159915 乖离率1.1 策略（GitHub Pages 版）

三个面板，同一网站、同一网址：

1. **成长100 / 价值100** —— 成长 vs 价值 风格轮动温度计
2. **中证1000 / 沪深300** —— 小盘 vs 大盘 规模轮动温度计
3. **159915 乖离率1.1 策略** —— 日线策略信号 + 回测统计 + 次日买卖提示

**全自动更新，无需任何服务器常驻、无需你开机。**

## 面板与口径

| 面板 | 内容 | 数据源 |
|---|---|---|
| 成长/价值 | 国证成长100(980080) ÷ 国证价值100(980081)，年线 MA250、布林带 242日/±2σ | 国证官网 hq.cnindex.com.cn |
| 中证1000/沪深300 | 中证1000 ÷ 沪深300，年线 MA250、布林带 242日/±2σ | 新浪财经 money.finance.sina.com.cn（国证兜底） |
| 159915 策略 | 创业板ETF 日线乖离率1.1；日K线标注买卖点；回测(单笔/总收益/最大回撤/同期指数)；次日信号与买入门槛 | 新浪财经 sz159915 + 创业板指 399006 |

- 比价数据起点：2013-01-04（全历史连续序列）
- 159915 策略：年上腿（连跌1日·次日开盘买·持5）／年下腿（连跌3日·次日高开买·持8），以 250 年线划分；回测为「核心触发」版（未含原文档的闸门/贯通细化项，总收益高于文档 +5905.5% 属预期差异，闸门可后续补）。

## 目录结构

```
index.html              网站首页（引用同域 echarts.min.js，无外部 CDN 依赖）
echarts.min.js          ECharts 5.5.0 库（同域引用，避免 CDN 被墙）
generate_data.py        抓比价/年线/布林带 → gv_data.json / sz_data.json
generate_strategy.py    抓 159915 日线+创业板指 → strategy_data.json（信号+回测）
fetch_live.py           每日 09:24 抓 159915 集合竞价实时行情 → live_signal.json
gv_data.json            成长/价值 数据
sz_data.json            中证1000/沪深300 数据
strategy_data.json      159915 策略信号 + 回测
live_signal.json        159915 当日实时触发状态
.github/workflows/      三个 Actions 工作流
```

## 自动更新机制（三个机器人）

| 工作流 | 触发时间（北京时间） | 做的事 |
|---|---|---|
| `weekly.yml` 风格比价周度 | 每周五 15:10（UTC 07:10） | 跑 `generate_data.py` 刷新两组比价 |
| `daily-strategy.yml` 策略信号每日 | 每个交易日收盘后 15:00（UTC 07:00） | 跑 `generate_strategy.py` 算次日信号+回测 |
| `daily-live.yml` 实时触发每日 | 每日 09:24（UTC 01:24） | 跑 `fetch_live.py` 抓集合竞价，比对信号门槛给出买入提示 |

- 任一数据源临时失败会**保留旧文件不覆盖**（下次再补），不会让网站白屏。
- GitHub Actions 的 cron 是「北京时间 = UTC + 8」，已在各工作流注明。
- **注意**：GitHub 免费 runner 的定时任务可能延迟几分钟（尤其 9:24 那档），「实时触发」实际可能在 9:30 前后执行，属正常现象；若当日非信号日则直接标注「非信号日/非交易日」。
- 也可手动触发：仓库 `Actions` 页 → 选对应工作流 → `Run workflow`。

## 部署到 GitHub Pages（一次性，已由脚本/AI 完成）

1. 仓库 `Settings` → `Pages` → `Build and deployment`：
   - Source 选 **Deploy from a branch**，Branch 选 **main** / **/ (root)**，保存。
2. 几分钟後访问 `https://<用户名>.github.io/<仓库名>/` 即可。
3. 之后所有更新全自动，无需你再做任何事。

## 本地预览

```bash
cd gv_gh
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```
