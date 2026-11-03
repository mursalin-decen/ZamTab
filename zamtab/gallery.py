"""Minitab 17 graph gallery variants (Simple / With Groups / With Fit / Multiple ...), extra graph types and Labels/Scale decoration."""
import numpy as np, pandas as pd, scipy.stats as st
from .graphs import FILL, EDGE, NAVY, RED, DOT, panel, isnum
from .stats_ops import ad_test, fmt, xbar_r_data, attr_data, dist_obj, DISTS

PAL = ["#e41a1c", "#377eb8", "#4daf4a", "#222222", "#ff7f00", "#984ea3", "#a65628", "#f781bf"]; MK = ["o", "s", "D", "x", "^", "v", "P", "*"]
def _side(fig):
    gs = fig.add_gridspec(1, 2, width_ratios=[5, 1]); ax = fig.add_subplot(gs[0]); sd = fig.add_subplot(gs[1]); sd.axis("off"); sd.grid(False); return ax, sd
def _leg(side, ax, title):
    h, l = ax.get_legend_handles_labels(); side.legend(h, l, title=title, loc="upper left", fontsize=8, title_fontsize=8, frameon=True)
def _grp(df, by, col): return [(str(k), g) for k, g in df.groupby(by)][:8]
def _series(df, ys, by):
    if by: return [(k, g[ys[0]].dropna().values) for k, g in _grp(df, by, ys[0])]
    return [(y, df[y].dropna().values) for y in ys]

def scatter_v(fig, df, y, x, kind, by=None):
    grp = by and "Groups" in kind; ax, sd = _side(fig) if grp else (fig.add_subplot(111), None)
    ax.set_title(f"Scatterplot of {y} vs {x}" + (f"\n{by}" if False else "")); ax.set(xlabel=x, ylabel=y)
    parts = _grp(df, by, y) if grp else [(None, df)]
    for i, (k, g) in enumerate(parts):
        d = g[list(dict.fromkeys([x, y]))].dropna(); c = PAL[i] if grp else DOT; m = MK[i] if grp else "o"
        ax.scatter(d[x], d[y], s=30, marker=m, color=c, facecolors="none" if m in "os" and not grp else c, label=k, linewidths=1.1)
        if "Connect" in kind: ax.plot(d[x], d[y], "-", color=c, lw=1)
        if "Regression" in kind and len(d) > 2: lr = st.linregress(d[x], d[y]); xs = np.array([d[x].min(), d[x].max()]); ax.plot(xs, lr.intercept + lr.slope * xs, color=c if grp else RED, lw=1.6)
    if grp: _leg(sd, ax, by)

def hist_v(fig, df, v, kind, by=None):
    from .graphs import histogram
    if not (by and "Groups" in kind): return histogram(fig, df, v, fit="Fit" in kind)
    ax, sd = _side(fig); ax.set_title(f"Histogram of {v}" + ("\nNormal " if "Fit" in kind else "")); edges = np.histogram_bin_edges(df[v].dropna(), bins="auto")
    for i, (k, g) in enumerate(_grp(df, by, v)):
        x = g[v].dropna()
        if "Outline" in kind or "Fit" in kind: ax.hist(x, bins=edges, histtype="step", color=PAL[i], lw=1.6, label=k)
        else: ax.hist(x, bins=edges, color=PAL[i], alpha=.6, label=k)
        if "Fit" in kind and x.std() > 0: xs = np.linspace(edges[0], edges[-1], 200); ax.plot(xs, st.norm.pdf(xs, x.mean(), x.std()) * len(x) * (edges[1] - edges[0]), color=PAL[i], lw=1.2, ls="--")
    ax.set(xlabel=v, ylabel="Frequency"); _leg(sd, ax, by)

