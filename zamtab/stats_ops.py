"""Statistical procedures with Minitab-style Session output. Each returns (title, text).
Lines starting with '## ' are rendered as bold sub-headings."""
import numpy as np, pandas as pd, scipy.stats as st

def isnum(s): return pd.api.types.is_numeric_dtype(s)
def fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "*"
    if isinstance(v, (int, np.integer)): return str(int(v))
    return f"{v:.5g}"
def pv(p): return f"{p:.3f}"
def tbl(head, rows, left=1):
    rows = [[str(c) for c in r] for r in rows]; w = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(head)]
    def line(r): return "  ".join(str(c).ljust(w[i]) if i < left else str(c).rjust(w[i]) for i, c in enumerate(r))
    return "\n".join([line(head)] + [line(r) for r in rows])
def qm(v, p):
    s = np.sort(np.asarray(v)); n = len(s); pos = min(max(p * (n + 1), 1), n); lo, hi = int(np.floor(pos)), int(np.ceil(pos))
    return s[lo - 1] + (pos - lo) * (s[hi - 1] - s[lo - 1])
def ci_t(v, conf=.95): m, se = v.mean(), v.sem(); h = st.t.ppf(1 - (1 - conf) / 2, len(v) - 1) * se; return m - h, m + h

def ad_test(v):
    """Anderson-Darling normality statistic and p-value (D'Agostino-Stephens)."""
    v = np.sort(np.asarray(v, float)); n = len(v); z = np.clip(st.norm.cdf((v - v.mean()) / v.std(ddof=1)), 1e-12, 1 - 1e-12)
    a = -n - np.sum((2 * np.arange(1, n + 1) - 1) / n * (np.log(z) + np.log(1 - z[::-1]))); x = a * (1 + .75 / n + 2.25 / n ** 2)
    if x >= .6: p = np.exp(1.2937 - 5.709 * x + .0186 * x * x)
    elif x >= .34: p = np.exp(.9177 - 4.279 * x - 1.38 * x * x)
    elif x > .2: p = 1 - np.exp(-8.318 + 42.796 * x - 59.938 * x * x)
    else: p = 1 - np.exp(-13.436 + 101.14 * x - 223.73 * x * x)
    return a, float(min(max(p, 0), 1))

def normality(df, x):
    v = df[x].dropna(); a, p = ad_test(v)
    return f"Normality Test: {x}", f"## Anderson-Darling Normality Test\nN = {len(v)}   Mean = {fmt(v.mean())}   StDev = {fmt(v.std())}\nAD = {a:.3f}   P-Value = {pv(p)}\n" + ("Data appear normally distributed (P >= 0.05)." if p >= .05 else "Data do not follow a normal distribution (P < 0.05).")

def regression(df, y, x):
    if y in x: raise ValueError('The response column cannot also be a predictor.')
    if len(x) >= len(df) - 1: raise ValueError('Too many predictors for this number of rows.')
    d = df[[y] + x].dropna(); n = len(d); Y = d[y].values; X = np.column_stack([np.ones(n)] + [d[c].values for c in x]); k = X.shape[1]
    b, *_ = np.linalg.lstsq(X, Y, rcond=None); res = Y - X @ b; sse = float(res @ res); sst = float(((Y - Y.mean()) ** 2).sum()); ssr = sst - sse
    dfe = n - k; mse = sse / dfe; cov = mse * np.linalg.inv(X.T @ X); se = np.sqrt(np.diag(cov)); t = b / se; p = 2 * st.t.sf(np.abs(t), dfe)
    h = np.einsum("ij,jk,ik->i", X, np.linalg.inv(X.T @ X), X); press = float(((res / (1 - h)) ** 2).sum())
    r2, r2a, r2p = ssr / sst, 1 - (1 - ssr / sst) * (n - 1) / dfe, 1 - press / sst
    f = (ssr / (k - 1)) / mse; vif = []
    for i, c in enumerate(x):
        if len(x) == 1: vif.append("1.00"); continue
        o = np.column_stack([np.ones(n)] + [d[z].values for z in x if z != c]); bb, *_ = np.linalg.lstsq(o, d[c].values, rcond=None)
        rr = 1 - ((d[c].values - o @ bb) ** 2).sum() / ((d[c].values - d[c].mean()) ** 2).sum(); vif.append(f"{1/(1-rr):.2f}")
    arows = [["Regression", k - 1, fmt(ssr), fmt(ssr / (k - 1)), f"{f:.2f}", pv(st.f.sf(f, k - 1, dfe))]]
    for i, c in enumerate(x):
        o = np.column_stack([np.ones(n)] + [d[z].values for z in x if z != c]); bb, *_ = np.linalg.lstsq(o, Y, rcond=None); adj = float(((Y - o @ bb) ** 2).sum()) - sse
        fi = adj / mse; arows.append(["  " + c, 1, fmt(adj), fmt(adj), f"{fi:.2f}", pv(st.f.sf(fi, 1, dfe))])
    arows += [["Error", dfe, fmt(sse), fmt(mse), "", ""], ["Total", n - 1, fmt(sst), "", "", ""]]
    crow = [["Constant", fmt(b[0]), fmt(se[0]), f"{t[0]:.2f}", pv(p[0]), ""]] + [[c, fmt(b[i + 1]), fmt(se[i + 1]), f"{t[i+1]:.2f}", pv(p[i + 1]), vif[i]] for i, c in enumerate(x)]
    eq = f"{y} = {b[0]:.5g}" + "".join(f" {'+' if b[i+1] >= 0 else '-'} {abs(b[i+1]):.5g} {c}" for i, c in enumerate(x))
    return f"Regression Analysis: {y} versus {', '.join(x)}", ("## Method\nRows used  " + str(n) + "\n\n## Analysis of Variance\n" + tbl(["Source", "DF", "Adj SS", "Adj MS", "F-Value", "P-Value"], arows) +
        "\n\n## Model Summary\n" + tbl(["S", "R-sq", "R-sq(adj)", "R-sq(pred)"], [[fmt(np.sqrt(mse)), f"{r2*100:.2f}%", f"{r2a*100:.2f}%", f"{r2p*100:.2f}%"]], 0) +
        "\n\n## Coefficients\n" + tbl(["Term", "Coef", "SE Coef", "T-Value", "P-Value", "VIF"], crow) + "\n\n## Regression Equation\n" + eq)

