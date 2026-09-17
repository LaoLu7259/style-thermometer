# -*- coding: utf-8 -*-
"""
9:24 集合竞价实时抓取：对比 strategy_data.json 中的次日信号，判断 159915 是否触发买入
数据：新浪实时行情 hq.sinajs.cn/list=sz159915
输出：live_signal.json
"""
import json, os, urllib.request
from datetime import date, datetime

HEAD = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}

def fetch_realtime():
    url = "https://hq.sinajs.cn/list=sz159915"
    for _ in range(4):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=HEAD), timeout=20).read()
            s = raw.decode("gbk", "ignore")
            # var hq_str_sz159915="name,open,prev_close,current,high,low,..."
            eq = s.split('"')
            if len(eq) < 2:
                return None
            f = eq[1].split(",")
            return {"name": f[0], "open": float(f[1]), "prev_close": float(f[2]),
                    "current": float(f[3])}
        except Exception:
            import time; time.sleep(1.5)
    return None

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    today = date.today().isoformat()
    wd = date.today().weekday()  # Mon=0 .. Sat=5, Sun=6
    if wd >= 5:
        out = {"date": today, "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "open": None, "current": None, "prev_close": None,
               "signal_day": False, "triggered": False, "action": "非交易日",
               "msg": "今日为周末，非交易日，无需抓取实时行情。"}
        with open(os.path.join(here, "live_signal.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        print("周末，跳过实时抓取。")
        return
    # 读取信号
    sig_path = os.path.join(here, "strategy_data.json")
    signal = {}
    if os.path.exists(sig_path):
        signal = json.load(open(sig_path, encoding="utf-8")).get("signal", {})

    rt = fetch_realtime()
    out = {"date": today, "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "open": None, "current": None, "prev_close": None,
           "signal_day": False, "triggered": False, "action": "数据未获取", "msg": ""}

    if rt is None:
        out["msg"] = "实时行情获取失败（可能未到交易时间或网络问题）"
        out["action"] = "无法判断"
    else:
        out["open"] = rt["open"]; out["current"] = rt["current"]; out["prev_close"] = rt["prev_close"]
        ntd = signal.get("next_trading_day")
        out["signal_day"] = (ntd == today)
        if not out["signal_day"]:
            out["action"] = "今日非信号日"
            out["msg"] = "今日(%s)不是策略信号日（信号日=%s），无需操作。" % (today, ntd)
        else:
            cond = signal.get("buy_cond")
            thr = signal.get("threshold")
            if cond == "OPEN":
                out["triggered"] = True
                out["action"] = "执行买入"
                out["msg"] = "信号日(开盘即买)：开盘价 %.4f，按规则开盘买入。" % rt["open"]
            else:  # GAPUP
                triggered = rt["open"] > thr
                out["triggered"] = triggered
                if triggered:
                    out["action"] = "执行买入"
                    out["msg"] = "信号日(高开买入)：开盘价 %.4f > 门槛 %.4f，触发买入。" % (rt["open"], thr)
                else:
                    out["action"] = "未触发，今日不买"
                    out["msg"] = "信号日(高开买入)：开盘价 %.4f 未高于门槛 %.4f，今日不买。" % (rt["open"], thr)

    with open(os.path.join(here, "live_signal.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("已生成 live_signal.json:", out["action"], "|", out["msg"])

if __name__ == "__main__":
    main()