def box_v(fig, df, ys, by=None):
    ax = fig.add_subplot(111); s = _series(df, ys, by); ax.set_title("Boxplot of " + (f"{ys[0]} by {by}" if by else (ys[0] if len(ys) == 1 else ", ".join(ys))))
    bp = ax.boxplot([v for _, v in s], patch_artist=True, flierprops=dict(marker="*", mfc="k", ms=7), medianprops=dict(color="k"), widths=.5)
    for b in bp["boxes"]: b.set(facecolor=FILL, edgecolor="k")
    ax.plot(range(1, len(s) + 1), [v.mean() for _, v in s], "o", mfc="white", mec="k", ms=7); ax.plot(range(1, len(s) + 1), [v.mean() for _, v in s], "+", c="k", ms=7)
    ax.set_xticks(range(1, len(s) + 1)); ax.set_xticklabels([k for k, _ in s]); ax.set(xlabel=by or "", ylabel=ys[0] if (by or len(ys) == 1) else "Data")

def dot_v(fig, df, ys, by=None):
    ax = fig.add_subplot(111); s = _series(df, ys, by); ax.set_title("Dotplot of " + (f"{ys[0]} by {by}" if by else ", ".join(ys))); allv = np.concatenate([v for _, v in s]); edges = np.histogram_bin_edges(allv, bins=40); base = 0; ticks = []
    for i, (k, v) in enumerate(s):
        c, _ = np.histogram(v, bins=edges); ctr = (edges[:-1] + edges[1:]) / 2
        for xc, n in zip(ctr, c):
            if n: ax.scatter([xc] * n, base + np.arange(1, n + 1) * .9, s=16, color=PAL[i % 8] if by else DOT)
        ticks.append((base + max(c.max(), 1) * .45, k)); base += max(c.max(), 1) * .9 + 2
    ax.set_yticks([t for t, _ in ticks]); ax.set_yticklabels([k for _, k in ticks]); ax.set_xlabel(ys[0] if by else "Data"); ax.grid(False)

def ivp_v(fig, df, ys, by=None):
    ax = fig.add_subplot(111); s = _series(df, ys, by); r = np.random.RandomState(0); ax.set_title("Individual Value Plot of " + (f"{ys[0]} vs {by}" if by else ", ".join(ys)))
    for i, (k, v) in enumerate(s, 1): ax.plot(i + r.uniform(-.1, .1, len(v)), v, "o", mfc=DOT, mec=DOT, ms=4, alpha=.8)
    ax.set_xticks(range(1, len(s) + 1)); ax.set_xticklabels([k for k, _ in s]); ax.set(xlabel=by or "", ylabel=ys[0] if by else "Data")

def interval_v(fig, df, ys, by=None, conf=95.0):
    ax = fig.add_subplot(111); s = _series(df, ys, by); ax.set_title("Interval Plot of " + (f"{ys[0]} vs {by}" if by else ", ".join(ys)) + f"\n{conf:g}% CI for the Mean"); xs, m, e = [], [], []
    for k, v in s:
        if len(v) > 1: xs.append(k); m.append(v.mean()); e.append(st.t.ppf(.5 + conf / 200, len(v) - 1) * st.sem(v))
    ax.errorbar(range(len(xs)), m, yerr=e, fmt="o", capsize=8, color=DOT, mfc=DOT, ms=6); ax.plot(range(len(xs)), m, c="#999", lw=.8, zorder=0)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs); ax.set(xlabel=by or "", ylabel=ys[0] if by else "Data")

def bar_v(fig, df, cats, kind, func=None, yv=None):
    ax = fig.add_subplot(111)
    def val(g): return g.size() if not func else getattr(g[yv], {"Mean": "mean", "Sum": "sum", "Median": "median", "StDev": "std", "Minimum": "min", "Maximum": "max", "Count": "count"}[func])()
    lab = f"{func}({yv})" if func else "Count"
    if len(cats) == 1 or "Simple" in kind: t = val(df.groupby(cats[0])); ax.bar(t.index.astype(str), t.values, color=FILL, edgecolor=EDGE); ax.set_title("Chart of " + (f"{func}({yv}) vs {cats[0]}" if func else cats[0])); ax.set(xlabel=cats[0], ylabel=lab)
    else:
        t = val(df.groupby(cats[:2])).unstack(fill_value=0); n = len(t.columns); w = .8 / (1 if "Stack" in kind else n); bot = np.zeros(len(t)); ax2, sd = None, None
        fig.clf(); ax, sd = _side(fig)
        for i, c in enumerate(t.columns):
            if "Stack" in kind: ax.bar(range(len(t)), t[c].values, bottom=bot, width=.7, color=PAL[i % 8], edgecolor="k", label=str(c)); bot += t[c].values
            else: ax.bar(np.arange(len(t)) + (i - (n - 1) / 2) * w, t[c].values, width=w, color=PAL[i % 8], edgecolor="k", label=str(c))
        ax.set_xticks(range(len(t))); ax.set_xticklabels(t.index.astype(str)); ax.set(xlabel=cats[0], ylabel=lab); ax.set_title(f"Chart of {cats[0]}, {cats[1]}"); _leg(sd, ax, cats[1])