def anova(df, y, x):
    d = df[[x, y]].dropna(); g = [(str(k), v[y].values) for k, v in d.groupby(x)]; k, n = len(g), len(d); gm = d[y].mean()
    ssb = sum(len(v) * (v.mean() - gm) ** 2 for _, v in g); ssw = sum(((v - v.mean()) ** 2).sum() for _, v in g); dfe = n - k
    f = (ssb / (k - 1)) / (ssw / dfe); sp = np.sqrt(ssw / dfe); sst = ssb + ssw; press = sum((((v - v.mean()) / (1 - 1 / len(v))) ** 2).sum() for _, v in g)
    r2, r2a = ssb / sst, 1 - (ssw / dfe) / (sst / (n - 1)); rows = []
    for nm, v in g:
        h = st.t.ppf(.975, dfe) * sp / np.sqrt(len(v)); rows.append([nm, len(v), fmt(v.mean()), fmt(v.std()), f"({v.mean()-h:.5g}, {v.mean()+h:.5g})"])
    return f"One-way ANOVA: {y} versus {x}", ("## Method\nNull hypothesis         All means are equal\nAlternative hypothesis  At least one mean is different\nSignificance level     α = 0.05\n\nEqual variances were assumed for the analysis.\n\n"
        "## Factor Information\n" + tbl(["Factor", "Levels", "Values"], [[x, k, ", ".join(a for a, _ in g)]]) + "\n\n## Analysis of Variance\n" +
        tbl(["Source", "DF", "Adj SS", "Adj MS", "F-Value", "P-Value"], [[x, k - 1, fmt(ssb), fmt(ssb / (k - 1)), f"{f:.2f}", pv(st.f.sf(f, k - 1, dfe))], ["Error", dfe, fmt(ssw), fmt(ssw / dfe), "", ""], ["Total", n - 1, fmt(sst), "", "", ""]]) +
        "\n\n## Model Summary\n" + tbl(["S", "R-sq", "R-sq(adj)", "R-sq(pred)"], [[fmt(sp), f"{r2*100:.2f}%", f"{r2a*100:.2f}%", f"{(1-press/sst)*100:.2f}%"]], 0) +
        "\n\n## Means\n" + tbl([x, "N", "Mean", "StDev", "95% CI"], rows) + f"\n\nPooled StDev = {sp:.5g}")

def imr_tests(v, x):
    a = v.values; sg = np.abs(np.diff(a)).mean() / 1.128; cl = a.mean(); u, l = cl + 3 * sg, cl - 3 * sg
    t1 = [i + 1 for i in np.where((a > u) | (a < l))[0]]; side = np.sign(a - cl); t2 = []
    for i in range(8, len(a)):
        if abs(side[i - 8:i + 1].sum()) == 9: t2.append(i + 1)
    s = f"## I Chart of {x}\nCenter line = {cl:.5g}   UCL = {u:.5g}   LCL = {l:.5g}\n\n"
    s += ("TEST 1. One point more than 3.00 standard deviations from center line.\nTest Failed at points: " + ", ".join(map(str, t1))) if t1 else "TEST 1: no points failed."
    s += "\n\n" + (("TEST 2. 9 points in a row on same side of center line.\nTest Failed at points: " + ", ".join(map(str, t2))) if t2 else "TEST 2: no points failed.")
    return f"I-MR Chart of {x}", s

def stem_leaf(df, x):
    v = np.sort(df[x].dropna().values); span = v.max() - v.min(); unit = 10 ** np.floor(np.log10(span / 5 if span else 1)); lines = []
    stems = np.floor(v / (unit * 10)).astype(int); leaves = (np.floor(v / unit) % 10).astype(int); cum = 0
    for s in range(stems.min(), stems.max() + 1):
        lv = "".join(str(l) for l, ss in zip(leaves, stems) if ss == s); cum += len(lv)
        lines.append(f"{cum:>4}  {s:>5} | {lv}")
    return f"Stem-and-Leaf Display: {x}", f"Stem-and-leaf of {x}   N = {len(v)}\nLeaf Unit = {unit:g}\n\n" + "\n".join(lines)

# ======================= Minitab 17 style procedures =======================
ALT = {"not equal": ("not =", "two-sided"), "less than": ("<", "less"), "greater than": (">", "greater")}
def _alt(a): return ALT.get(a or "not equal", ALT["not equal"])
def _pt(t, d, sci): return 2 * st.t.sf(abs(t), d) if sci == "two-sided" else (st.t.cdf(t, d) if sci == "less" else st.t.sf(t, d))
def _pz(z, sci): return 2 * st.norm.sf(abs(z)) if sci == "two-sided" else (st.norm.cdf(z) if sci == "less" else st.norm.sf(z))
def _q(conf, sci): a = 1 - conf / 100; return 1 - a / 2 if sci == "two-sided" else 1 - a
def _bound(est, se, crit, conf, sci, what):
    if sci == "two-sided": return f"{conf:g}% CI for {what}", f"({est - crit * se:.5g}, {est + crit * se:.5g})"
    if sci == "less": return f"{conf:g}% upper bound for {what}", f"{est + crit * se:.5g}"
    return f"{conf:g}% lower bound for {what}", f"{est - crit * se:.5g}"
