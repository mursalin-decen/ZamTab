"""Menu structure (Minitab 17 order) and the dialogs/handlers behind every menu item."""
import inspect, os, tempfile
import numpy as np, pandas as pd, scipy.stats as st
from tkinter import messagebox, simpledialog
from . import stats_ops as so, graphs as G, gallery as GL
from .dialogs import LABELS_SUB, SCALE_SUB, McDialog

ALT = ("Alternative hypothesis:", "combo", ["not equal", "less than", "greater than"])
OPT_T = ("Options...", [("conf", "Confidence level:", "float", 95.0), ("alt", ALT[0], "combo", ALT[2])])
def _graphs(*items): return ("Graphs...", [(k, l, "check", d) for k, l, d in items])

def menu_spec(app):
    def C(fn, **fx):
        sig = inspect.signature(fn); has_kw = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()); names = set(sig.parameters)
        return lambda r: fn(app.df, **{k: v for k, v in {**r, **fx}.items() if has_kw or k in names})
    P = app.proc; D = lambda: app.df
    def stat(title, fields, fn, subs=(), graphs=None, need=True): return lambda: P(title, fields, fn, list(subs), graphs, need)
    def qg(r, cols):
        jobs = []
        for c in cols:
            if r.get("g_hist"): jobs.append((f"Histogram of {c}", lambda fig, c=c: G.histogram(fig, D(), c, fit=False)))
            if r.get("g_histfit"): jobs.append((f"Histogram of {c}", lambda fig, c=c: G.histogram(fig, D(), c, fit=True)))
            if r.get("g_ivp"): jobs.append((f"Individual Value Plot of {c}", lambda fig, c=c: GL.ivp_v(fig, D(), [c])))
            if r.get("g_box"): jobs.append((f"Boxplot of {c}", lambda fig, c=c: GL.box_v(fig, D(), [c])))
        return jobs
    G3 = _graphs(("g_hist", "Histogram of data", False), ("g_ivp", "Individual value plot", False), ("g_box", "Boxplot of data", False))

    # ---------- File / Edit ----------
    def new_ws(): app.new_ws()
    file_ = [("New Project", app.new_project), ("New Worksheet", new_ws), None, ("Open Project...", app.open_project), ("Open Worksheet...", app.open_file, "Ctrl+O"), None, ("Save Project", app.save_project, "Ctrl+S"), ("Save Project As...", app.save_project_as),
             ("Save Current Worksheet As...", app.save_ws), None, ("Print Session Window...", app.print_session), None, ("Exit", app.destroy)]
    edit = [("Undo", app.do_undo, "Ctrl+Z"), ("Redo", app.do_redo, "Ctrl+Y"), None, ("Edit Last Dialog", app.edit_last, "Ctrl+E"), None, ("Cut Cells", lambda: (app.sheet.copy(), app.sheet.clear_cell())), ("Copy Cells", lambda: app.sheet.copy()),
            ("Paste Cells", lambda: app.sheet.paste()), ("Clear Cells", lambda: app.sheet.clear_cell()), None, ("Find...", app.find, "Ctrl+F"), None, ("Clear Session Window", lambda: app.out.delete("1.0", "end"))]

    # ---------- Data ----------
    def subset(r): sub = D().query(r["cond"], engine="python").reset_index(drop=True); app.new_ws(sub); return None
    def sort(r): app.snap(); app.df = D().sort_values(r["by"], ascending=not r["desc"]).reset_index(drop=True); app.refresh()
    def drop_na(): app.snap(); n = len(D()); app.df = D().dropna(how="all").dropna().reset_index(drop=True); app.refresh(); app.note(f"Deleted {n - len(app.df)} row(s) containing missing values.")
    def erase(r): app.snap(); app.df = D().drop(columns=r["vars"]); app.refresh()
    def copycols(r): [app.store(c + "_copy", D()[c].values) for c in r["vars"]]
    def stack(r):
        cols = r["vars"]; app.store(r["out"] or "Stacked", np.concatenate([D()[c].values.astype(object) for c in cols])); app.store(r["sub"] or "Subscripts", np.repeat(cols, len(D())))
    def unstack(r):
        for lv, g in D().groupby(r["sub"]): app.store(f"{r['x']}_{lv}", g[r["x"]].reset_index(drop=True))
    def dtype(r):
        app.snap()
        for c in r["vars"]: app.df[c] = pd.to_numeric(D()[c], errors="coerce") if r["to"] == "Numeric" else D()[c].map(lambda v: v if pd.isna(v) else (f"{v:g}" if isinstance(v, (int, float, np.number)) else str(v)))
        app.refresh()
    def code(r):
        m = dict(p.split("=", 1) for p in r["map"].replace(";", ",").split(",") if "=" in p); m = {a.strip(): b.strip() for a, b in m.items()}; s = D()[r["x"]].map(lambda v: m.get(f"{v:g}" if isinstance(v, (int, float, np.number)) else str(v), v))
        conv = pd.to_numeric(s, errors="coerce"); app.store(r["out"] or r["x"] + "_coded", conv if conv.notna().sum() == s.notna().sum() else s)
    data = [("Subset Worksheet...", stat("Subset Worksheet", [("cond", "Condition  (e.g.  Height > 165 and Group == 'A'):", "text", "")], subset)), None,
            ("Sort...", stat("Sort", [("by", "Sort column(s):", "any", True), ("desc", "Descending order", "check", False)], sort)),
            ("Rank...", stat("Rank", [("x", "Rank values in:", "num"), ("out", "Store ranks in:", "text", "")], lambda r: app.store(r["out"] or "Rank_" + r["x"], D()[r["x"]].rank()))),
            ("Delete Rows With Missing Values", drop_na), ("Erase Variables...", stat("Erase Variables", [("vars", "Columns to erase:", "any", True)], erase)), None,
            ("Copy", [("Columns to Columns...", stat("Copy Columns", [("vars", "Copy from columns:", "any", True)], copycols))]),
            ("Stack", [("Columns...", stat("Stack Columns", [("vars", "Stack the following columns:", "any", True), ("out", "Store stacked data in:", "text", "Stacked"), ("sub", "Store subscripts in:", "text", "Subscripts")], stack))]),
            ("Unstack Columns...", stat("Unstack Columns", [("x", "Unstack the data in:", "any"), ("sub", "Using subscripts in:", "any")], unstack)), None,
            ("Change Data Type", [("Numeric <-> Text...", stat("Change Data Type", [("vars", "Columns:", "any", True), ("to", "Change to:", "combo", ["Text", "Numeric"])], dtype))]),
            ("Code", [("Numeric to Numeric / Text to Text...", stat("Code", [("x", "Code data from columns:", "any"), ("out", "Store coded data in:", "text", ""), ("map", "Recode  old=new, old=new, ...:", "text", "")], code))])]

    # ---------- Calc ----------
    def calc(r):
        env = {c: D()[c] for c in D().columns if c.isidentifier()}; env.update({f"C{i+1}": D()[c] for i, c in enumerate(D().columns)})
        fn = dict(ln=np.log, log=np.log10, sqrt=np.sqrt, abs=np.abs, exp=np.exp, sin=np.sin, cos=np.cos, tan=np.tan, round=np.round, mean=lambda s: s.mean(), stdev=lambda s: s.std(), sum=lambda s: s.sum(), min=lambda s: s.min(), max=lambda s: s.max(), median=lambda s: s.median())
        env.update(fn); env.update({k.upper(): v for k, v in fn.items()}); res = eval(r["expr"], {"__builtins__": {}}, env); app.store(r["out"], pd.Series(res, index=D().index))
    def patterned(r):
        seq = np.arange(r["a"], r["b"] + r["step"] / 2, r["step"]); app.store(r["out"], np.tile(np.repeat(seq, int(r["each"] or 1)), int(r["seq"] or 1)))
    def rowstat(r):
        f = {"Sum": "sum", "Mean": "mean", "Standard deviation": "std", "Minimum": "min", "Maximum": "max", "Median": "median", "N nonmissing": "count"}[r["stat"]]; app.store(r["out"], getattr(D()[r["vars"]], f)(axis=1))
    def colstat(r):
        t, b, v = so.col_stat(D(), r["x"], r["stat"]); app.say(t, b)
        if r["out"]: app.store(r["out"], [v])
    def standardize(r):
        for c in r["vars"]: app.store(r["pre"] + c, (D()[c] - D()[c].mean()) / D()[c].std())
    def rnd(kind):
        def go(r):
            n = int(r["n"] or 0); rs = np.random
            if D().empty: app.df = pd.DataFrame(index=range(n))
            v = {"Normal": lambda: rs.normal(r["a"] or 0, r["b"] if r["b"] is not None else 1, n), "Uniform": lambda: rs.uniform(r["a"] or 0, r["b"] if r["b"] is not None else 1, n), "Integer": lambda: rs.randint(int(r["a"] or 0), int(r["b"] or 10) + 1, n),
                 "Binomial": lambda: rs.binomial(int(r["a"] or 1), r["b"] if r["b"] is not None else .5, n), "Poisson": lambda: rs.poisson(r["a"] or 1, n)}[kind](); app.store(r["out"] or "C1", v)
        lab = {"Normal": ("Mean:", "Standard deviation:"), "Uniform": ("Lower endpoint:", "Upper endpoint:"), "Integer": ("Minimum value:", "Maximum value:"), "Binomial": ("Number of trials:", "Event probability:"), "Poisson": ("Mean:", "")}[kind]
        fl = [("n", "Number of rows of data to generate:", "float", 100), ("out", "Store in column(s):", "text", "C1"), ("a", lab[0], "float", 0 if kind != "Poisson" else 1)] + ([("b", lab[1], "float", 1)] if lab[1] else [("b", "", "float", None)][:0])
        return (kind + "...", stat(f"{kind} Distribution", fl, go, need=False))
    def dist_item(name):
        l1, l2 = so.DISTS[name]; disc = name in ("Binomial", "Poisson"); kinds = ["Probability" if disc else "Probability density", "Cumulative probability", "Inverse cumulative probability"]
        fl = [("kind", "Compute:", "combo", kinds), ("p1", l1 + ":", "float", 0 if name == "Normal" else 1)] + ([("p2", l2 + ":", "float", 1)] if l2 else []) + [("x", "Input constant:", "float", None)]
        return (name + "...", stat(f"{name} Distribution", fl, lambda r: so.distcalc(r["kind"], name, r.get("p1"), r.get("p2"), r["x"]), need=False))
    calc_ = [("Calculator...", stat("Calculator", [("out", "Store result in variable:", "text", "C_new"), ("expr", "Expression  (e.g.  LN(Weight) / Height * 2):", "text", "")], calc)), None,
             ("Make Patterned Data", [("Simple Set of Numbers...", stat("Simple Set of Numbers", [("out", "Store patterned data in:", "text", "Pattern"), ("a", "From first value:", "float", 1), ("b", "To last value:", "float", 10), ("step", "In steps of:", "float", 1), ("each", "Number of times to list each value:", "float", 1), ("seq", "Number of times to list the whole sequence:", "float", 1)], patterned, need=False))]),
             ("Row Statistics...", stat("Row Statistics", [("stat", "Statistic:", "combo", ["Sum", "Mean", "Standard deviation", "Minimum", "Maximum", "Median", "N nonmissing"]), ("vars", "Input variables:", "num", True), ("out", "Store result in:", "text", "RowStat")], rowstat)),
             ("Column Statistics...", stat("Column Statistics", [("stat", "Statistic:", "combo", ["Mean", "Sum", "StDev", "Minimum", "Maximum", "Median", "N total", "N nonmissing", "N missing", "Sum of squares"]), ("x", "Input variable:", "num"), ("out", "Store result in (optional):", "text", "")], colstat)),
             ("Standardize...", stat("Standardize", [("vars", "Input column(s):", "num", True), ("pre", "Store results in columns named:  prefix", "text", "Z_")], standardize)), None,
             ("Random Data", [rnd(k) for k in ("Normal", "Uniform", "Integer", "Binomial", "Poisson")]), ("Probability Distributions", [dist_item(n) for n in so.DISTS])]

    # ---------- Stat ----------
    def regress(r):
        t, b = so.regression(D(), r["y"], r["x"])
        if r.get("s_fits") or r.get("s_res"):
            d = D()[[r["y"]] + r["x"]].dropna(); X = np.column_stack([np.ones(len(d))] + [d[c].values for c in r["x"]]); co, *_ = np.linalg.lstsq(X, d[r["y"]].values, rcond=None); fit = pd.Series(X @ co, index=d.index).reindex(D().index)
            if r.get("s_fits"): app.store("FITS", fit.values)
            if r.get("s_res"): app.store("RESI", (D()[r["y"]] - fit).values)
        return t, b
    def reg_graphs(r):
        y, x = r["y"], r["x"]; j = []
        if r.get("g_four"): j.append(("Residual Plots for " + y, lambda fig: G.residual_plots(fig, D(), y, x)))
        for k, n in (("g_hist", "hist"), ("g_nplot", "nplot"), ("g_fits", "fits"), ("g_order", "order")):
            if r.get(k): j.append((f"Residual plot ({n})", lambda fig, n=n: GL.residual_single(fig, D(), y, x, n)))
        return j
    def fitted(r):
        deg = {"Linear": 1, "Quadratic": 2, "Cubic": 3}[r["type"]]
        if deg == 1: return so.regression(D(), r["y"], [r["x"]])
        d = D()[[r["x"], r["y"]]].dropna(); c = np.polyfit(d[r["x"]], d[r["y"]], deg); fit = np.polyval(c, d[r["x"]]); sse = ((d[r["y"]] - fit) ** 2).sum(); sst = ((d[r["y"]] - d[r["y"]].mean()) ** 2).sum(); n = len(d); dfe = n - deg - 1; ssr = sst - sse
        eq = f"{r['y']} = {c[-1]:.5g}" + "".join(f" {'+' if c[-1-k] >= 0 else '-'} {abs(c[-1-k]):.5g} {r['x']}" + ("" if k == 1 else f"**{k}") for k in range(1, deg + 1)); f = ssr / deg / (sse / dfe)
        return f"Polynomial Regression Analysis: {r['y']} versus {r['x']}", f"The regression equation is\n{eq}\n\nS = {np.sqrt(sse/dfe):.5g}   R-Sq = {ssr/sst*100:.1f}%   R-Sq(adj) = {(1-(sse/dfe)/(sst/(n-1)))*100:.1f}%\n\nAnalysis of Variance\n" + so.tbl(["Source", "DF", "SS", "MS", "F", "P"], [["Regression", deg, so.fmt(ssr), so.fmt(ssr / deg), f"{f:.2f}", so.pv(st.f.sf(f, deg, dfe))], ["Error", dfe, so.fmt(sse), so.fmt(sse / dfe), "", ""], ["Total", n - 1, so.fmt(sst), "", "", ""]])
    def anova1(r):
        t, b = so.anova(D(), r["y"], r["x"])
        if r.get("tukey") and D()[r["x"]].nunique() > 2: b += "\n\n## " + so.tukey(D(), r["y"], r["x"], r.get("conf") or 95.0)[0] + "\n" + so.tukey(D(), r["y"], r["x"], r.get("conf") or 95.0)[1]
        return t, b
    def anova_graphs(r):
        y, x = r["y"], r["x"]; j = []
        if r.get("g_box"): j.append((f"Boxplot of {y} by {x}", lambda fig: GL.box_v(fig, D(), [y], x)))
        if r.get("g_ivp"): j.append((f"Individual Value Plot of {y} vs {x}", lambda fig: GL.ivp_v(fig, D(), [y], x)))
        if r.get("g_int"): j.append((f"Interval Plot of {y} vs {x}", lambda fig: GL.interval_v(fig, D(), [y], x)))
        if r.get("g_res"):
            def res(fig): d = pd.get_dummies(D()[[x]].astype(str), drop_first=True).astype(float); t = pd.concat([D()[[y]], d], axis=1); G.residual_plots(fig, t, y, list(d.columns))
            j.append((f"Residual Plots for {y}", res))
        return j
    def imr_graphs(r): return [(f"I-MR Chart of {c}", lambda fig, c=c: G.imr_chart(fig, D(), c)) for c in r["vars"]]
    def imr_say(r): [app.say(*so.imr_tests(D()[c].dropna(), c)) for c in r["vars"]]
    def pareto_item(): return stat("Pareto Chart", [("x", "Defects or attribute data in:", "any")], lambda r: None, graphs=lambda r: [(f"Pareto Chart of {r['x']}", lambda fig: G.pareto(fig, D(), r["x"]))])
    def attr(kind):
        fl = [("counts", "Variable (defectives/defects):", "num"), ("sizes", "Subgroup sizes in (column):", "optnum"), ("size", "or constant subgroup size:", "float", None)] if kind != "C" else [("counts", "Variable (defects):", "num")]
        return (f"{kind} Chart...", stat(f"{kind} Chart", fl, lambda r: so.attr_tests(kind, D(), r["counts"], r.get("sizes"), r.get("size")), graphs=lambda r: [(f"{kind} Chart of {r['counts']}", lambda fig: GL.attr_chart(fig, D(), kind, r["counts"], r.get("sizes"), r.get("size")))]))
    sub_t = [("Statistics...", so.stat_fields()), _graphs(("g_hist", "Histogram of data", False), ("g_histfit", "Histogram of data, with normal curve", False), ("g_ivp", "Individual value plot", False), ("g_box", "Boxplot of data", False))]
    basic = [("Display Descriptive Statistics...", stat("Display Descriptive Statistics", [("vars", "Variables:", "num", True), ("by", "By variables (optional):", "opt")], C(so.descriptive), sub_t, lambda r: qg(r, r["vars"]))),
        ("Store Descriptive Statistics...", stat("Store Descriptive Statistics", [("vars", "Variables:", "num", True), ("by", "By variables (optional):", "opt")], lambda r: [app.store(k, v) for k, v in so.store_descriptive(D(), r["vars"], r.get("by"), **{k: v for k, v in r.items() if k.startswith("s") and k[1:].isdigit()}).items()] and None, [sub_t[0]])),
        ("Graphical Summary...", stat("Graphical Summary", [("vars", "Variables:", "num", True)], lambda r: None, graphs=lambda r: [(f"Summary for {c}", lambda fig, c=c: G.graphical_summary(fig, D(), c)) for c in r["vars"]])), None,
        ("1-Sample Z...", stat("1-Sample Z", [("x", "Samples in columns:", "num", True), ("sigma", "Standard deviation:", "float", None), ("mu", "Test mean:", "float", 0)], C(so.z1), [OPT_T, G3], lambda r: qg(r, r["x"]))),
        ("1-Sample t...", stat("1-Sample t", [("x", "Samples in columns:", "num", True), ("mu", "Test mean:", "float", 0)], C(so.t1), [OPT_T, G3], lambda r: qg(r, r["x"]))),
        ("2-Sample t...", stat("2-Sample t", [("s1", "Samples (response) / Sample 1:", "num"), ("s2", "Sample 2 (if in a separate column):", "optnum"), ("grp", "Sample IDs (if both samples are in one column):", "opt")], C(so.t2),
            [("Options...", [("conf", "Confidence level:", "float", 95.0), ("diff", "Test difference:", "float", 0), ("alt", ALT[0], "combo", ALT[2]), ("pooled", "Assume equal variances", "check", False)]), _graphs(("g_ivp", "Individual value plot", False), ("g_box", "Boxplot of data", False))],
            lambda r: ([(f"Individual Value Plot of {r['s1']}", lambda fig: GL.ivp_v(fig, D(), [r["s1"]], r["grp"]))] if r.get("g_ivp") and r.get("grp") else [(f"Individual Value Plot", lambda fig: GL.ivp_v(fig, D(), [r["s1"], r["s2"]]))] if r.get("g_ivp") and r.get("s2") else []) + ([(f"Boxplot", lambda fig: GL.box_v(fig, D(), [r["s1"]], r["grp"]) if r["grp"] else GL.box_v(fig, D(), [r["s1"], r["s2"]]))] if r.get("g_box") else []))),
        ("Paired t...", stat("Paired t", [("x", "Sample 1:", "num"), ("y", "Sample 2:", "num")], C(so.paired), [("Options...", [("conf", "Confidence level:", "float", 95.0), ("diff", "Test mean difference:", "float", 0), ("alt", ALT[0], "combo", ALT[2])]), G3],
            lambda r: [(t, (lambda fig, f=f: f(fig, pd.DataFrame({"Differences": D()[r["x"]] - D()[r["y"]]}), "Differences"))) for t, f in ((("Histogram of Differences", lambda fig, d, c: G.histogram(fig, d, c, False)),) if r.get("g_hist") else ()) + ((("Individual Value Plot of Differences", lambda fig, d, c: GL.ivp_v(fig, d, [c])),) if r.get("g_ivp") else ()) + ((("Boxplot of Differences", lambda fig, d, c: GL.box_v(fig, d, [c])),) if r.get("g_box") else ())])),
        ("1 Proportion...", stat("1 Proportion", [("x", "Samples in columns (optional):", "opt"), ("event", "Event (value in column):", "text", ""), ("events", "or Number of events:", "float", None), ("trials", "Number of trials:", "float", None)], C(so.prop1), [("Options...", [("p0", "Test proportion:", "float", 0.5), ("conf", "Confidence level:", "float", 95.0), ("alt", ALT[0], "combo", ALT[2])])], need=False)),
        ("2 Proportions...", stat("2 Proportions", [("e1", "First sample - number of events:", "float", None), ("n1", "First sample - number of trials:", "float", None), ("e2", "Second sample - number of events:", "float", None), ("n2", "Second sample - number of trials:", "float", None)], C(so.prop2), [("Options...", [("conf", "Confidence level:", "float", 95.0), ("diff", "Test difference:", "float", 0), ("alt", ALT[0], "combo", ALT[2])])], need=False)),
        ("2 Variances...", stat("2 Variances", [("y", "Response:", "num"), ("x", "Factor (2 levels):", "any")], C(so.equal_var), (), lambda r: [("Test for Equal Variances", lambda fig: GL.equalvar_plot(fig, D(), r["y"], r["x"]))])), None,
        ("Correlation...", stat("Correlation", [("vars", "Variables:", "num", True)], C(so.correlation))), ("Covariance...", stat("Covariance", [("vars", "Variables:", "num", True)], C(so.covariance))),
        ("Normality Test...", stat("Normality Test", [("vars", "Variable:", "num", True)], lambda r: None, graphs=lambda r: [(f"Probability Plot of {c}", lambda fig, c=c: GL.prob_v(fig, D(), [c])) for c in r["vars"]]))]
    reg = [("Regression", [("Fit Regression Model...", stat("Fit Regression Model", [("y", "Responses:", "num"), ("x", "Continuous predictors:", "num", True)], regress,
            [_graphs(("g_four", "Four in one", True), ("g_hist", "Histogram of residuals", False), ("g_nplot", "Normal probability plot of residuals", False), ("g_fits", "Residuals versus fits", False), ("g_order", "Residuals versus order", False)), ("Storage...", [("s_fits", "Fits", "check", False), ("s_res", "Residuals", "check", False)])], reg_graphs)),
            ("Fitted Line Plot...", stat("Fitted Line Plot", [("y", "Response (Y):", "num"), ("x", "Predictor (X):", "num"), ("type", "Type of regression model:", "combo", ["Linear", "Quadratic", "Cubic"])], fitted, (), lambda r: [("Fitted Line Plot", lambda fig: GL.poly_fit(fig, D(), r["y"], r["x"], {"Linear": 1, "Quadratic": 2, "Cubic": 3}[r["type"]]))]))])]
    anov = [("One-Way...", stat("One-Way Analysis of Variance", [("y", "Response:", "num"), ("x", "Factor:", "any")], anova1, [("Comparisons...", [("tukey", "Tukey", "check", True), ("conf", "Family confidence level:", "float", 95.0)]), _graphs(("g_box", "Boxplots of data", True), ("g_ivp", "Individual value plot", False), ("g_int", "Interval plot", False), ("g_res", "Residual plots, four in one", False))], anova_graphs)),
            ("Two-Way...", stat("Two-Way Analysis of Variance", [("y", "Response:", "num"), ("a", "Row factor:", "any"), ("b", "Column factor:", "any")], C(so.two_way))),
            ("Test for Equal Variances...", stat("Test for Equal Variances", [("y", "Response:", "num"), ("x", "Factors:", "any")], C(so.equal_var), [("Options...", [("conf", "Confidence level:", "float", 95.0)])], lambda r: [("Test for Equal Variances", lambda fig: GL.equalvar_plot(fig, D(), r["y"], r["x"], r.get("conf") or 95.0))])),
            ("Main Effects Plot...", stat("Main Effects Plot", [("y", "Responses:", "num"), ("f", "Factors:", "any", True)], lambda r: None, graphs=lambda r: [("Main Effects Plot", lambda fig: GL.effects(fig, D(), r["y"], r["f"]))])),
            ("Interactions Plot...", stat("Interactions Plot", [("y", "Responses:", "num"), ("f", "Factors (2):", "any", True)], lambda r: None, graphs=lambda r: [("Interaction Plot", lambda fig: GL.effects(fig, D(), r["y"], r["f"], True))]))]
    ctrl = [("Variables Charts for Subgroups", [("Xbar-R...", stat("Xbar-R Chart", [("x", "Observations in one column:", "num"), ("size", "Subgroup size:", "float", 5)], lambda r: so.xbar_r_tests(D(), r["x"], r["size"]), graphs=lambda r: [(f"Xbar-R Chart of {r['x']}", lambda fig: GL.xbar_r(fig, D(), r["x"], r["size"]))]))]),
            ("Variables Charts for Individuals", [("I-MR...", stat("I-MR Chart", [("vars", "Variables:", "num", True)], lambda r: imr_say(r), graphs=imr_graphs))]), ("Attributes Charts", [attr(k) for k in ("P", "NP", "C", "U")])]
    qual = [("Run Chart...", stat("Run Chart", [("x", "Single column:", "num")], lambda r: None, graphs=lambda r: [(f"Run Chart of {r['x']}", lambda fig: G.run_chart(fig, D(), r["x"]))])), ("Pareto Chart...", pareto_item()),
            ("Capability Analysis", [("Normal...", stat("Capability Analysis (Normal)", [("x", "Single column:", "num"), ("size", "Subgroup size:", "float", 1), ("lsl", "Lower spec:", "float", None), ("usl", "Upper spec:", "float", None)], C(so.capability), (), lambda r: [("Process Capability", lambda fig: G.capability(fig, D(), r["x"], r["lsl"], r["usl"], r["size"]))]))])]
    tabs = [("Cross Tabulation and Chi-Square...", stat("Cross Tabulation and Chi-Square", [("r", "For rows:", "cat"), ("c", "For columns:", "cat")], C(so.crosstab), [("Display...", [("counts", "Counts", "check", True), ("rowp", "Row percents", "check", False), ("colp", "Column percents", "check", False), ("totp", "Total percents", "check", False), ("expected", "Expected cell counts", "check", False), ("chi", "Chi-Square analysis", "check", True)])])),
            ("Tally Individual Variables...", stat("Tally Individual Variables", [("vars", "Variables:", "any", True)], C(so.tally)))]
    nonp = [("1-Sample Wilcoxon...", stat("1-Sample Wilcoxon", [("x", "Variables:", "num"), ("mu", "Test median:", "float", 0)], C(so.wilcoxon1), [OPT_T])), ("Mann-Whitney...", stat("Mann-Whitney", [("s1", "First sample / Response:", "num"), ("s2", "Second sample (separate column):", "optnum"), ("grp", "Sample IDs (one-column form):", "opt")], C(so.mannwhitney), [OPT_T])),
            ("Kruskal-Wallis...", stat("Kruskal-Wallis", [("y", "Response:", "num"), ("x", "Factor:", "any")], C(so.kruskal)))]
    power = [("1-Sample t...", stat("Power and Sample Size for 1-Sample t", [("n", "Sample size:", "float", None), ("diff", "Differences:", "float", None), ("power", "Power values:", "float", None), ("sd", "Standard deviation:", "float", 1.0), ("alpha", "Significance level:", "float", 0.05)], C(so.power_t1), need=False))]
    stat_menu = [("Basic Statistics", basic), ("Regression", reg), ("ANOVA", anov), ("DOE", None), ("Control Charts", ctrl), ("Quality Tools", qual), ("Reliability/Survival", None), ("Multivariate", None), ("Time Series", None), ("Tables", tabs), ("Nonparametrics", nonp), ("EDA", None), ("Power and Sample Size", power)]

    # ---------- Graph (galleries) ----------
    A = app.gallery; SUBS = [LABELS_SUB, SCALE_SUB]; col = lambda k, lbl="Graph variables:": [("vars", lbl, "num", True)]
    def g_scatter():
        V = ["Simple", "With Regression", "With Connect Line", "With Groups", "With Regression and Groups", "With Connect and Groups"]
        f = lambda k: [("y", "Y variables:", "num", True), ("x", "X variables:", "num", True)] + ([("by", "Categorical variables for grouping:", "any")] if "Groups" in k else [])
        b = lambda k, r: [(f"Scatterplot of {y} vs {r['x'][min(i, len(r['x']) - 1)]}", lambda fig, y=y, x=r["x"][min(i, len(r["x"]) - 1)]: GL.scatter_v(fig, D(), y, x, k, r.get("by"))) for i, y in enumerate(r["y"])]; A("Scatterplots", V, f, b, SUBS)
    def g_hist():
        V = ["Simple", "With Fit", "With Outline and Groups", "With Fit and Groups"]; f = lambda k: col(k) + ([("by", "Categorical variables for grouping:", "any")] if "Groups" in k else [])
        A("Histograms", V, f, lambda k, r: [(f"Histogram of {c}", lambda fig, c=c: GL.hist_v(fig, D(), c, k, r.get("by"))) for c in r["vars"]], SUBS)
    def fam(title, fn, nm):
        V = ["One Y Simple", "One Y With Groups", "Multiple Y's Simple"]
        f = lambda k: [("vars", "Graph variables:", "num", True)] + ([("by", "Categorical variables for grouping:", "any")] if "Groups" in k else [])
        def b(k, r):
            if "Multiple" in k: return [(f"{nm} of " + ", ".join(r["vars"]), lambda fig: fn(fig, D(), r["vars"]))]
            return [(f"{nm} of {c}", lambda fig, c=c: fn(fig, D(), [c], r.get("by"))) for c in r["vars"]]
        A(nm + "s", V, f, b, SUBS)
    def g_bar():
        V = ["Counts of unique values: Simple", "Counts of unique values: Cluster", "Counts of unique values: Stack", "A function of a variable: Simple", "A function of a variable: Cluster", "A function of a variable: Stack"]
        def f(k):
            fl = [("cats", "Categorical variables:", "any", True)]
            if "function" in k: fl = [("func", "Function:", "combo", ["Mean", "Sum", "Median", "StDev", "Minimum", "Maximum", "Count"]), ("yv", "Graph variable:", "num")] + fl
            return fl
        A("Bar Charts", V, f, lambda k, r: [("Chart of " + ", ".join(r["cats"]), lambda fig: GL.bar_v(fig, D(), r["cats"], k.split(": ")[1], r.get("func") if "function" in k else None, r.get("yv")))], SUBS)
    def g_ts(): A("Time Series Plots", ["Simple", "Multiple"], lambda k: [("vars", "Series:", "num", True)], lambda k, r: [("Time Series Plot of " + ", ".join(r["vars"]), lambda fig: GL.ts_v(fig, D(), r["vars"], k))], SUBS)
    def g_prob(): A("Probability Plots", ["Single", "Multiple"], lambda k: col(k) + [("dist", "Distribution:", "combo", ["Normal", "Lognormal", "Weibull", "Exponential"])], lambda k, r: ([(f"Probability Plot of {c}", lambda fig, c=c: GL.prob_v(fig, D(), [c], r["dist"])) for c in r["vars"]] if k == "Single" else [("Probability Plot", lambda fig: GL.prob_v(fig, D(), r["vars"], r["dist"]))]), SUBS)
    def g_ecdf(): A("Empirical CDF", ["Single", "Multiple"], lambda k: col(k) + [("dist", "Distribution (optional):", "combo", ["None", "Normal"])], lambda k, r: ([(f"ECDF of {c}", lambda fig, c=c: GL.ecdf_v(fig, D(), [c], None if r["dist"] == "None" else r["dist"])) for c in r["vars"]] if k == "Single" else [("Empirical CDF", lambda fig: GL.ecdf_v(fig, D(), r["vars"], None if r["dist"] == "None" else r["dist"]))]), SUBS)
    def g_matrix(): A("Matrix Plots", ["Matrix of plots: Simple", "Each Y versus each X: Simple"], lambda k: [("vars", "Graph variables:" if "Matrix of" in k else "Y variables:", "num", True)] + ([("xs", "X variables:", "num", True)] if "Each" in k else []), lambda k, r: [("Matrix Plot", lambda fig: GL.matrix_v(fig, D(), r["vars"], r.get("xs")))], SUBS)
    def g_line(area):
        A("Area Graphs" if area else "Line Plots", ["Simple", "Multiple"], lambda k: [("y", "Y variables:", "num", True), ("x", "X variable:", "num")], lambda k, r: [("Area Graph" if area else "Line Plot", lambda fig: GL.line_v(fig, D(), r["y"], r["x"], area))], SUBS)
    def g_marg(): A("Marginal Plots", ["With Histograms", "With Boxplots", "With Dotplots"], lambda k: [("y", "Y variable:", "num"), ("x", "X variable:", "num")], lambda k, r: [(f"Marginal Plot of {r['y']} vs {r['x']}", lambda fig: GL.marginal(fig, D(), r["y"], r["x"], k))], SUBS)
    def g_3d(mode): A(mode, [mode], lambda k: [("z", "Z variable:", "num"), ("y", "Y variable:", "num"), ("x", "X variable:", "num")], lambda k, r: [(mode, lambda fig: GL.surface3d(fig, D(), r["z"], r["y"], r["x"], mode))], SUBS)
    def g_dist():
        f = lambda k: [("dist", "Distribution:", "combo", list(so.DISTS)), ("p1", "Parameter 1  (Normal mean / DF / scale / lower / n / mean):", "float", 0), ("p2", "Parameter 2  (StDev / DF2 / upper / event prob.):", "float", 1)] + ([("tail", "Shaded area:", "combo", ["Left Tail", "Right Tail", "Middle"]), ("xval", "X value:", "float", None), ("prob", "or Probability:", "float", None)] if k == "View Probability" else [])
        A("Probability Distribution Plots", ["View Probability", "View Single"], f, lambda k, r: [("Distribution Plot", lambda fig: GL.dist_plot(fig, r["dist"], r["p1"], r["p2"], k, None, r.get("xval"), r.get("prob"), r.get("tail", "Left Tail")))], SUBS[:1], need=False)
    def g_pie(): P("Pie Chart", [("vars", "Categorical variable:", "any", True)], lambda r: None, [LABELS_SUB], lambda r: [(f"Pie Chart of {c}", lambda fig, c=c: G.pie(fig, D(), c)) for c in r["vars"]])
    def g_bubble(): P("Bubble Plot", [("y", "Y variable:", "num"), ("x", "X variable:", "num"), ("s", "Size variable:", "num")], lambda r: None, [LABELS_SUB], lambda r: [("Bubble Plot", lambda fig: GL.bubble(fig, D(), r["y"], r["x"], r["s"]))])
    def g_stem(): P("Stem-and-Leaf", [("x", "Graph variable:", "num")], C(so.stem_leaf))
    graph = [("Scatterplot...", g_scatter), ("Bubble Plot...", g_bubble), ("Marginal Plot...", g_marg), ("Matrix Plot...", g_matrix), ("3D Scatterplot...", lambda: g_3d("3D Scatterplot")), ("3D Surface Plot...", lambda: g_3d("3D Surface Plot")), ("Contour Plot...", lambda: g_3d("Contour Plot")), None,
             ("Histogram...", g_hist), ("Dotplot...", lambda: fam("Dotplot", GL.dot_v, "Dotplot")), ("Stem-and-Leaf...", g_stem), ("Probability Plot...", g_prob), ("Empirical CDF...", g_ecdf), ("Probability Distribution Plot...", g_dist), None,
             ("Boxplot...", lambda: fam("Boxplot", GL.box_v, "Boxplot")), ("Interval Plot...", lambda: fam("Interval Plot", GL.interval_v, "Interval Plot")), ("Individual Value Plot...", lambda: fam("Individual Value Plot", GL.ivp_v, "Individual Value Plot")), ("Line Plot...", lambda: g_line(False)), None,
             ("Bar Chart...", g_bar), ("Pie Chart...", g_pie), ("Time Series Plot...", g_ts), ("Area Graph...", lambda: g_line(True)), None, ("Graph All Columns (live)...", app.visualize)]

    # ---------- Editor / Help ----------
    def rows_dlg():
        n = simpledialog.askinteger("Insert Rows", "Number of rows to insert above the selected cell:", initialvalue=1, minvalue=1, parent=app)
        if n: app.insert_rows(n)
    def cols_dlg():
        n = simpledialog.askinteger("Insert Columns", "Number of columns to insert before the selected column:", initialvalue=1, minvalue=1, parent=app)
        if n: app.insert_cols(n)
    def help_():
        import tkinter as tk
        w = tk.Toplevel(app); w.title("ZamTab Help"); t = tk.Text(w, width=88, height=28, wrap="word", padx=10, pady=8); t.pack(); t.insert("end", "ZamTab - quick help\n\n1. Type or paste data into the worksheet (Ctrl+V works with Excel). Double-click the grey name row under C1, C2... to name a column.\n2. Stat and Graph menus open dialog boxes. Pick columns on the left, press Select (or double-click), then OK.\n3. Options..., Graphs..., Storage..., Statistics..., Labels... and Scale... buttons work like Minitab.\n4. Results appear in the Session window. Each graph opens in its own window (right-click a graph: Edit Title / Save).\n5. The 📈 button graphs everything for the chosen columns and updates live as you change the data.\n6. Ctrl+Z / Ctrl+Y undo and redo, Ctrl+E = Edit Last Dialog, Ctrl+F = Find.\n\nGreyed-out menu items are Minitab features not built into ZamTab yet."); t.config(state="disabled")
    return [("File", file_), ("Edit", edit), ("Data", data), ("Calc", calc_), ("Stat", stat_menu), ("Graph", graph),
            ("Editor", [("Insert Rows...", rows_dlg), ("Insert Columns...", cols_dlg), ("Delete Row", lambda: app.delete_row()), None, ("Rename Column...", lambda: app.rename_dialog()), ("Format Column...", None)]),
            ("Tools", [("Customize...", None), ("Options...", None), ("Stat Guide", None)]), ("Window", []), ("Help", [("Help", help_, "F1"), None, ("About ZamTab", lambda: messagebox.showinfo("About ZamTab", "ZamTab - a Minitab-style statistics program in Python.\nBuilt with pandas, SciPy, Matplotlib and Tkinter."))]),
            ("Assistant", [("Measurement Systems Analysis...", None), ("Capability Analysis...", None), ("Graphical Analysis...", None), ("Hypothesis Tests...", None), ("Control Charts...", None)])]