def ts_v(fig, df, ys, kind):
    ax, sd = _side(fig) if len(ys) > 1 else (fig.add_subplot(111), None); ax.set_title("Time Series Plot of " + ", ".join(ys))
    for i, y in enumerate(ys): v = df[y].dropna(); ax.plot(range(1, len(v) + 1), v.values, marker=MK[i] if len(ys) > 1 else "o", ms=4, lw=1, color=PAL[i] if len(ys) > 1 else DOT, label=y)
    ax.set(xlabel="Index", ylabel=ys[0] if len(ys) == 1 else "Data")
    if sd is not None: _leg(sd, ax, "Variable")

def line_v(fig, df, ys, x, area=False):
    ax, sd = _side(fig) if len(ys) > 1 else (fig.add_subplot(111), None); ax.set_title(("Area Graph of " if area else "Scatterplot of ") + ", ".join(ys) + f" vs {x}")
    for i, y in enumerate(ys):
        d = df[list(dict.fromkeys([x, y]))].dropna().sort_values(x); c = PAL[i] if len(ys) > 1 else DOT
        if area: ax.fill_between(d[x], d[y], color=c, alpha=.45, label=y); ax.plot(d[x], d[y], color=c, lw=1)
        else: ax.plot(d[x], d[y], "-", color=c, lw=1.4, label=y)
    ax.set(xlabel=x, ylabel=ys[0] if len(ys) == 1 else "Data")
    if sd is not None: _leg(sd, ax, "Variable")

def bubble(fig, df, y, x, size):
    d = df[list(dict.fromkeys([x, y, size]))].dropna(); ax = fig.add_subplot(111); s = d[size]; ax.scatter(d[x], d[y], s=40 + 600 * (s - s.min()) / ((s.max() - s.min()) or 1), facecolors="none", edgecolors=DOT, linewidths=1.2); ax.set(xlabel=x, ylabel=y, title=f"Bubble Plot of {y} vs {x}\nSize: {size}")

def marginal(fig, df, y, x, kind):
    d = df[list(dict.fromkeys([x, y]))].dropna(); gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4], hspace=.04, wspace=.04); ax = fig.add_subplot(gs[1, 0]); tx = fig.add_subplot(gs[0, 0], sharex=ax); ry = fig.add_subplot(gs[1, 1], sharey=ax)
    ax.scatter(d[x], d[y], s=26, facecolors="none", edgecolors=DOT, linewidths=1.1); ax.set(xlabel=x, ylabel=y); fig.suptitle(f"Marginal Plot of {y} vs {x}", fontweight="bold")
    for a, v, o in ((tx, d[x], "vertical"), (ry, d[y], "horizontal")):
        a.grid(False)
        if "Hist" in kind: a.hist(v, bins="auto", color=FILL, edgecolor=EDGE, orientation=o)
        elif "Box" in kind: bp = a.boxplot(v, vert=o == "vertical" and False or o != "vertical", patch_artist=True); bp["boxes"][0].set(facecolor=FILL)
        else: a.plot(v, np.zeros(len(v)), "o", mfc=DOT, mec=DOT, ms=3) if o == "vertical" else a.plot(np.zeros(len(v)), v, "o", mfc=DOT, mec=DOT, ms=3)
        a.tick_params(labelbottom=False, labelleft=False)