def _hd(conf, sci): return {"two-sided": f"{conf:g}% CI", "less": f"{conf:g}% Upper Bound", "greater": f"{conf:g}% Lower Bound"}[sci]

SD = [("N total", "Total Count", False, lambda v, t, m: t), ("N nonmissing", "N", True, lambda v, t, m: len(v)), ("N missing", "N*", True, lambda v, t, m: m),
      ("Mean", "Mean", True, lambda v, t, m: v.mean()), ("SE of mean", "SE Mean", True, lambda v, t, m: v.sem()), ("Trimmed mean", "TrMean", False, lambda v, t, m: st.trim_mean(v, .05)),
      ("StDev", "StDev", True, lambda v, t, m: v.std()), ("Variance", "Variance", False, lambda v, t, m: v.var()), ("Coefficient of variation", "CoefVar", False, lambda v, t, m: v.std() / v.mean() * 100),
      ("Minimum", "Minimum", True, lambda v, t, m: v.min()), ("First quartile", "Q1", True, lambda v, t, m: qm(v, .25)), ("Median", "Median", True, lambda v, t, m: v.median()),
      ("Third quartile", "Q3", True, lambda v, t, m: qm(v, .75)), ("Maximum", "Maximum", True, lambda v, t, m: v.max()), ("Range", "Range", False, lambda v, t, m: v.max() - v.min()),
      ("Interquartile range", "IQR", False, lambda v, t, m: qm(v, .75) - qm(v, .25)), ("Mode", "Mode", False, lambda v, t, m: v.mode().iloc[0] if len(v) else np.nan),
      ("Sum", "Sum", False, lambda v, t, m: v.sum()), ("Sum of squares", "SumSq", False, lambda v, t, m: (v ** 2).sum()),
      ("Skewness", "Skewness", False, lambda v, t, m: st.skew(v, bias=False)), ("Kurtosis", "Kurtosis", False, lambda v, t, m: st.kurtosis(v, bias=False))]
def stat_fields(): return [(f"s{i}", d[0], "check", d[2]) for i, d in enumerate(SD)]
def _stat_rows(df, vars, by, kw):
    sel = [i for i, d in enumerate(SD) if kw.get(f"s{i}", d[2])]; rows = []
    for c in vars:
        parts = [(None, df[c])] if not by else [(k, g[c]) for k, g in df.groupby(by)]
        for k, col in parts:
            v = col.dropna(); rows.append(([c] + ([str(k)] if by else []), [d(v, len(col), int(col.isna().sum())) for d in (SD[i][3] for i in sel)]))
    return sel, rows
def descriptive(df, vars, by=None, **kw):
    sel, rows = _stat_rows(df, vars, by, kw)
    head = ["Variable"] + ([by] if by else []) + [SD[i][1] for i in sel]
    return "Descriptive Statistics: " + ", ".join(vars) + (f" by {by}" if by else ""), tbl(head, [a + [fmt(x) for x in b] for a, b in rows], 2 if by else 1)
def store_descriptive(df, vars, by=None, **kw):
    sel, rows = _stat_rows(df, vars, by, kw); out = {}
    for j, i in enumerate(sel): out[SD[i][1].replace("*", "Miss") + "1"] = [b[j] for _, b in rows]
    out["Variable"] = [a[0] for a, _ in rows]; return out

def correlation(df, vars, **_):
    d = df[vars].dropna(); n = len(d)
    if len(vars) == 2:
        r, p = st.pearsonr(d[vars[0]], d[vars[1]]); return f"Correlations: {vars[0]}, {vars[1]}", f"Pearson correlation of {vars[0]} and {vars[1]} = {r:.3f}\nP-Value = {pv(p)}"
    rows = []
    for a in vars:
        rows.append([a] + [f"{d[a].corr(d[b]):.3f}" if b != a or True else "" for b in vars]); rows.append([""] + ["" if a == b else pv(st.pearsonr(d[a], d[b])[1]) for b in vars])
    return "Correlations: " + ", ".join(vars), tbl([""] + vars, rows) + "\n\nCell Contents: Pearson correlation\n               P-Value"
def covariance(df, vars, **_):
    c = df[vars].dropna().cov(); return "Covariances: " + ", ".join(vars), tbl([""] + vars, [[a] + [fmt(c.loc[a, b]) for b in vars] for a in vars])

def t1(df, x, mu=None, conf=95.0, alt="not equal", **_):
    mu = mu or 0.0; sym, sci = _alt(alt); rows = []
    for c in x:
        v = df[c].dropna(); n = len(v); se = v.sem(); t = (v.mean() - mu) / se; crit = st.t.ppf(_q(conf, sci), n - 1); _, ci = _bound(v.mean(), se, crit, conf, sci, "")
        rows.append([c, n, fmt(v.mean()), fmt(v.std()), fmt(se), ci, f"{t:.2f}", pv(_pt(t, n - 1, sci))])
    return "One-Sample T: " + ", ".join(x), f"Test of mu = {fmt(mu)} vs {sym} {fmt(mu)}\n\n" + tbl(["Variable", "N", "Mean", "StDev", "SE Mean", _hd(conf, sci), "T", "P"], rows)
