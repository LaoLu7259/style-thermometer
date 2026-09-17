# -*- coding: utf-8 -*-
"""
159915 乖离率1.1 策略：信号 + 回测生成器
- 数据：新浪财经 sz159915 (日线) + sz399006 (创业板指，用于同期比较)
- 策略（创业板159915 乖离率1.1 原值）：
    年上腿：MA250 之上，连跌 >=1 天 -> 次日开盘买入；持有 5 日；收盘卖
    年下腿：MA250 之下，连跌 >=3 天 -> 次日高开(开盘>昨收)买入；持有 8 日；开盘卖
  （闸门/贯通为原策略附加项，此处先实现核心触发逻辑）
- 输出：strategy_data.json（日K线 + 买卖标记 + 回测统计 + 次日信号）
"""
import json, os, urllib.request
from datetime import date, timedelta

HEAD = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}

def fetch_sina(symbol, datalen=4000):
    url = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           "CN_MarketData.getKLineData?symbol=%s&scale=240&ma=no&datalen=%d" % (symbol, datalen))
    for _ in range(4):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=HEAD), timeout=30).read()
            arr = json.loads(raw.decode("gbk", "ignore"))
            out = {}
            for r in arr:
                d = r["day"][:10]
                out[d] = {"o": float(r["open"]), "c": float(r["close"]),
                          "h": float(r["high"]), "l": float(r["low"])}
            if out:
                return out
        except Exception:
            import time; time.sleep(1.5)
    raise RuntimeError("%s 抓取失败" % symbol)

def ma250(closes, i):
    if i + 1 < 250:
        return None
    return sum(closes[i-249:i+1]) / 250.0

def consecutive_down(closes, i):
    cd = 0
    j = i
    while j > 0 and closes[j] < closes[j-1]:
        cd += 1
        j -= 1
    return cd

def next_trading_day(d_str):
    d = date.fromisoformat(d_str)
    while True:
        d += timedelta(days=1)
        if d.weekday() < 5:  # 跳过周末（节假日近似）
            return d.isoformat()

def run_backtest(dates, o, c, h, l, ma):
    trades = []
    pos = None
    pending = None
    for i in range(len(dates)):
        m = ma[i]
        if m is None:
            continue
        leg = "UP" if c[i] > m else "DOWN"
        cd = consecutive_down(c, i)
        N = 1 if leg == "UP" else 3
        H = 5 if leg == "UP" else 8
        sell_rule = "CLOSE" if leg == "UP" else "OPEN"
        buy_cond = "OPEN" if leg == "UP" else "GAPUP"
        # 生成次日信号
        if cd >= N and i + 1 < len(dates):
            pending = {"date": dates[i+1], "leg": leg, "buy_cond": buy_cond,
                       "threshold": c[i], "hold": H, "sell_rule": sell_rule}
        # 执行信号
        if pending and pending["date"] == dates[i] and pos is None:
            do_buy = False
            entry_price = None
            if pending["buy_cond"] == "OPEN":
                entry_price = o[i]; do_buy = True
            else:
                if o[i] > pending["threshold"]:
                    entry_price = o[i]; do_buy = True
            if do_buy:
                pos = {"entry_idx": i, "entry_price": entry_price, "leg": pending["leg"],
                       "hold": pending["hold"], "sell_rule": pending["sell_rule"],
                       "entry_date": dates[i]}
            pending = None
        # 平仓
        if pos is not None:
            exit_idx = pos["entry_idx"] + pos["hold"]
            if i >= exit_idx:
                if i >= len(dates):
                    i2 = len(dates) - 1
                else:
                    i2 = i
                exit_price = c[i2] if pos["sell_rule"] == "CLOSE" else o[i2]
                ret = exit_price / pos["entry_price"] - 1.0
                trades.append({"entry_date": pos["entry_date"], "entry_price": round(pos["entry_price"], 4),
                               "exit_date": dates[i2], "exit_price": round(exit_price, 4),
                               "ret": ret, "leg": pos["leg"], "hold": pos["hold"]})
                pos = None
    return trades