def surface3d(fig, df, z, y, x, mode):
    d = df[[x, y, z]].dropna()
    if mode == "3D Scatterplot": ax = fig.add_subplot(111, projection="3d"); ax.scatter(d[x], d[y], d[z], facecolors="none", edgecolors=DOT); ax.set(xlabel=x, ylabel=y, zlabel=z, title=f"3D Scatterplot of {z} vs {y} vs {x}")
    elif mode == "3D Surface Plot": ax = fig.add_subplot(111, projection="3d"); ax.plot_trisurf(d[x], d[y], d[z], cmap="Blues", edgecolor="#555", linewidth=.2); ax.set(xlabel=x, ylabel=y, zlabel=z, title=f"Surface Plot of {z} vs {y}, {x}")
    else: ax = fig.add_subplot(111); c = ax.tricontourf(d[x], d[y], d[z], levels=8, cmap="Blues"); fig.colorbar(c, label=z); ax.set(xlabel=x, ylabel=y, title=f"Contour Plot of {z} vs {y}, {x}")

def matrix_v(fig, df, ys, xs=None):
    from .graphs import matrix_plot
    if not xs: return matrix_plot(fig, df, ys)
    a = fig.subplots(len(ys), len(xs), squeeze=False); fig.suptitle("Matrix Plot of " + ", ".join(ys) + " vs " + ", ".join(xs), fontweight="bold")
    for i, y in enumerate(ys):
        for j, x in enumerate(xs): a[i][j].scatter(df[x], df[y], s=8, facecolors="none", edgecolors=DOT, lw=.8); a[i][j].tick_params(labelsize=6); a[i][j].set_xlabel(x, fontsize=7); a[i][j].set_ylabel(y, fontsize=7)

def prob_v(fig, df, vars, dist="Normal"):
    ax, sd = _side(fig); ax.set_title(f"Probability Plot of {', '.join(vars)}\n{dist} - 95% CI" if len(vars) == 1 else f"Probability Plot of {', '.join(vars)}\n{dist}"); info = []
    for i, c in enumerate(vars):
        v = np.sort(df[c].dropna().values); n = len(v); p = (np.arange(1, n + 1) - .3) / (n + .4); col = PAL[i] if len(vars) > 1 else DOT
        if dist == "Normal": z = st.norm.ppf(p); mu, s_ = v.mean(), v.std(ddof=1); a_, pp = ad_test(v); lx = lambda zz: mu + s_ * zz; ax.plot(v, z, "o", mfc="none", mec=col, ms=5); zz = np.linspace(z.min() - .3, z.max() + .3, 50); ax.plot(lx(zz), zz, color=col)
        elif dist == "Lognormal": lv = np.log(v); z = st.norm.ppf(p); mu, s_ = lv.mean(), lv.std(ddof=1); ax.plot(v, z, "o", mfc="none", mec=col, ms=5); zz = np.linspace(z.min() - .3, z.max() + .3, 50); ax.plot(np.exp(mu + s_ * zz), zz, color=col); ax.set_xscale("log"); a_, pp = ad_test(lv)
        elif dist == "Exponential": z = -np.log(1 - p); sc = v.mean(); ax.plot(v, z, "o", mfc="none", mec=col, ms=5); zz = np.linspace(0, z.max() + .3, 50); ax.plot(zz * sc, zz, color=col); a_ = pp = None
        else: z = np.log(-np.log(1 - p)); sh, _, sc = st.weibull_min.fit(v, floc=0); ax.plot(v, z, "o", mfc="none", mec=col, ms=5); xs = np.linspace(v.min() * .9, v.max() * 1.1, 50); ax.plot(xs, shape_line(xs, sh, sc), color=col); ax.set_xscale("log"); a_ = pp = None
        info.append((c, n, v, a_, pp, z))
        if len(vars) > 1: ax.plot([], [], "o", mfc="none", mec=col, label=c)
    pc = np.array([1, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99]) / 100; z0 = info[0][5]
    tr = {"Normal": st.norm.ppf, "Lognormal": st.norm.ppf, "Exponential": lambda q: -np.log(1 - q), "Weibull": lambda q: np.log(-np.log(1 - q))}[dist]; ax.set_yticks(tr(pc)); ax.set_yticklabels([f"{int(q*100)}" for q in pc]); ax.set(xlabel=", ".join(vars) if len(vars) == 1 else "Data", ylabel="Percent")
    if len(vars) == 1:
        c, n, v, a_, pp, _ = info[0]; txt = f"Mean   {fmt(v.mean())}\nStDev  {fmt(v.std(ddof=1))}\nN      {n}" + (f"\nAD     {a_:.3f}\nP-Value {pp:.3f}" if a_ is not None else ""); sd.text(0, .96, txt, va="top", fontsize=8, family="DejaVu Sans", linespacing=1.5, bbox=dict(boxstyle="square", fc="white", ec="#999"))
    else: _leg(sd, ax, "Variable")
