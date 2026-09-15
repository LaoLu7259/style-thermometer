# 风格比价温度计（GitHub Pages 版）

成长 / 价值、中证1000 / 沪深300 两组风格比价的长期走势 + 布林带温度计。
**周度自动更新，无需任何服务器常驻。**

## 比价定义

| 面板 | 比价 | 含义 |
|---|---|---|
| 成长100 / 价值100 | 国证成长100(980080) ÷ 国证价值100(980081) | 成长 vs 价值 风格轮动 |
| 中证1000 / 沪深300 | 中证1000 ÷ 沪深300 | 小盘 vs 大盘 规模轮动 |

- 数据起点：2013-01-04（两组均为全历史连续序列）
- 年线：MA250；布林带：242 日窗口、±2σ
- 数据源：成长/价值 = 国证指数官网（hq.cnindex.com.cn）；中证1000/沪深300 = 新浪财经（money.finance.sina.com.cn），国证官网作兜底

## 目录结构

```
index.html          网站首页（ECharts 已内联，单文件自包含，无外部 CDN 依赖）
generate_data.py    抓取并计算比价/年线/布林带，输出 gv_data.json / sz_data.json
gv_data.json        成长/价值 数据
sz_data.json        中证1000/沪深300 数据
.github/workflows/weekly.yml   Actions 工作流（周度更新）
```

## 更新机制

- **每周五 15:10（北京时间 = UTC 07:10）** 由 GitHub Actions 自动运行 `generate_data.py`，
  抓取最新收盘数据并写回 `gv_data.json` / `sz_data.json`，提交后 GitHub Pages 自动重新发布。
- 任一数据源临时失败会**保留旧文件不覆盖**（下周再补），不会让网站白屏。
- 也支持手动触发：`Actions` 页 → `风格比价周度更新` → `Run workflow`。

## 部署到 GitHub Pages（一次性）

1. 在 GitHub 新建一个**公开**仓库（例如 `style-ratio`）。
2. 把本目录全部文件推上去：
   ```bash
   cd gv_gh
   git init
   git add -A
   git commit -m "init: 风格比价温度计"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```
3. 仓库 `Settings` → `Pages` → `Build and deployment`：
   - Source 选 **Deploy from a branch**
   - Branch 选 **main** / **/ (root)**
   - 保存。
4. 几分钟後访问 `https://<你的用户名>.github.io/<仓库名>/` 即可。
   之后每周五收盘后自动刷新，无需你再做任何事。

## 本地预览

```bash
cd gv_gh
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```
