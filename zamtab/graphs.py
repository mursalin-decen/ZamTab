"""Minitab-style graphs. Every builder takes a matplotlib Figure first."""
import logging
import numpy as np, pandas as pd, scipy.stats as st, matplotlib
from .stats_ops import ad_test, fmt, capability_stats, qm
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
matplotlib.rcParams.update({"font.family": ["Arial", "DejaVu Sans"], "font.size": 9, "axes.grid": True, "grid.color": "#d9d9d9", "grid.linewidth": .6,
    "axes.edgecolor": "#808080", "axes.titleweight": "bold", "axes.titlesize": 12, "figure.facecolor": "white", "axes.facecolor": "white", "axes.axisbelow": True})
FILL, EDGE, NAVY, RED, DOT = "#7fb2e5", "#1f4e79", "#1f3d6b", "#d62728", "#3465a4"
isnum = lambda s: pd.api.types.is_numeric_dtype(s)

def panel(fig, info=None, title=None):
    if info:
        gs = fig.add_gridspec(1, 2, width_ratios=[4.3, 1]); ax = fig.add_subplot(gs[0]); ia = fig.add_subplot(gs[1]); ia.axis("off"); ia.grid(False)
        ia.text(0, .96, info, va="top", ha="left", fontsize=8, family="DejaVu Sans", linespacing=1.5, bbox=dict(boxstyle="square", fc="white", ec="#999"))
    else: ax = fig.add_subplot(111)
    if title: ax.set_title(title)
    return ax

def histogram(fig, df, x, fit=True):
    v = df[x].dropna(); info = f"Normal\nMean   {fmt(v.mean())}\nStDev  {fmt(v.std())}\nN      {len(v)}" if fit else None
    ax = panel(fig, info, f"Histogram of {x}" + ("\nNormal" if fit else "")); c, e, _ = ax.hist(v, bins="auto", color=FILL, edgecolor=EDGE, linewidth=.9)
    if fit and v.std() > 0: xs = np.linspace(e[0], e[-1], 200); ax.plot(xs, st.norm.pdf(xs, v.mean(), v.std()) * len(v) * (e[1] - e[0]), color=NAVY, lw=1.8)
    ax.set(xlabel=x, ylabel="Frequency")

def boxplot(fig, df, y, by=None):
    ax = panel(fig, None, f"Boxplot of {y}" + (f" by {by}" if by else ""))
    groups = [(str(k), g[y].dropna().values) for k, g in df.groupby(by)][:20] if by else [(y, df[y].dropna().values)]
    bp = ax.boxplot([g for _, g in groups], patch_artist=True, flierprops=dict(marker="*", mfc="k", ms=7), medianprops=dict(color="k"), widths=.5)
    for b in bp["boxes"]: b.set(facecolor=FILL, edgecolor="k")
    ax.plot(range(1, len(groups) + 1), [g.mean() for _, g in groups], "o", mfc="white", mec="k", ms=7); ax.plot(range(1, len(groups) + 1), [g.mean() for _, g in groups], "+", c="k", ms=7)
    ax.set_xticks(range(1, len(groups) + 1)); ax.set_xticklabels([k for k, _ in groups]); ax.set(ylabel=y, xlabel=by or "")

def scatter(fig, df, y, x):
    d = df[list(dict.fromkeys([x, y]))].dropna(); ax = panel(fig, None, f"Scatterplot of {y} vs {x}"); ax.scatter(d[x], d[y], s=28, facecolors="none", edgecolors=DOT, linewidths=1.2); ax.set(xlabel=x, ylabel=y)

def fitted_line(fig, df, y, x):
    d = df[list(dict.fromkeys([x, y]))].dropna(); lr = st.linregress(d[x], d[y]); n = len(d); r2 = lr.rvalue ** 2; s = np.sqrt(((d[y] - lr.intercept - lr.slope * d[x]) ** 2).sum() / (n - 2))
    info = f"S        {s:.5g}\nR-Sq     {r2*100:.1f}%\nR-Sq(adj) {(1-(1-r2)*(n-1)/(n-2))*100:.1f}%"
    ax = panel(fig, info, f"Fitted Line Plot\n{y} = {lr.intercept:.5g} {'+' if lr.slope >= 0 else '-'} {abs(lr.slope):.5g} {x}")
    ax.scatter(d[x], d[y], s=28, facecolors="none", edgecolors=DOT, linewidths=1.2); xs = np.array([d[x].min(), d[x].max()]); ax.plot(xs, lr.intercept + lr.slope * xs, color=RED, lw=1.6); ax.set(xlabel=x, ylabel=y)