def shape_line(xs, sh, sc): return np.log(-np.log(1 - (1 - np.exp(-(xs / sc) ** sh))))

def ecdf_v(fig, df, vars, dist=None):
    ax, sd = _side(fig) if len(vars) > 1 else (fig.add_subplot(111), None); ax.set_title(f"Empirical CDF of {', '.join(vars)}" + (f"\n{dist}" if dist else ""))
    for i, c in enumerate(vars):
        v = np.sort(df[c].dropna().values); col = PAL[i] if len(vars) > 1 else DOT; ax.step(v, np.arange(1, len(v) + 1) / len(v) * 100, where="post", color=col, label=c)
        if dist == "Normal": xs = np.linspace(v.min(), v.max(), 200); ax.plot(xs, st.norm.cdf(xs, v.mean(), v.std()) * 100, color=RED)
    ax.set(xlabel=vars[0] if len(vars) == 1 else "Data", ylabel="Percent")
    if sd is not None: _leg(sd, ax, "Variable")

def effects(fig, df, y, factors, interaction=False):
    if interaction:
        a, b = factors[:2]; ax, sd = _side(fig); ax.set_title(f"Interaction Plot for {y}\nData Means")
        for i, (k, g) in enumerate(df.groupby(b)): m = g.groupby(a)[y].mean(); ax.plot(m.index.astype(str), m.values, marker=MK[i % 8], color=PAL[i % 8], label=str(k))
        ax.set(xlabel=a, ylabel="Mean"); _leg(sd, ax, b); return
    ax = fig.subplots(1, len(factors), sharey=True, squeeze=False)[0]; fig.suptitle(f"Main Effects Plot for {y}\nData Means", fontweight="bold"); gm = df[y].mean()
    for q, f in zip(ax, factors): m = df.groupby(f)[y].mean(); q.plot(m.index.astype(str), m.values, "o-", color=DOT); q.axhline(gm, color="k", ls="--", lw=.8); q.set_xlabel(f)
    ax[0].set_ylabel("Mean")

def equalvar_plot(fig, df, y, x, conf=95.0):
    g = [(str(k), v[y].dropna()) for k, v in df.groupby(x)]; k = len(g); a = 1 - conf / 100; ax = fig.add_subplot(111); ax.set_title(f"Test for Equal Variances for {y}\n{conf:g}% Bonferroni Confidence Intervals for StDevs")
    for i, (nm, v) in enumerate(g):
        n, s_ = len(v), v.std(); lo = s_ * np.sqrt((n - 1) / st.chi2.ppf(1 - a / (2 * k), n - 1)); hi = s_ * np.sqrt((n - 1) / st.chi2.ppf(a / (2 * k), n - 1)); ax.plot([lo, hi], [i, i], "-", c=DOT, lw=2); ax.plot([s_], [i], "o", c=DOT)
    ax.set_yticks(range(k)); ax.set_yticklabels([n for n, _ in g]); ax.set(xlabel="StDev", ylabel=x)
    b = st.bartlett(*[v.values for _, v in g]); lv = st.levene(*[v.values for _, v in g], center="median"); ax.text(1.02, .5, f"Bartlett's Test\nTest Statistic  {b.statistic:.2f}\nP-Value  {b.pvalue:.3f}\n\nLevene's Test\nTest Statistic  {lv.statistic:.2f}\nP-Value  {lv.pvalue:.3f}", transform=ax.transAxes, fontsize=8, va="center", bbox=dict(boxstyle="square", fc="white", ec="#999"))