def z1(df, x, sigma=None, mu=None, conf=95.0, alt="not equal", **_):
    if not sigma: raise ValueError("Enter the known standard deviation.")
    mu = mu or 0.0; sym, sci = _alt(alt); rows = []
    for c in x:
        v = df[c].dropna(); n = len(v); se = sigma / np.sqrt(n); z = (v.mean() - mu) / se; _, ci = _bound(v.mean(), se, st.norm.ppf(_q(conf, sci)), conf, sci, "")
        rows.append([c, n, fmt(v.mean()), fmt(v.std()), fmt(se), ci, f"{z:.2f}", pv(_pz(z, sci))])
    return "One-Sample Z: " + ", ".join(x), f"Test of mu = {fmt(mu)} vs {sym} {fmt(mu)}\nThe assumed standard deviation = {fmt(sigma)}\n\n" + tbl(["Variable", "N", "Mean", "StDev", "SE Mean", _hd(conf, sci), "Z", "P"], rows)

def t2(df, s1, s2=None, grp=None, conf=95.0, diff=None, alt="not equal", pooled=False, **_):
    diff = diff or 0.0; sym, sci = _alt(alt)
    if grp:
        g = [(str(k), v[s1].dropna()) for k, v in df.groupby(grp)]
        if len(g) != 2: raise ValueError(f"'{grp}' must have exactly 2 levels (found {len(g)}).")
        (n1, a), (n2, b) = g; title, head = f"Two-Sample T-Test and CI: {s1}, {grp}", f"Two-sample T for {s1}"
    elif s2: a, b, n1, n2 = df[s1].dropna(), df[s2].dropna(), s1, s2; title, head = f"Two-Sample T-Test and CI: {s1}, {s2}", f"Two-sample T for {s1} vs {s2}"
    else: raise ValueError("Give Sample 2 (separate column) or Sample IDs (one-column form).")
    na, nb, va, vb = len(a), len(b), a.var(), b.var(); d = a.mean() - b.mean()
    if pooled: dof = na + nb - 2; sp = np.sqrt(((na - 1) * va + (nb - 1) * vb) / dof); se = sp * np.sqrt(1 / na + 1 / nb)
    else: se = np.sqrt(va / na + vb / nb); dof = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    t = (d - diff) / se; lab, ci = _bound(d, se, st.t.ppf(_q(conf, sci), dof), conf, sci, "difference")
    body = (f"{head}\n\n" + tbl(["", "N", "Mean", "StDev", "SE Mean"], [[n1, na, fmt(a.mean()), fmt(a.std()), fmt(a.sem())], [n2, nb, fmt(b.mean()), fmt(b.std()), fmt(b.sem())]]) +
            f"\n\nDifference = mu ({n1}) - mu ({n2})\nEstimate for difference:  {fmt(d)}\n{lab}:  {ci}\nT-Test of difference = {fmt(diff)} (vs {sym}): T-Value = {t:.2f}  P-Value = {pv(_pt(t, dof, sci))}  DF = {int(dof)}")
    return title, body + (f"\nBoth use Pooled StDev = {sp:.5g}" if pooled else "")
def paired(df, x, y, conf=95.0, diff=None, alt="not equal", **_):
    diff = diff or 0.0; sym, sci = _alt(alt); d = df[[x, y]].dropna(); dd = d[x] - d[y]; n = len(d); t = (dd.mean() - diff) / dd.sem(); lab, ci = _bound(dd.mean(), dd.sem(), st.t.ppf(_q(conf, sci), n - 1), conf, sci, "mean difference")
    r = [[c, n, fmt(d[c].mean()), fmt(d[c].std()), fmt(d[c].sem())] for c in (x, y)] + [["Difference", n, fmt(dd.mean()), fmt(dd.std()), fmt(dd.sem())]]
    return f"Paired T-Test and CI: {x}, {y}", f"Paired T for {x} - {y}\n\n" + tbl(["", "N", "Mean", "StDev", "SE Mean"], r) + f"\n\n{lab}: {ci}\nT-Test of mean difference = {fmt(diff)} (vs {sym} {fmt(diff)}): T-Value = {t:.2f}  P-Value = {pv(_pt(t, n - 1, sci))}"

def prop1(df, x=None, event=None, events=None, trials=None, p0=None, conf=95.0, alt="not equal", **_):
    p0 = 0.5 if p0 is None else p0; sym, sci = _alt(alt); extra = ""
    if x: v = df[x].dropna().astype(str); ev = event or sorted(v.unique())[-1]; X, N = int((v == ev).sum()), len(v); extra = f"Event = {ev}\n\n"
    else:
        if events is None or not trials: raise ValueError("Enter number of events and trials, or choose a column.")
        X, N = int(events), int(trials)
    a = 1 - conf / 100; lo = st.beta.ppf(a / 2 if sci == "two-sided" else a, X, N - X + 1) if X > 0 else 0.0; hi = st.beta.ppf(1 - a / 2 if sci == "two-sided" else 1 - a, X + 1, N - X) if X < N else 1.0
    ci = {"two-sided": f"({lo:.6f}, {hi:.6f})", "less": f"{hi:.6f}", "greater": f"{lo:.6f}"}[sci]; p = st.binomtest(X, N, p0, alternative=sci).pvalue
    return "Test and CI for One Proportion", extra + f"Test of p = {p0:g} vs p {sym} {p0:g}\n\n" + tbl(["Sample", "X", "N", "Sample p", _hd(conf, sci), "Exact P-Value"], [[1, X, N, f"{X/N:.6f}", ci, pv(p)]])