def dotplot(fig, df, x):
    v = df[x].dropna().values; ax = panel(fig, None, f"Dotplot of {x}"); c, e = np.histogram(v, bins=min(40, max(10, len(v) // 2))); ctr = (e[:-1] + e[1:]) / 2
    for xc, k in zip(ctr, c): ax.scatter([xc] * k, range(1, k + 1), s=22, c=DOT)
    ax.set(xlabel=x, yticks=[]); ax.grid(False)

def prob_plot(fig, df, x):
    v = np.sort(df[x].dropna().values); n = len(v); a, p = ad_test(v); pos = (np.arange(1, n + 1) - .3) / (n + .4); z = st.norm.ppf(pos)
    ax = panel(fig, f"Mean   {fmt(v.mean())}\nStDev  {fmt(v.std(ddof=1))}\nN      {n}\nAD     {a:.3f}\nP-Value {p:.3f}", f"Probability Plot of {x}\nNormal")
    ax.plot(v, z, "o", mfc="none", mec=DOT, ms=5); zz = np.linspace(z.min() - .3, z.max() + .3, 50); mu, sd = v.mean(), v.std(ddof=1); ax.plot(mu + sd * zz, zz, color=RED, lw=1.5)
    se = sd * np.sqrt((1 + zz ** 2 / 2) / n) * 1.96; ax.plot(mu + sd * zz - se, zz, "--", c=RED, lw=.9); ax.plot(mu + sd * zz + se, zz, "--", c=RED, lw=.9)
    pc = [1, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99]; ax.set_yticks(st.norm.ppf(np.array(pc) / 100)); ax.set_yticklabels(pc); ax.set(xlabel=x, ylabel="Percent")

def ecdf(fig, df, x):
    v = np.sort(df[x].dropna().values); ax = panel(fig, None, f"Empirical CDF of {x}\nNormal"); ax.step(v, np.arange(1, len(v) + 1) / len(v) * 100, where="post", color=DOT)
    xs = np.linspace(v.min(), v.max(), 200); ax.plot(xs, st.norm.cdf(xs, v.mean(), v.std()) * 100, color=RED); ax.set(xlabel=x, ylabel="Percent")

def interval(fig, df, y, by):
    ax = panel(fig, None, f"Interval Plot of {y} by {by}\n95% CI for the Mean"); ks, ms, es = [], [], []
    for k, g in df.groupby(by):
        g = g[y].dropna()
        if len(g) > 1: ks.append(str(k)); ms.append(g.mean()); es.append(st.t.ppf(.975, len(g) - 1) * g.sem())
    ax.errorbar(ks, ms, yerr=es, fmt="o", capsize=7, c=DOT, mfc=DOT); ax.plot(ks, ms, c="#999", lw=.8, zorder=0); ax.set(xlabel=by, ylabel=y)

def ivp(fig, df, y, by=None):
    ax = panel(fig, None, f"Individual Value Plot of {y}" + (f" vs {by}" if by else ""))
    groups = [(str(k), g[y].dropna().values) for k, g in df.groupby(by)] if by else [(y, df[y].dropna().values)]; r = np.random.RandomState(0)
    for i, (k, g) in enumerate(groups, 1): ax.plot(i + r.uniform(-.12, .12, len(g)), g, "o", mfc="none", mec=DOT, ms=5)
    ax.set_xticks(range(1, len(groups) + 1)); ax.set_xticklabels([k for k, _ in groups]); ax.set(ylabel=y, xlabel=by or "")

def bar(fig, df, x):
    vc = df[x].value_counts().head(20); ax = panel(fig, None, f"Chart of {x}"); ax.bar(vc.index.astype(str), vc.values, color=FILL, edgecolor=EDGE); ax.set(xlabel=x, ylabel="Count")

def pie(fig, df, x):
    vc = df[x].value_counts().head(20); ax = panel(fig, None, f"Pie Chart of {x}"); ax.grid(False)
    ax.pie(vc.values, labels=vc.index.astype(str), autopct="%1.1f%%", wedgeprops=dict(edgecolor="white")); ax.set_aspect("equal")

def pareto(fig, df, x):
    vc = df[x].value_counts().head(20); ax = panel(fig, None, f"Pareto Chart of {x}"); ax.bar(vc.index.astype(str), vc.values, color=FILL, edgecolor=EDGE)
    a2 = ax.twinx(); a2.plot(range(len(vc)), vc.cumsum() / vc.sum() * 100, "o-", c=RED); a2.set_ylim(0, 105); a2.grid(False); ax.set(xlabel=x, ylabel="Count"); a2.set_ylabel("Percent")

def timeseries(fig, df, y):
    v = df[y].dropna(); ax = panel(fig, None, f"Time Series Plot of {y}"); ax.plot(range(1, len(v) + 1), v.values, "o-", c=DOT, ms=4, lw=1); ax.set(xlabel="Index", ylabel=y)

def run_chart(fig, df, x):
    v = df[x].dropna(); ax = panel(fig, None, f"Run Chart of {x}"); ax.plot(range(1, len(v) + 1), v.values, "o-", c=DOT, ms=4, lw=1); ax.axhline(v.median(), c="g", lw=1.3)
    ax.set(xlabel="Observation", ylabel=x); ax.text(1.0, v.median(), f" Median={v.median():.4g}", transform=ax.get_yaxis_transform(), va="bottom", color="g")

def matrix_plot(fig, df, vars):
    vars = vars[:5]; k = len(vars); axs = fig.subplots(k, k, squeeze=False); fig.suptitle("Matrix Plot of " + ", ".join(vars), fontweight="bold")
    for i, a in enumerate(vars):
        for j, b in enumerate(vars):
            ax = axs[i][j]; ax.grid(False)
            if i == j: ax.text(.5, .5, a, ha="center", va="center", fontweight="bold", transform=ax.transAxes); ax.set_xticks([]); ax.set_yticks([])
            else: ax.scatter(df[b], df[a], s=8, facecolors="none", edgecolors=DOT, linewidths=.8); ax.tick_params(labelsize=6)

def graphical_summary(fig, df, x):
    v = df[x].dropna(); n = len(v); a, p = ad_test(v); gs = fig.add_gridspec(3, 2, width_ratios=[1.7, 1], height_ratios=[3, 1, 1.1])
    fig.suptitle(f"Summary for {x}", fontweight="bold"); ax = fig.add_subplot(gs[0, 0]); c, e, _ = ax.hist(v, bins="auto", color=FILL, edgecolor=EDGE)
    xs = np.linspace(e[0], e[-1], 200); ax.plot(xs, st.norm.pdf(xs, v.mean(), v.std()) * n * (e[1] - e[0]), c=NAVY); ax.set_ylabel("Frequency"); ax.tick_params(labelbottom=False)
    bx = fig.add_subplot(gs[1, 0], sharex=ax); bp = bx.boxplot(v, vert=False, patch_artist=True, flierprops=dict(marker="*", mfc="k")); bp["boxes"][0].set(facecolor=FILL); bx.set_yticks([]); bx.tick_params(labelbottom=False); bx.grid(False)
    cx = fig.add_subplot(gs[2, 0], sharex=ax); lo, hi = st.t.interval(.95, n - 1, v.mean(), v.sem()); s = np.sort(v.values); j = max(int(np.floor(n / 2 - .98 * np.sqrt(n))), 0); k = min(n - 1 - j, n - 1)
    cx.errorbar([v.mean()], [1], xerr=[[v.mean() - lo], [hi - v.mean()]], fmt="o", c=DOT, capsize=5); cx.errorbar([v.median()], [0], xerr=[[v.median() - s[j]], [s[k] - v.median()]], fmt="o", c=DOT, capsize=5)
    cx.set_yticks([0, 1]); cx.set_yticklabels(["Median", "Mean"]); cx.set_ylim(-.7, 1.7); cx.set_xlabel(x); cx.grid(False)
    ts = fig.add_subplot(gs[:, 1]); ts.axis("off"); ts.grid(False); sk, ku = st.skew(v, bias=False), st.kurtosis(v, bias=False); sl, sh = np.sqrt((n - 1) * v.var() / st.chi2.ppf(.975, n - 1)), np.sqrt((n - 1) * v.var() / st.chi2.ppf(.025, n - 1))
    txt = (f"Anderson-Darling Normality Test\nA-Squared  {a:.2f}\nP-Value    {p:.3f}\n\nMean       {fmt(v.mean())}\nStDev      {fmt(v.std())}\nVariance   {fmt(v.var())}\nSkewness   {sk:.4g}\nKurtosis   {ku:.4g}\nN          {n}\n\n"
           f"Minimum    {fmt(v.min())}\n1st Quartile {fmt(qm(v, .25))}\nMedian     {fmt(v.median())}\n3rd Quartile {fmt(qm(v, .75))}\nMaximum    {fmt(v.max())}\n\n95% CI for Mean\n  {lo:.5g}  {hi:.5g}\n95% CI for Median\n  {s[j]:.5g}  {s[k]:.5g}\n95% CI for StDev\n  {sl:.5g}  {sh:.5g}")
    ts.text(0, 1, txt, va="top", fontsize=8, family="DejaVu Sans", linespacing=1.35)

def imr_chart(fig, df, x):
    a = df[x].dropna().values; mr = np.abs(np.diff(a)); mrb = mr.mean(); cl = a.mean(); u, l = cl + 2.66 * mrb, cl - 2.66 * mrb; ax, bx = fig.subplots(2, 1); fig.suptitle(f"I-MR Chart of {x}", fontweight="bold")
    ax.plot(range(1, len(a) + 1), a, "o-", c=DOT, ms=4, lw=1); bad = np.where((a > u) | (a < l))[0]; ax.plot(bad + 1, a[bad], "s", c=RED, ms=7, mfc="none")
    for val, c, t in ((cl, "g", "X̄"), (u, RED, "UCL"), (l, RED, "LCL")): ax.axhline(val, c=c, ls="-" if t == "X̄" else "--", lw=1); ax.text(1.0, val, f" {t}={val:.4g}", transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=c)
    ax.set_ylabel("Individual Value"); bx.plot(range(2, len(a) + 1), mr, "o-", c=DOT, ms=4, lw=1)
    for val, c, t in ((mrb, "g", "MR̄"), (3.267 * mrb, RED, "UCL"), (0, RED, "LCL")): bx.axhline(val, c=c, ls="-" if t == "MR̄" else "--", lw=1); bx.text(1.0, val, f" {t}={val:.4g}", transform=bx.get_yaxis_transform(), va="center", fontsize=8, color=c)
    bx.set(ylabel="Moving Range", xlabel="Observation")

def capability(fig, df, x, lsl=None, usl=None, size=1):
    v = df[x].dropna(); mu, so, sw, (cp, cpl, cpu, cpk), (pp, ppl, ppu, ppk), pw, po = capability_stats(v, lsl, usl, size or 1); r = lambda z: "*" if np.isnan(z) else f"{z:.2f}"
    info = (f"Process Data\nLSL    {fmt(lsl)}\nTarget *\nUSL    {fmt(usl)}\nMean   {mu:.5g}\nN      {len(v)}\nStDev(W) {sw:.4g}\nStDev(O) {so:.4g}\n\nPotential (Within)\nCp   {r(cp)}\nCPL  {r(cpl)}\nCPU  {r(cpu)}\nCpk  {r(cpk)}\n\nOverall\nPp   {r(pp)}\nPPL  {r(ppl)}\nPPU  {r(ppu)}\nPpk  {r(ppk)}")
    ax = panel(fig, info, f"Process Capability Report for {x}"); c, e, _ = ax.hist(v, bins="auto", density=True, color=FILL, edgecolor=EDGE)
    lo = min([v.min()] + ([lsl] if lsl is not None else [])); hi = max([v.max()] + ([usl] if usl is not None else [])); xs = np.linspace(lo - sw, hi + sw, 300)
    ax.plot(xs, st.norm.pdf(xs, mu, sw), c=NAVY, lw=1.6, label="Within"); ax.plot(xs, st.norm.pdf(xs, mu, so), c=RED, ls="--", lw=1.6, label="Overall")
    for val, t in ((lsl, "LSL"), (usl, "USL")):
        if val is not None: ax.axvline(val, c="r"); ax.text(val, ax.get_ylim()[1] * .97, t, color="r", ha="center", fontweight="bold")
    ax.legend(loc="upper left", fontsize=8); ax.set(xlabel=x, ylabel="Density", yticks=[])

def residual_plots(fig, df, y, x):
    d = df[[y] + x].dropna(); X = np.column_stack([np.ones(len(d))] + [d[c].values for c in x]); b, *_ = np.linalg.lstsq(X, d[y].values, rcond=None); fit = X @ b; r = d[y].values - fit
    a = fig.subplots(2, 2); fig.suptitle(f"Residual Plots for {y}", fontweight="bold"); z = st.norm.ppf((st.rankdata(r) - .375) / (len(r) + .25))
    a[0, 0].plot(r, z, "o", mfc="none", mec=DOT, ms=4); a[0, 0].set(title="Normal Probability Plot", xlabel="Residual", ylabel="Normal score")
    a[0, 1].plot(fit, r, "o", mfc="none", mec=DOT, ms=4); a[0, 1].axhline(0, c="k", lw=.8); a[0, 1].set(title="Versus Fits", xlabel="Fitted Value", ylabel="Residual")
    a[1, 0].hist(r, bins="auto", color=FILL, edgecolor=EDGE); a[1, 0].set(title="Histogram", xlabel="Residual", ylabel="Frequency")
    a[1, 1].plot(range(1, len(r) + 1), r, "o-", c=DOT, ms=3, lw=.8); a[1, 1].axhline(0, c="k", lw=.8); a[1, 1].set(title="Versus Order", xlabel="Observation Order", ylabel="Residual")
    for q in a.flat: q.title.set_fontsize(9)

def plan(df, x, y=None):
    """Every graph that fits the chosen columns: [(title, fn(fig))]."""
    jobs = []
    if df is None or x not in df: return jobs
    y = y if y in df else None
    def add(t, f, *a, **k): jobs.append((t, lambda fig: f(fig, df, *a, **k)))
    def single(c):
        if isnum(df[c]):
            if df[c].notna().sum() >= 4:
                add(f"Histogram of {c}", histogram, c); add(f"Boxplot of {c}", boxplot, c); add(f"Probability Plot of {c}", prob_plot, c); add(f"Dotplot of {c}", dotplot, c)
                add(f"Time Series Plot of {c}", timeseries, c); add(f"Empirical CDF of {c}", ecdf, c); add(f"Summary for {c}", graphical_summary, c); add(f"I-MR Chart of {c}", imr_chart, c)
        else: add(f"Chart of {c}", bar, c); add(f"Pareto Chart of {c}", pareto, c); add(f"Pie Chart of {c}", pie, c)
    if y:
        nx, ny = isnum(df[x]), isnum(df[y])
        if nx and ny: add(f"Scatterplot of {y} vs {x}", scatter, y, x); add(f"Fitted Line Plot", fitted_line, y, x); add("Residual Plots", residual_plots, y, [x])
        elif not nx and ny: add(f"Boxplot of {y} by {x}", boxplot, y, by=x); add(f"Interval Plot of {y} by {x}", interval, y, x); add(f"Individual Value Plot", ivp, y, by=x)
        elif nx and not ny: add(f"Boxplot of {x} by {y}", boxplot, x, by=y); add(f"Interval Plot of {x} by {y}", interval, x, y)
    single(x)
    if y: single(y)
    nums = [c for c in df if isnum(df[c])]
    if len(nums) >= 2: add("Matrix Plot", matrix_plot, nums)
    return jobs