def xbar_r(fig, df, x, size):
    d = xbar_r_data(df, x, size); a, b = fig.subplots(2, 1); fig.suptitle(f"Xbar-R Chart of {x}", fontweight="bold")
    for q, y, cl, u, l, nm in ((a, d["xb"], d["xbb"], d["ux"], d["lx"], "Sample Mean"), (b, d["rg"], d["rb"], d["ur"], d["lr"], "Sample Range")):
        q.plot(range(1, len(y) + 1), y, "o-", c=DOT, ms=4, lw=1); bad = [i for i, v in enumerate(y) if v > u or v < l]; q.plot([i + 1 for i in bad], y[bad], "s", c=RED, mfc="none", ms=8)
        for v, c, t in ((cl, "g", "X̄" if nm == "Sample Mean" else "R̄"), (u, RED, "UCL"), (l, RED, "LCL")): q.axhline(v, c=c, ls="-" if c == "g" else "--", lw=1); q.text(1.0, v, f" {t}={v:.4g}", transform=q.get_yaxis_transform(), va="center", fontsize=8, color=c)
        q.set_ylabel(nm)
    b.set_xlabel("Sample")

def attr_chart(fig, df, kind, counts, sizes=None, size=None):
    y, cl, u, l = attr_data(kind, df, counts, sizes, size); ax = fig.add_subplot(111); ax.set_title(f"{kind} Chart of {counts}"); xs = np.arange(1, len(y) + 1)
    ax.plot(xs, y, "o-", c=DOT, ms=4, lw=1); ax.step(xs, cl, "g", where="mid", lw=1); ax.step(xs, u, "--", c=RED, where="mid", lw=1); ax.step(xs, l, "--", c=RED, where="mid", lw=1)
    bad = [i for i in range(len(y)) if y[i] > u[i] or y[i] < l[i]]; ax.plot(xs[bad], y[bad], "s", c=RED, mfc="none", ms=8)
    for v, c, t in ((cl[-1], "g", {"P": "P̄", "NP": "NP̄", "C": "C̄", "U": "Ū"}[kind]), (u[-1], RED, "UCL"), (l[-1], RED, "LCL")): ax.text(1.0, v, f" {t}={v:.4g}", transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=c)
    ax.set(xlabel="Sample", ylabel={"P": "Proportion", "NP": "Sample Count", "C": "Sample Count", "U": "Sample Count Per Unit"}[kind])

def residual_single(fig, df, y, x, which):
    d = df[[y] + x].dropna(); X = np.column_stack([np.ones(len(d))] + [d[c].values for c in x]); b, *_ = np.linalg.lstsq(X, d[y].values, rcond=None); fit = X @ b; r = d[y].values - fit; ax = fig.add_subplot(111)
    if which == "nplot": z = st.norm.ppf((st.rankdata(r) - .375) / (len(r) + .25)); ax.plot(r, z, "o", mfc="none", mec=DOT); ax.set(title=f"Normal Probability Plot\n(response is {y})", xlabel="Residual", ylabel="Normal Score")
    elif which == "fits": ax.plot(fit, r, "o", mfc="none", mec=DOT); ax.axhline(0, c="k", lw=.8); ax.set(title=f"Residuals Versus the Fitted Values\n(response is {y})", xlabel="Fitted Value", ylabel="Residual")
    elif which == "order": ax.plot(range(1, len(r) + 1), r, "o-", c=DOT, ms=3, lw=.8); ax.axhline(0, c="k", lw=.8); ax.set(title=f"Residuals Versus the Order of the Data\n(response is {y})", xlabel="Observation Order", ylabel="Residual")
    else: ax.hist(r, bins="auto", color=FILL, edgecolor=EDGE); ax.set(title=f"Histogram of the Residuals\n(response is {y})", xlabel="Residual", ylabel="Frequency")