def prop2(df, e1, n1, e2, n2, conf=95.0, diff=None, alt="not equal", **_):
    if None in (e1, n1, e2, n2): raise ValueError("Enter events and trials for both samples.")
    diff = diff or 0.0; sym, sci = _alt(alt); p1, p2 = e1 / n1, e2 / n2; d = p1 - p2; se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2); pp = (e1 + e2) / (n1 + n2)
    set_ = np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) if diff == 0 else se; z = (d - diff) / set_; lab, ci = _bound(d, se, st.norm.ppf(_q(conf, sci)), conf, sci, "difference")
    fe = st.fisher_exact([[int(e1), int(n1 - e1)], [int(e2), int(n2 - e2)]], alternative=sci)[1]
    return "Test and CI for Two Proportions", (tbl(["Sample", "X", "N", "Sample p"], [[1, int(e1), int(n1), f"{p1:.6f}"], [2, int(e2), int(n2), f"{p2:.6f}"]]) +
        f"\n\nDifference = p (1) - p (2)\nEstimate for difference:  {d:.6g}\n{lab}:  {ci}\nTest for difference = {diff:g} (vs {sym} {diff:g}):  Z = {z:.2f}  P-Value = {pv(_pz(z, sci))}\n\nFisher's exact test: P-Value = {pv(fe)}")

def equal_var(df, y, x, conf=95.0, **_):
    g = [(str(k), v[y].dropna()) for k, v in df.groupby(x)]; k = len(g); a = 1 - conf / 100; rows = []
    for nm, v in g:
        n, sd_ = len(v), v.std(); rows.append([nm, n, fmt(sd_ * np.sqrt((n - 1) / st.chi2.ppf(1 - a / (2 * k), n - 1))), fmt(sd_), fmt(sd_ * np.sqrt((n - 1) / st.chi2.ppf(a / (2 * k), n - 1)))])
    vals = [v.values for _, v in g]; b = st.bartlett(*vals); lv = st.levene(*vals, center="median"); s = f"{conf:g}% Bonferroni confidence intervals for standard deviations\n\n" + tbl([x, "N", "Lower", "StDev", "Upper"], rows)
    if k == 2:
        f = vals[0].var(ddof=1) / vals[1].var(ddof=1); n1, n2 = len(vals[0]), len(vals[1]); s += f"\n\nF Test (Normal Distribution)\nTest statistic = {f:.2f}, p-value = {pv(2 * min(st.f.cdf(f, n1 - 1, n2 - 1), st.f.sf(f, n1 - 1, n2 - 1)))}"
    return f"Test for Equal Variances: {y} versus {x}", s + f"\n\nBartlett's Test (Normal Distribution)\nTest statistic = {b.statistic:.2f}, p-value = {pv(b.pvalue)}\n\nLevene's Test (Any Continuous Distribution)\nTest statistic = {lv.statistic:.2f}, p-value = {pv(lv.pvalue)}"

def _dum(s): return pd.get_dummies(s.astype(str), drop_first=True).astype(float).values
def kruskal(df, y, x, **_):
    d = df[[x, y]].dropna(); r = st.rankdata(d[y]); d = d.assign(_r=r); N = len(d); g = d.groupby(x); rows = []; H = 0
    for k, v in g:
        n = len(v); mr = v["_r"].mean(); z = (mr - (N + 1) / 2) / np.sqrt((N + 1) * (N - n) / (12 * n)); H += n * mr ** 2; rows.append([str(k), n, fmt(v[y].median()), f"{mr:.1f}", f"{z:.2f}"])
    H = 12 / (N * (N + 1)) * H - 3 * (N + 1); adj = st.kruskal(*[v[y].values for _, v in g]); dof = len(rows) - 1; rows.append(["Overall", N, "", f"{(N+1)/2:.1f}", ""])
    return f"Kruskal-Wallis Test: {y} versus {x}", f"Kruskal-Wallis Test on {y}\n\n" + tbl([x, "N", "Median", "Ave Rank", "Z"], rows) + f"\n\nH = {H:.2f}  DF = {dof}  P = {pv(st.chi2.sf(H, dof))}\nH = {adj.statistic:.2f}  DF = {dof}  P = {pv(adj.pvalue)}  (adjusted for ties)"
def wilcoxon1(df, x, mu=None, conf=95.0, alt="not equal", **_):
    mu = mu or 0.0; sym, sci = _alt(alt); v = df[x].dropna(); d = v - mu; d = d[d != 0]; n = len(v); wp = st.rankdata(np.abs(d))[(d > 0).values].sum(); p = st.wilcoxon(d, alternative=sci).pvalue
    a = v.values; walsh = ((a[:, None] + a[None, :]) / 2)[np.triu_indices(len(a))]
    return f"Wilcoxon Signed Rank Test: {x}", f"Test of median = {fmt(mu)} versus median {sym} {fmt(mu)}\n\n" + tbl(["", "N", "N for Test", "Wilcoxon Statistic", "P", "Estimated Median"], [[x, n, len(d), f"{wp:.1f}", pv(p), fmt(np.median(walsh))]])
def tally(df, vars, **_):
    out = []
    for c in vars:
        vc = df[c].value_counts().sort_index(); n = vc.sum(); out.append(f"Tally for Discrete Variables: {c}\n\n" + tbl([c, "Count", "Percent"], [[str(k), v, f"{v/n*100:.2f}"] for k, v in vc.items()] + [["N=", n, ""]]))
    return "Tally for Discrete Variables: " + ", ".join(vars), "\n\n".join(out)