def stats(trades, dates, c, idx_close_map):
    if not trades:
        return {}
    eq = 1.0
    peak = 1.0
    mdd = 0.0
    eq_curve = []
    wins = 0
    rets = []
    for t in trades:
        r = t["ret"]
        rets.append(r)
        if r > 0:
            wins += 1
        eq *= (1 + r)
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
        eq_curve.append(eq)
    total = eq - 1.0
    # 同期买入持有
    sd = trades[0]["entry_date"]; ed = trades[-1]["exit_date"]
    sd_i = dates.index(sd); ed_i = dates.index(ed)
    bh_159915 = c[ed_i] / c[sd_i] - 1.0
    bh_cyb = None
    if idx_close_map:
        ida = [d for d in idx_close_map.keys() if sd <= d <= ed]
        if ida:
            ic = [idx_close_map[d]["c"] for d in ida]
            bh_cyb = ic[-1] / ic[0] - 1.0
    return {
        "start": sd, "end": ed, "trade_count": len(trades),
        "win_rate": wins / len(trades),
        "avg_ret": sum(rets) / len(rets),
        "best": max(rets), "worst": min(rets),
        "total_return": total, "max_drawdown": mdd,
        "bh_159915": bh_159915, "bh_cyb": bh_cyb,
    }

def main():
    etf = fetch_sina("sz159915", 4000)
    try:
        idx = fetch_sina("sz399006", 4000)
    except Exception:
        idx = {}
    dates = sorted(etf.keys())
    o = [etf[d]["o"] for d in dates]
    c = [etf[d]["c"] for d in dates]
    h = [etf[d]["h"] for d in dates]
    l = [etf[d]["l"] for d in dates]
    ma = [ma250(c, i) for i in range(len(dates))]
    trades = run_backtest(dates, o, c, h, l, ma)
    st = stats(trades, dates, c, idx)

    buy_markers = [{"date": t["entry_date"], "price": t["entry_price"]} for t in trades]
    sell_markers = [{"date": t["exit_date"], "price": t["exit_price"]} for t in trades]

    # 次日信号（基于最后一根）
    last = len(dates) - 1
    m = ma[last]
    leg = "UP" if c[last] > m else "DOWN"
    cd = consecutive_down(c, last)
    N = 1 if leg == "UP" else 3
    H = 5 if leg == "UP" else 8
    sell_rule = "CLOSE" if leg == "UP" else "OPEN"
    buy_cond = "OPEN" if leg == "UP" else "GAPUP"
    is_signal = cd >= N
    ntd = next_trading_day(dates[last])
    if is_signal:
        msg = ("次日(下一交易日)为买入信号日｜%s腿｜%s%s｜门槛价 %.4f｜持有 %d 日｜%s卖"
               % (leg, buy_cond, ("(开盘>昨收才买)" if buy_cond == "GAPUP" else "(开盘即买)"),
                  c[last], H, ("收盘" if sell_rule == "CLOSE" else "开盘")))
    else:
        msg = ("次日非买入信号日｜当前%s腿｜已连跌 %d 天（需连跌 %d 天）" % (leg, cd, N))

    data = {
        "updated": dates[last],
        "kline": {"dates": dates, "open": o, "close": c, "high": h, "low": l},
        "markers": {"buy": buy_markers, "sell": sell_markers},
        "stats": st,
        "signal": {
            "as_of": dates[last], "leg": leg, "consecutive_down": cd,
            "next_trading_day": ntd, "is_signal_day": bool(is_signal),
            "buy_cond": buy_cond, "threshold": round(c[last], 4),
            "hold": H, "sell_rule": sell_rule, "msg": msg,
        },
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategy_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("已生成 strategy_data.json")
    print("最新日:", dates[last], "腿:", leg, "连跌:", cd, "信号日:", is_signal)
    print("交易次数:", st.get("trade_count"), "总收益: %.2f%%" % (st.get("total_return", 0)*100),
          "最大回撤: %.2f%%" % (st.get("max_drawdown", 0)*100))
    print("同期159915: %.2f%%  同期创业板指: %s"
          % (st.get("bh_159915", 0)*100,
             ("%.2f%%" % (st.get("bh_cyb", 0)*100)) if st.get("bh_cyb") is not None else "N/A"))

if __name__ == "__main__":
    main()
