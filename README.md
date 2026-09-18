# 风格比价温度计（GitHub Pages 版）

两个面板，同一网站、同一网址：

1. **成长100 / 价值100** —— 成长 vs 价值 风格轮动温度计
2. **中证1000 / 沪深300** —— 小盘 vs 大盘 规模轮动温度计

**全自动更新，无需任何服务器常驻、无需你开机。**

## 面板与口径

| 面板 | 内容 | 数据源 |
|---|---|---|
| 成长/价值 | 国证成长100(980080) ÷ 国证价值100(980081)，年线 MA250、布林带 242日/±2σ | 国证官网 hq.cnindex.com.cn |
| 中证1000/沪深300 | 中证1000 ÷ 沪深300，年线 MA250、布林带 242日/±2σ | 新浪财经 money.finance.sina.com.cn（国证兜底） |

- 比价数据起点：2013-01-04（全历史连续序列）

## 目录结构

```
index.html              网站首页（引用同域 echarts.min.js，无外部 CDN 依赖）
echarts.min.js          ECharts 5.5.0 库（同域引用，避免 CDN 被墙）
generate_data.py        抓比价/年线/布林带 → gv_data.json / sz_data.json
gv_data.json            成长/价值 数据
sz_data.json            中证1000/沪深300 数据
.github/workflows/      比价周度更新工作流
```

## 自动更新机制

| 工作流 | 触发时间（北京时间） | 做的事 |
|---|---|---|
| `weekly.yml` 风格比价周度 | 每周五 15:10（UTC 07:10） | 跑 `generate_data.py` 刷新两组比价 |

- 任一数据源临时失败会**保留旧文件不覆盖**（下次再补），不会让网站白屏。
- GitHub Actions 的 cron 是「北京时间 = UTC + 8」，已在工作流注明。
- 也可手动触发：仓库 `Actions` 页 → 选 `weekly.yml` → `Run workflow`。

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