def power_t1(df=None, n=None, power=None, diff=None, sd=None, alpha=0.05, alt="not equal", **_):
    sd = sd or 1.0; sci = _alt(alt)[1]
    def pw(n, d):
        df_ = n - 1; nc = d * np.sqrt(n) / sd
        if sci == "two-sided": c = st.t.ppf(1 - alpha / 2, df_); return st.nct.sf(c, df_, nc) + st.nct.cdf(-c, df_, nc)
        c = st.t.ppf(1 - alpha, df_); return st.nct.sf(c, df_, nc) if sci == "greater" else st.nct.cdf(-c, df_, nc)
    if n and diff: res = [[fmt(diff), int(n), f"{pw(int(n), diff):.5f}"]]; mode = "Calculating power"
    elif power and diff:
        k = 2
        while k < 100000 and pw(k, diff) < power: k += 1
        res = [[fmt(diff), k, f"{pw(k, diff):.5f}"]]; mode = "Calculating sample size"
    else: raise ValueError("Enter Difference and either Sample size (to get power) or Power (to get sample size).")
    return "Power and Sample Size", f"1-Sample t Test\n\nTesting mean = null (versus {_alt(alt)[0]} null)\n{mode} for mean = null + difference\nα = {alpha:g}  Assumed standard deviation = {fmt(sd)}\n\n" + tbl(["Difference", "Sample Size", "Power"], res, 0)

def capability_stats(v, lsl, usl, size=1):
    mu, so_ = v.mean(), v.std(); a = v.values
    if size and size > 1:
        m = len(a) // int(size); sub = a[:m * int(size)].reshape(m, int(size)); sw = np.sqrt(np.mean(sub.var(axis=1, ddof=1)))
    else: sw = np.abs(np.diff(a)).mean() / 1.128
    def idx(s):
        cpu = (usl - mu) / (3 * s) if usl is not None else np.nan; cpl = (mu - lsl) / (3 * s) if lsl is not None else np.nan
        cp = (usl - lsl) / (6 * s) if lsl is not None and usl is not None else np.nan; return cp, cpl, cpu, np.nanmin([cpl, cpu])
    def ppm(s): lo = st.norm.cdf(lsl, mu, s) if lsl is not None else 0; hi = st.norm.sf(usl, mu, s) if usl is not None else 0; return lo * 1e6, hi * 1e6, (lo + hi) * 1e6
    return mu, so_, sw, idx(sw), idx(so_), ppm(sw), ppm(so_)
def capability(df, x, lsl=None, usl=None, size=None, **_):
    if lsl is None and usl is None: raise ValueError("Enter at least one specification limit (lower or upper).")
    v = df[x].dropna(); mu, so_, sw, (cp, cpl, cpu, cpk), (pp, ppl, ppu, ppk), pw, po = capability_stats(v, lsl, usl, size or 1)
    obs = [(v < lsl).sum() / len(v) * 1e6 if lsl is not None else 0, (v > usl).sum() / len(v) * 1e6 if usl is not None else 0]; r2 = lambda z: fmt(round(z, 2)); pp3 = lambda a: [f"{q:.2f}" for q in a]
    return f"Process Capability of {x}", (f"Process Data\nLSL                {fmt(lsl)}\nTarget             *\nUSL                {fmt(usl)}\nSample Mean        {fmt(mu)}\nSample N           {len(v)}\nStDev (Within)     {fmt(sw)}\nStDev (Overall)    {fmt(so_)}\n\n"
        "Potential (Within) Capability\n" + tbl(["Cp", "CPL", "CPU", "Cpk"], [[r2(cp), r2(cpl), r2(cpu), r2(cpk)]], 0) + "\n\nOverall Capability\n" + tbl(["Pp", "PPL", "PPU", "Ppk"], [[r2(pp), r2(ppl), r2(ppu), r2(ppk)]], 0) +
        "\n\nObserved Performance\n" + tbl(["PPM < LSL", "PPM > USL", "PPM Total"], [pp3(obs + [sum(obs)])], 0) + "\n\nExp. Within Performance\n" + tbl(["PPM < LSL", "PPM > USL", "PPM Total"], [pp3(pw)], 0) + "\n\nExp. Overall Performance\n" + tbl(["PPM < LSL", "PPM > USL", "PPM Total"], [pp3(po)], 0))

A2 = {2: 1.880, 3: 1.023, 4: .729, 5: .577, 6: .483, 7: .419, 8: .373, 9: .337, 10: .308}; D3 = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: .076, 8: .136, 9: .184, 10: .223}; D4 = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
def xbar_r_data(df, x, size):
    size = int(size or 0)
    if size < 2 or size > 10: raise ValueError("Subgroup size must be between 2 and 10.")
    a = df[x].dropna().values; m = len(a) // size; sub = a[:m * size].reshape(m, size); xb, rg = sub.mean(1), sub.max(1) - sub.min(1); xbb, rb = xb.mean(), rg.mean()
    return dict(xb=xb, rg=rg, xbb=xbb, rb=rb, ux=xbb + A2[size] * rb, lx=xbb - A2[size] * rb, ur=D4[size] * rb, lr=D3[size] * rb)
def xbar_r_tests(df, x, size):
    d = xbar_r_data(df, x, size); b1 = [i + 1 for i, v in enumerate(d["xb"]) if v > d["ux"] or v < d["lx"]]; b2 = [i + 1 for i, v in enumerate(d["rg"]) if v > d["ur"] or v < d["lr"]]
    return f"Xbar-R Chart of {x}", f"Test Results for Xbar Chart of {x}\n\n" + (f"TEST 1. One point more than 3.00 standard deviations from center line.\nTest Failed at points: {', '.join(map(str, b1))}" if b1 else "No tests failed.") + f"\n\nTest Results for R Chart of {x}\n\n" + (f"TEST 1. One point more than 3.00 standard deviations from center line.\nTest Failed at points: {', '.join(map(str, b2))}" if b2 else "No tests failed.")