def poly_fit(fig, df, y, x, deg):
    d = df[list(dict.fromkeys([x, y]))].dropna(); c = np.polyfit(d[x], d[y], deg); fit = np.polyval(c, d[x]); sse = ((d[y] - fit) ** 2).sum(); sst = ((d[y] - d[y].mean()) ** 2).sum(); n = len(d); r2 = 1 - sse / sst; s_ = np.sqrt(sse / (n - deg - 1))
    eq = f"{y} = {c[-1]:.5g}" + "".join(f" {'+' if c[-1-k] >= 0 else '-'} {abs(c[-1-k]):.5g} {x}" + ("" if k == 1 else f"**{k}") for k in range(1, deg + 1))
    ax = panel(fig, f"S        {s_:.5g}\nR-Sq     {r2*100:.1f}%\nR-Sq(adj) {(1-(1-r2)*(n-1)/(n-deg-1))*100:.1f}%", f"Fitted Line Plot\n{eq}"); ax.scatter(d[x], d[y], s=28, facecolors="none", edgecolors=DOT, linewidths=1.2)
    xs = np.linspace(d[x].min(), d[x].max(), 200); ax.plot(xs, np.polyval(c, xs), color=RED, lw=1.6); ax.set(xlabel=x, ylabel=y); return eq, r2, s_, n

def dist_plot(fig, dist, p1, p2, view="View Single", shade=None, xval=None, prob=None, tail="Left Tail"):
    d = dist_obj(dist, p1, p2); lo, hi = d.ppf(.0005), d.ppf(.9995); ax = fig.add_subplot(111); disc = dist in ("Binomial", "Poisson")
    par = {"Normal": f"Mean={fmt(p1 or 0)}, StDev={fmt(p2 if p2 is not None else 1)}", "t": f"DF={fmt(p1)}", "Chi-Square": f"DF={fmt(p1)}", "F": f"DF1={fmt(p1)}, DF2={fmt(p2)}", "Exponential": f"Scale={fmt(p1)}", "Uniform": f"Lower={fmt(p1)}, Upper={fmt(p2)}", "Binomial": f"N={fmt(p1)}, P={fmt(p2)}", "Poisson": f"Mean={fmt(p1)}"}[dist]
    ax.set_title(f"Distribution Plot\n{dist}, {par}"); ax.set(ylabel="Probability" if disc else "Density", xlabel="X")
    if disc: xs = np.arange(int(lo), int(hi) + 1); ax.bar(xs, d.pmf(xs), color=FILL, edgecolor=EDGE); return
    xs = np.linspace(lo, hi, 400); ax.plot(xs, d.pdf(xs), color=NAVY, lw=1.6)
    if view == "View Probability":
        if prob is not None and xval is None: xv = d.ppf(prob if tail == "Left Tail" else 1 - prob if tail == "Right Tail" else .5 + prob / 2)
        else: xv = xval if xval is not None else d.ppf(.5)
        if tail == "Left Tail": m = xs <= xv; pr = d.cdf(xv); lab = xv
        elif tail == "Right Tail": m = xs >= xv; pr = d.sf(xv); lab = xv
        else: a = d.ppf(.5 - abs(d.cdf(xv) - .5)); m = (xs >= min(a, xv)) & (xs <= max(a, xv)); pr = abs(d.cdf(max(a, xv)) - d.cdf(min(a, xv))); lab = xv
        ax.fill_between(xs[m], d.pdf(xs[m]), color=RED, alpha=.7); ax.text(xs[m].mean() if m.any() else xv, d.pdf(xv) * .5, f"{pr:.4g}", ha="center", color="k", fontweight="bold"); ax.set_xlabel(f"X  (x = {lab:.4g})")

def decorate(fig, r):
    if not r: return
    axs = [a for a in fig.axes if a.axison]; ax = axs[0] if axs else None
    if ax is None: return
    t = r.get("t_title") or ""; sub = r.get("t_sub") or ""
    if t: ax.set_title(t + (f"\n{sub}" if sub else ""))
    elif sub: ax.set_title(ax.get_title() + "\n" + sub)
    if r.get("t_foot"): fig.text(.01, .01, r["t_foot"], fontsize=8, ha="left", va="bottom")
    for k, f in (("xmin", None), ("xmax", None)):
        pass
    if r.get("xmin") is not None or r.get("xmax") is not None: ax.set_xlim(r.get("xmin"), r.get("xmax"))
    if r.get("ymin") is not None or r.get("ymax") is not None: ax.set_ylim(r.get("ymin"), r.get("ymax"))
    if r.get("xlog"): ax.set_xscale("log")
    if r.get("ylog"): ax.set_yscale("log")
