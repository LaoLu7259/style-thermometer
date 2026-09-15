# -*- coding: utf-8 -*-
"""
每日抓取并生成比价兜底静态 JSON：
  - 成长/价值 (980080/980081): 国证官网 hq.cnindex.com.cn
  - 中证1000/沪深300 (000852/000300): 新浪财经 money.finance.sina.com.cn (主) + 国证官网(兜底)
输出 gv_web/gv_data.json 与 gv_web/sz_data.json，由网页同源读取展示。
抓取失败则保留旧文件不覆盖。
"""
import urllib.request, json, datetime, os, time

GZ = "https://hq.cnindex.com.cn/market/market/getIndexDailyDataWithDataFormat"
SINA = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "CN_MarketData.getKLineData?symbol=%s&scale=240&ma=no&datalen=4000")
HEAD = {"User-Agent": "Mozilla/5.0"}
MA_ANNUAL = 250
BB_WIN = 242
BB_K = 2
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_guozheng(gcode, vcode, retries=4):
    def one(code):
        url = ("%s?indexCode=%s&startDate=2013-01-01&endDate=2099-12-31&frequency=day"
               % (GZ, code))
        last = None
        for _ in range(retries):
            try:
                req = urllib.request.Request(url, headers=HEAD)
                with urllib.request.urlopen(req, timeout=30) as r:
                    d = json.loads(r.read().decode("utf-8"))
                rows = (d.get("data") or {}).get("data") or []
                out = {row[0]: float(row[5]) for row in rows}
                if not out:
                    last = RuntimeError("%s 返回空" % code); time.sleep(1.5); continue
                return out
            except Exception as e:
                last = e; time.sleep(1.5)
        raise last or RuntimeError("%s 失败" % code)
    return one(gcode), one(vcode)


def fetch_sina(sym_g, sym_v, retries=4):
    def one(sym):
        url = SINA % sym
        last = None
        for _ in range(retries):
            try:
                req = urllib.request.Request(
                    url, headers={**HEAD, "Referer": "https://finance.sina.com.cn/"})
                raw = urllib.request.urlopen(req, timeout=30).read().decode("gbk", "ignore")
                arr = json.loads(raw)
                out = {o["day"]: float(o["close"]) for o in arr}
                if not out:
                    last = RuntimeError("%s 返回空" % sym); time.sleep(1.5); continue
                return out
            except Exception as e:
                last = e; time.sleep(1.5)
        raise last or RuntimeError("%s 失败" % sym)
    return one(sym_g), one(sym_v)


def mean(a):
    return sum(a) / len(a)


def std(a):
    m = mean(a)
    return (sum((x - m) ** 2 for x in a) / len(a)) ** 0.5


def compute(g, v):
    dates = sorted(d for d in g if d in v)
    n = len(dates)
    gv = [g[d] for d in dates]
    vv = [v[d] for d in dates]
    ratio = [gv[i] / vv[i] for i in range(n)]
    ma250 = [mean(ratio[i - MA_ANNUAL + 1:i + 1]) if i + 1 >= MA_ANNUAL else None
             for i in range(n)]
    bb_mid, bb_up, bb_dn, bb_std = [], [], [], []
    for i in range(n):
        if i + 1 < BB_WIN:
            bb_mid.append(None); bb_up.append(None); bb_dn.append(None); bb_std.append(None)
        else:
            w = ratio[i - BB_WIN + 1:i + 1]
            m = mean(w); s = std(w)
            bb_mid.append(m); bb_up.append(m + BB_K * s)
            bb_dn.append(m - BB_K * s); bb_std.append(s)
    cur = ratio[-1]; cur_ma = ma250[-1]; cur_mid = bb_mid[-1]
    cur_up = bb_up[-1]; cur_dn = bb_dn[-1]; cur_std = bb_std[-1]
    rmin = min(ratio); rmax = max(ratio)
    pct = sum(1 for x in ratio if x <= cur) / n * 100
    dev_ma = (cur - cur_ma) / cur_ma * 100 if cur_ma else None
    dev_mid = (cur - cur_mid) / cur_mid * 100 if cur_mid else None
    z = (cur - cur_mid) / cur_std if (cur_mid and cur_std) else None
    ma_dir = (ma250[-1] - ma250[-21]) / ma250[-21] * 100 if (ma250[-1] and ma250[-21]) else None
    return {
        "dates": dates, "ratio": ratio, "ma250": ma250,
        "bb_mid": bb_mid, "bb_up": bb_up, "bb_dn": bb_dn,
        "g_norm": [x / gv[0] * 100 for x in gv],
        "v_norm": [x / vv[0] * 100 for x in vv],
        "stats": {
            "count": n, "start": dates[0], "end": dates[-1], "cur_ratio": cur,
            "cur_ma": cur_ma, "cur_mid": cur_mid, "cur_up": cur_up, "cur_dn": cur_dn,
            "rmin": rmin, "rmax": rmax, "pct": pct, "dev_ma": dev_ma,
            "dev_mid": dev_mid, "zscore": z, "ma_dir": ma_dir,
        },
    }


def write_json(path, g, v, label):
    try:
        D = compute(g, v)
        out = {"D": D, "at": datetime.datetime.now().isoformat()}
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        os.replace(tmp, path)
        s = D["stats"]
        print("[OK] %s: end=%s count=%d ratio=%.4f pct=%.1f%%"
              % (label, s["end"], s["count"], s["cur_ratio"], s["pct"]))
        return True
    except Exception as e:
        print("[FAIL] %s: %s" % (label, e))
        return False


# 每个分组按优先级尝试多个源，任一成功即采用
GROUPS = {
    "gv_data.json": {
        "label": "成长/价值",
        "sources": [("guozheng", "980080", "980081")],
    },
    "sz_data.json": {
        "label": "中证1000/沪深300",
        "sources": [("sina", "sh000852", "sh000300"),
                    ("guozheng", "000852", "000300")],
    },
}


def try_sources(spec):
    for kind, a, b in spec["sources"]:
        try:
            if kind == "guozheng":
                g, v = fetch_guozheng(a, b)
            elif kind == "sina":
                g, v = fetch_sina(a, b)
            else:
                continue
            return g, v
        except Exception as e:
            print("  源 %s 失败: %s" % (kind, e))
    return None, None


if __name__ == "__main__":
    for fn, spec in GROUPS.items():
        path = os.path.join(OUT_DIR, fn)
        g, v = try_sources(spec)
        if g is None:
            print("[SKIP] %s: 全部源失败 -> 保留旧文件" % spec["label"])
            continue
        write_json(path, g, v, spec["label"])
    print("完成。输出目录:", OUT_DIR)