def attr_data(kind, df, counts, sizes=None, size=None):
    c = df[counts].dropna().values.astype(float); n = df[sizes].loc[df[counts].dropna().index].values.astype(float) if sizes else np.full(len(c), float(size or 0))
    if kind in ("P", "U") and (n <= 0).any(): raise ValueError("Give subgroup sizes (column or constant).")
    if kind == "P": y = c / n; cl = c.sum() / n.sum(); s = np.sqrt(cl * (1 - cl) / n); u, l = cl + 3 * s, np.maximum(cl - 3 * s, 0)
    elif kind == "NP": y = c; pb = c.sum() / n.sum(); cl = pb * n; s = np.sqrt(n * pb * (1 - pb)); u, l = cl + 3 * s, np.maximum(cl - 3 * s, 0)
    elif kind == "C": y = c; cl = c.mean(); s = np.sqrt(cl); u, l = cl + 3 * s, max(cl - 3 * s, 0) * np.ones(len(c)); cl = cl * np.ones(len(c)); u = u * np.ones(len(c))
    else: y = c / n; cl = c.sum() / n.sum(); s = np.sqrt(cl / n); u, l = cl + 3 * s, np.maximum(cl - 3 * s, 0)
    cl = np.broadcast_to(cl, y.shape); u = np.broadcast_to(u, y.shape); l = np.broadcast_to(l, y.shape); return y, cl, u, l
def attr_tests(kind, df, counts, sizes=None, size=None):
    y, cl, u, l = attr_data(kind, df, counts, sizes, size); bad = [i + 1 for i in range(len(y)) if y[i] > u[i] or y[i] < l[i]]
    return f"{kind} Chart of {counts}", f"Test Results for {kind} Chart of {counts}\n\n" + (f"TEST 1. One point more than 3.00 standard deviations from center line.\nTest Failed at points: {', '.join(map(str, bad))}" if bad else "No tests failed.")

def col_stat(df, x, stat):
    v = df[x].dropna(); f = {"Sum": v.sum, "Mean": v.mean, "StDev": v.std, "Minimum": v.min, "Maximum": v.max, "Median": v.median, "N total": lambda: len(df[x]), "N nonmissing": lambda: len(v), "N missing": lambda: int(df[x].isna().sum()), "Sum of squares": lambda: (v ** 2).sum()}[stat]()
    return f"Column Statistics: {x}", f"{stat} of {x} = {fmt(f)}", f
DISTS = {"Normal": ("Mean", "StDev"), "t": ("DF", ""), "Chi-Square": ("DF", ""), "F": ("DF numerator", "DF denominator"), "Exponential": ("Scale", ""), "Uniform": ("Lower endpoint", "Upper endpoint"), "Binomial": ("Number of trials", "Event probability"), "Poisson": ("Mean", "")}
def dist_obj(name, p1, p2):
    p1 = 0 if p1 is None else p1; p2 = 1 if p2 is None else p2
    return {"Normal": lambda: st.norm(p1, p2), "t": lambda: st.t(p1), "Chi-Square": lambda: st.chi2(p1), "F": lambda: st.f(p1, p2), "Exponential": lambda: st.expon(scale=p1 or 1), "Uniform": lambda: st.uniform(p1, p2 - p1), "Binomial": lambda: st.binom(int(p1), p2), "Poisson": lambda: st.poisson(p1)}[name]()
def distcalc(kind, dist, p1, p2, x):
    if x is None: raise ValueError("Enter the input constant.")
    d = dist_obj(dist, p1, p2); disc = dist in ("Binomial", "Poisson"); par = {"Normal": f"mean = {fmt(p1 or 0)} and standard deviation = {fmt(p2 if p2 is not None else 1)}", "t": f"{fmt(p1)} DF", "Chi-Square": f"{fmt(p1)} DF", "F": f"{fmt(p1)} DF numerator, {fmt(p2)} DF denominator", "Exponential": f"scale = {fmt(p1)}", "Uniform": f"lower endpoint = {fmt(p1)} and upper endpoint = {fmt(p2)}", "Binomial": f"n = {fmt(p1)} and p = {fmt(p2)}", "Poisson": f"mean = {fmt(p1)}"}[dist]
    if kind == "Cumulative probability": return "Cumulative Distribution Function", f"{dist} with {par}\n\n" + tbl(["x", "P( X <= x )"], [[fmt(x), f"{d.cdf(x):.6g}"]], 0)
    if kind == "Probability density" or kind == "Probability": return ("Probability Mass Function" if disc else "Probability Density Function"), f"{dist} with {par}\n\n" + tbl(["x", "P( X = x )" if disc else "f( x )"], [[fmt(x), f"{(d.pmf(x) if disc else d.pdf(x)):.6g}"]], 0)
    return "Inverse Cumulative Distribution Function", f"{dist} with {par}\n\n" + tbl(["P( X <= x )", "x"], [[fmt(x), f"{d.ppf(x):.6g}"]], 0)

def two_way(df, y, a, b, **_):
    d = df[[y, a, b]].dropna(); Y = d[y].values; n = len(d); A, B = _dum(d[a]), _dum(d[b]); AB = np.column_stack([A[:, i] * B[:, j] for i in range(A.shape[1]) for j in range(B.shape[1])])
    def sse(*M):
        X = np.column_stack([np.ones(n)] + list(M)); c, *_ = np.linalg.lstsq(X, Y, rcond=None); r = Y - X @ c; return float(r @ r)
    sst = float(((Y - Y.mean()) ** 2).sum()); e1, e2, e3 = sse(A), sse(A, B), sse(A, B, AB); da, db, dab = A.shape[1], B.shape[1], AB.shape[1]; dfe = n - 1 - da - db - dab; inter = dfe > 0
    if not inter: e3, dab, dfe = e2, 0, n - 1 - da - db
    ss = {a: (sst - e1, da), b: (e1 - e2, db)}
    if inter: ss["Interaction"] = (e2 - e3, dab)
    mse = e3 / dfe; rows = []
    for nm, (q, d_) in ss.items(): f = q / d_ / mse; rows.append([nm, d_, fmt(q), fmt(q / d_), f"{f:.2f}", pv(st.f.sf(f, d_, dfe))])
    rows += [["Error", dfe, fmt(e3), fmt(mse), "", ""], ["Total", n - 1, fmt(sst), "", "", ""]]; r2 = 1 - e3 / sst
    return f"Two-way ANOVA: {y} versus {a}, {b}", tbl(["Source", "DF", "SS", "MS", "F", "P"], rows) + f"\n\nS = {np.sqrt(mse):.5g}   R-Sq = {r2*100:.2f}%   R-Sq(adj) = {(1-(e3/dfe)/(sst/(n-1)))*100:.2f}%"

def tukey(df, y, x, conf=95.0, **_):
    g = [(str(k), v[y].dropna().values) for k, v in df.groupby(x)]; r = st.tukey_hsd(*[v for _, v in g]); ci = r.confidence_interval(conf / 100); rows = []
    dfe = sum(len(v) for _, v in g) - len(g); mse = sum(((v - v.mean()) ** 2).sum() for _, v in g) / dfe
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            d = g[j][1].mean() - g[i][1].mean(); se = np.sqrt(mse * (1 / len(g[i][1]) + 1 / len(g[j][1])))
            rows.append([f"{g[j][0]} - {g[i][0]}", fmt(d), fmt(se), f"({ci.low[j, i]:.5g}, {ci.high[j, i]:.5g})", f"{d/se:.2f}", pv(r.pvalue[j, i])])
    return f"Tukey Pairwise Comparisons: {y} versus {x}", f"Tukey Simultaneous Tests for Differences of Means ({conf:g}% family confidence)\n\n" + tbl(["Difference of Levels", "Difference of Means", "SE of Difference", "Simultaneous CI", "T-Value", "Adjusted P-Value"], rows)

def mannwhitney(df, s1, s2=None, grp=None, conf=95.0, alt="not equal", **_):
    sym, sci = _alt(alt)
    if grp:
        g = [(str(k), v[s1].dropna()) for k, v in df.groupby(grp)]
        if len(g) != 2: raise ValueError("Sample IDs must have exactly 2 levels.")
        (n1, a), (n2, b) = g; title = f"Mann-Whitney Test and CI: {s1}, {grp}"
    elif s2: a, b, n1, n2 = df[s1].dropna(), df[s2].dropna(), s1, s2; title = f"Mann-Whitney Test and CI: {s1}, {s2}"
    else: raise ValueError("Give Sample 2 or Sample IDs.")
    na, nb = len(a), len(b); w = st.rankdata(np.concatenate([a, b]))[:na].sum(); p = st.mannwhitneyu(a, b, alternative=sci).pvalue
    dd = np.sort((a.values[:, None] - b.values[None, :]).ravel()); k = int(max(np.floor(na * nb / 2 - st.norm.ppf(1 - (1 - conf / 100) / 2) * np.sqrt(na * nb * (na + nb + 1) / 12)), 0)); lo, hi = dd[k], dd[len(dd) - 1 - k]
    body = (tbl(["", "N", "Median"], [[n1, na, fmt(a.median())], [n2, nb, fmt(b.median())]]) + f"\n\nPoint estimate for ETA1-ETA2 is {np.median(dd):.5g}\n{conf:.1f} Percent CI for ETA1-ETA2 is ({lo:.5g}, {hi:.5g})\nW = {w:.1f}\nTest of ETA1 = ETA2 vs ETA1 {sym} ETA2 is significant at {p:.4f}")
    return title, body + (f"\nThe test is significant at {p:.4f} (adjusted for ties)" if p < .05 else "\nCannot reject at alpha = 0.05")

def crosstab(df, r, c, counts=True, rowp=False, colp=False, totp=False, expected=False, chi=True, **_):
    ct = pd.crosstab(df[r], df[c]); V = ct.values; tot = V.sum(); chi2, p, dof, exp = st.chi2_contingency(ct, correction=False); R, C = V.shape; cols = [str(x) for x in ct.columns] + ["All"]; rows = []
    contents = [n for n, on in (("Count", counts), ("% of Row", rowp), ("% of Column", colp), ("% of Total", totp), ("Expected count", expected)) if on]
    for i in range(R + 1):
        blk = []
        for j in range(C + 1):
            n = V[i, j] if i < R and j < C else (V[i].sum() if i < R else (V[:, j].sum() if j < C else tot)); rt = V[i].sum() if i < R else tot; cc = V[:, j].sum() if j < C else tot; o = []
            if counts: o.append(str(n))
            if rowp: o.append(f"{n/rt*100:.2f}")
            if colp: o.append(f"{n/cc*100:.2f}")
            if totp: o.append(f"{n/tot*100:.2f}")
            if expected: o.append(f"{exp[i, j]:.2f}" if i < R and j < C else "")
            blk.append(o)
        for k in range(len(contents)): rows.append([(str(ct.index[i]) if i < R else "All") if k == 0 else ""] + [b[k] for b in blk])
    s = f"Rows: {r}   Columns: {c}\n\n" + tbl([""] + cols, rows) + "\n\nCell Contents:  " + "\n                ".join(contents)
    if chi:
        lr = st.chi2_contingency(ct, correction=False, lambda_="log-likelihood"); s += f"\n\nPearson Chi-Square = {chi2:.3f}, DF = {dof}, P-Value = {pv(p)}\nLikelihood Ratio Chi-Square = {lr[0]:.3f}, DF = {dof}, P-Value = {pv(lr[1])}"
        low = int((exp < 5).sum())
        if low: s += f"\n\n* NOTE * {low} cell(s) with expected counts less than 5"
    return f"Tabulated statistics: {r}, {c}", s
