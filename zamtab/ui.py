"""ZamTab main window - Minitab-17 layout: menus, toolbar, Project Manager, Session window, Worksheet, graph windows."""
import os, sys, json, time, tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np, pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from . import graphs as G, gallery as GL
from .sheet import Sheet
from .dialogs import McDialog, Gallery
from .commands import menu_spec

ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BG, TB, TITLE = "#f0f0f0", "#f5f6f8", "#3a73b8"
isnum = lambda s: pd.api.types.is_numeric_dtype(s)

class GraphWindow(tk.Toplevel):
    def __init__(self, app, title, jobs, deco=None, live=None):
        super().__init__(app); self.app, self.figs, self.deco, self.live, self.k = app, [], deco, live, max(app.winfo_fpixels("1i") / 96.0, 1.0)
        self.title(title); self.geometry(f"{int(780 * self.k)}x{int(600 * self.k)}"); self.configure(bg="white")
        try: self.iconphoto(False, app.icon)
        except Exception: pass
        m = tk.Menu(self); self.config(menu=m); f = tk.Menu(m, tearoff=0); m.add_cascade(label="File", menu=f); f.add_command(label="Save Graph As...", command=self.save); f.add_separator(); f.add_command(label="Close", command=self.destroy)
        e = tk.Menu(m, tearoff=0); m.add_cascade(label="Editor", menu=e); e.add_command(label="Edit Title...", command=self.edit_title); self.holder = tk.Frame(self, bg="white"); self.holder.pack(fill="both", expand=True)
        self.bind("<Button-3>", lambda ev: self.popup(ev)); self.build(jobs)
    def popup(self, ev):
        m = tk.Menu(self, tearoff=0); m.add_command(label="Edit Title...", command=self.edit_title); m.add_command(label="Save Graph As...", command=self.save); m.tk_popup(ev.x_root, ev.y_root)
    def build(self, jobs):
        for c in self.holder.winfo_children(): c.destroy()
        self.figs = []; sel = 0
        if len(jobs) == 1: self.make(self.holder, jobs[0][1])
        else:
            nb = ttk.Notebook(self.holder); nb.pack(fill="both", expand=True); self.nb = nb
            for t, fn in jobs:
                fr = tk.Frame(nb, bg="white")
                try: self.make(fr, fn)
                except Exception as e: fr.destroy(); self.app.note(f"Graph '{t}' skipped: {e}"); continue
                nb.add(fr, text=t[:30])
    def make(self, parent, fn):
        fig = Figure(figsize=(7.4, 5), dpi=int(100 * self.k), layout="constrained"); fn(fig); GL.decorate(fig, self.deco); self.figs.append(fig)
        cv = FigureCanvasTkAgg(fig, parent); cv.draw(); tb = NavigationToolbar2Tk(cv, parent, pack_toolbar=False); tb.pack(side="bottom", fill="x"); cv.get_tk_widget().pack(fill="both", expand=True)
    def cur(self): return self.figs[self.nb.index(self.nb.select())] if hasattr(self, "nb") and len(self.figs) > 1 and self.nb.winfo_exists() else self.figs[0]
    def save(self):
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")], parent=self)
        if p: self.cur().savefig(p, dpi=200)
    def edit_title(self):
        fig = self.cur(); ax = [a for a in fig.axes if a.axison][0]; t = simpledialog.askstring("Edit Title", "Title:", initialvalue=ax.get_title().replace("\n", " | "), parent=self)
        if t is not None: ax.set_title(t.replace(" | ", "\n")); fig.canvas.draw_idle()

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("ZamTab - Untitled"); self.k = max(self.winfo_fpixels("1i") / 96.0, 1.0); self.geometry(f"{int(1300 * self.k)}x{int(800 * self.k)}"); self.configure(bg=BG)
        try: self.icon = tk.PhotoImage(file=os.path.join(ROOT, "assets", "zamtab.png")); self.iconphoto(True, self.icon)
        except Exception: self.icon = None
        s = ttk.Style(self); s.theme_use("clam"); s.configure("Treeview", rowheight=int(20 * self.k), font=("Segoe UI", 9)); s.configure("TPanedwindow", background="#9aa5b5")
        self.sheets, self.cur, self.last, self.gwins, self.undo, self.redo_, self.lastcmd, self.proj, self.lastvals = [{"name": "Worksheet 1", "df": pd.DataFrame()}], 0, None, [], [], [], None, None, {}
        self.make_menu(); self.toolbar()
        self.status = tk.Label(self, anchor="w", bg="#e6e6e6", relief="sunken", bd=1, font=("Segoe UI", 9), padx=6); self.status.pack(side="bottom", fill="x")
        pw = ttk.PanedWindow(self, orient="horizontal"); pw.pack(fill="both", expand=True)
        pm = tk.Frame(pw, bg="white", width=int(210 * self.k)); pw.add(pm, weight=0); self.title_bar(pm, "Project Manager")
        self.pmt = ttk.Treeview(pm, show="tree"); self.pmt.pack(fill="both", expand=True); self.pmt.bind("<Double-1>", self.pm_click)
        right = ttk.PanedWindow(pw, orient="vertical"); pw.add(right, weight=1)
        sf = tk.Frame(right, bg="white"); right.add(sf, weight=3); self.title_bar(sf, "Session")
        self.out = tk.Text(sf, font=("Courier New", 10), bg="white", wrap="none", padx=10, pady=6, bd=0, cursor="arrow"); sy = tk.Scrollbar(sf, command=self.out.yview); sx = tk.Scrollbar(sf, orient="horizontal", command=self.out.xview)
        self.out.configure(yscrollcommand=sy.set, xscrollcommand=sx.set); sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x"); self.out.pack(fill="both", expand=True)
        self.out.tag_configure("res", font=("Segoe UI", 11, "bold")); self.out.tag_configure("cmd", font=("Segoe UI", 11, "bold"), foreground="#1f3d6b"); self.out.tag_configure("sub", font=("Courier New", 10, "bold"))
        self.out.bind("<Key>", lambda e: "break" if e.state & 4 == 0 else None)
        wf = tk.Frame(right, bg="white"); right.add(wf, weight=3); self.wt = self.title_bar(wf, "Worksheet 1 ***"); self.sheet = Sheet(wf, self); self.sheet.pack(fill="both", expand=True)
        for k, f in (("<Control-o>", self.open_file), ("<Control-s>", self.save_project), ("<Control-z>", self.do_undo), ("<Control-y>", self.do_redo), ("<Control-e>", self.edit_last), ("<Control-f>", self.find)): self.bind(k, lambda e, f=f: f())
        self.note("Welcome to ZamTab, press F1 for help."); self.refresh()

    # ---------- worksheets ----------
    @property
    def df(self): return self.sheets[self.cur]["df"]
    @df.setter
    def df(self, v): self.sheets[self.cur]["df"] = v
    @property
    def name(self): return self.sheets[self.cur]["name"]
    def snap(self): self.undo.append((self.cur, self.df.copy(), self.name)); self.undo = self.undo[-30:]; self.redo_.clear()
    def do_undo(self):
        if not self.undo: return
        c, d, n = self.undo.pop(); self.redo_.append((c, self.sheets[c]["df"].copy(), self.sheets[c]["name"])); self.sheets[c]["df"] = d; self.cur = c; self.refresh()
    def do_redo(self):
        if not self.redo_: return
        c, d, n = self.redo_.pop(); self.undo.append((c, self.sheets[c]["df"].copy(), n)); self.sheets[c]["df"] = d; self.cur = c; self.refresh()
    def new_ws(self, df=None, name=None):
        self.sheets.append({"name": name or f"Worksheet {len(self.sheets) + 1}", "df": df if df is not None else pd.DataFrame()}); self.cur = len(self.sheets) - 1; self.sheet.sel = (0, 0); self.refresh()
    def need(self):
        if self.df.empty: messagebox.showinfo("ZamTab", "The worksheet is empty.\nType or paste data into the worksheet, open a file (File > Open Worksheet), or load the sample (flask button)."); return False
        return True

    # ---------- chrome ----------
    def title_bar(self, parent, text):
        l = tk.Label(parent, text=text, bg=TITLE, fg="white", anchor="w", font=("Segoe UI", 9, "bold"), padx=8, pady=2); l.pack(fill="x"); return l
    def make_menu(self):
        m = tk.Menu(self); self.config(menu=m)
        def build(parent, items):
            for it in items:
                if it is None: parent.add_separator(); continue
                label, cmd = it[0], it[1]; acc = it[2] if len(it) > 2 else None
                if isinstance(cmd, list): sub = tk.Menu(parent, tearoff=0); parent.add_cascade(label=label, menu=sub); build(sub, cmd)
                elif cmd is None: parent.add_command(label=label, state="disabled")
                else: parent.add_command(label=label, command=cmd, accelerator=acc)
        for label, items in menu_spec(self):
            mm = tk.Menu(m, tearoff=0, postcommand=self.fill_window if label == "Window" else None); m.add_cascade(label=label, menu=mm)
            if label == "Window": self.wmenu = mm
            build(mm, items)
    def toolbar(self):
        tb = tk.Frame(self, bg=TB, bd=1, relief="groove"); tb.pack(fill="x")
        items = [("📂", self.open_file, "Open Worksheet"), ("💾", self.save_project, "Save Project"), ("🖨", self.print_session, "Print Session"), None, ("✂", lambda: (self.sheet.copy(), self.sheet.clear_cell()), "Cut"), ("⧉", lambda: self.sheet.copy(), "Copy"), ("📋", lambda: self.sheet.paste(), "Paste"), None,
                 ("↶", self.do_undo, "Undo"), ("↷", self.do_redo, "Redo"), None, ("fx", lambda: self.menu_call("Calc", "Calculator..."), "Calculator"), ("Σ", lambda: self.menu_call("Stat", "Basic Statistics", "Display Descriptive Statistics..."), "Descriptive Statistics"),
                 ("📈", self.visualize, "Graph all (live)"), None, ("🧪", self.sample, "Load sample data"), ("🧹", lambda: self.out.delete("1.0", "end"), "Clear Session")]
        for it in items:
            if it is None: tk.Frame(tb, width=1, bg="#bbb").pack(side="left", fill="y", padx=4, pady=3)
            else:
                b = tk.Button(tb, text=it[0], command=it[1], relief="flat", bg=TB, activebackground="#cfe0f7", font=("Segoe UI Emoji", 11), width=3); b.pack(side="left", pady=1); self.tip(b, it[2])
        tk.Label(tb, text="  Type data into the worksheet, then press  📈  to see all graphs update live", bg=TB, fg="#6a6a6a", font=("Segoe UI", 8)).pack(side="left")
    def tip(self, w, text):
        t = {"w": None}
        def show(e): t["w"] = tk.Toplevel(w); t["w"].wm_overrideredirect(True); t["w"].geometry(f"+{e.x_root + 10}+{e.y_root + 18}"); tk.Label(t["w"], text=text, bg="#ffffe1", relief="solid", bd=1, font=("Segoe UI", 8)).pack()
        def hide(e):
            if t["w"]: t["w"].destroy(); t["w"] = None
        w.bind("<Enter>", show); w.bind("<Leave>", hide)
    def menu_call(self, *path):
        top = self.nametowidget(self.cget("menu")); m = top
        for i, p in enumerate(path):
            for j in range(m.index("end") + 1):
                if m.type(j) in ("command", "cascade") and m.entrycget(j, "label") == p:
                    if i == len(path) - 1: m.invoke(j); return
                    m = m.nametowidget(m.entrycget(j, "menu")); break
    def fill_window(self):
        m = self.wmenu; m.delete(0, "end"); m.add_command(label="Session", command=lambda: self.out.focus_set()); m.add_command(label="Project Manager", command=lambda: self.pmt.focus_set())
        for i, s in enumerate(self.sheets): m.add_command(label=("► " if i == self.cur else "    ") + s["name"], command=lambda i=i: self.switch(i))
        self.gwins = [w for w in self.gwins if w.winfo_exists()]
        if self.gwins: m.add_separator()
        for w in self.gwins: m.add_command(label=w.title(), command=w.lift)
    def switch(self, i): self.cur = i; self.sheet.sel = (0, 0); self.refresh()
    def pm_click(self, e):
        s = self.pmt.selection()
        if not s: return
        t = s[0]
        if t.startswith("ws"): self.switch(int(t[2:]))
        elif t.startswith("g"):
            i = int(t[1:])
            if i < len(self.gwins) and self.gwins[i].winfo_exists(): self.gwins[i].lift()
        elif t == "sess": self.out.focus_set()

    # ---------- session ----------
    def note(self, text): self.out.insert("end", text + "\n\n"); self.out.see("end")
    def say(self, title, body):
        o = self.out
        if self.last != self.name: o.insert("end", f"Results for: {self.name}\n\n", "res"); self.last = self.name
        o.insert("end", title + "\n\n", "cmd")
        for ln in body.split("\n"): o.insert("end", (ln[3:] if ln.startswith("## ") else ln) + "\n", "sub" if ln.startswith("## ") else "")
        o.insert("end", "\n"); o.see("end")
    def print_session(self):
        p = os.path.join(tempfile.gettempdir(), "zamtab_session.txt"); open(p, "w", encoding="utf-8").write(self.out.get("1.0", "end"))
        try: os.startfile(p, "print")
        except Exception: messagebox.showinfo("ZamTab", f"Session saved to:\n{p}\nOpen it and print from there.")

    # ---------- refresh / data ----------
    def refresh(self):
        self.sheet.redraw(); self.wt.config(text=f"{self.name} ***"); self.title(f"ZamTab - {self.proj or 'Untitled'} - [{self.name}]")
        t = self.pmt; t.delete(*t.get_children()); t.insert("", "end", iid="sess", text="  📄 Session"); w = t.insert("", "end", iid="wss", text="  📁 Worksheets", open=True)
        for i, s in enumerate(self.sheets): t.insert(w, "end", iid=f"ws{i}", text=("  ► " if i == self.cur else "    ") + s["name"])
        g = t.insert("", "end", iid="grs", text="  📁 Graphs", open=True); self.gwins = [x for x in self.gwins if x.winfo_exists()]
        for i, x in enumerate(self.gwins): t.insert(g, "end", iid=f"g{i}", text="    " + x.title())
        t.insert("", "end", text="  📁 Related Documents")
        self.status.config(text=f"Current Worksheet: {self.name}        Rows: {len(self.df)}   Columns: {len(self.df.columns)}")
        if getattr(self, "_live_job", None): self.after_cancel(self._live_job)
        self._live_job = self.after(250, self.update_live)
    def set_df(self, df, name, path=None):
        self.snap(); df = df.copy(); df.columns = [str(c) for c in df.columns]; self.df = df.reset_index(drop=True); self.sheets[self.cur]["name"] = name; self.sheet.sel = (0, 0); self.sheet.selcol = None; self.refresh()
        self.note(f"Retrieving worksheet from file: '{path or name}'\n" + "\n".join(f"  C{i+1}{'' if isnum(df[c]) else '-T'}   {c}" for i, c in enumerate(df.columns)) + f"\n  {len(df)} rows")
    def set_cell(self, r, c, text):
        df = self.df; text = text.strip()
        if text == "" and (r >= len(df) or c >= len(df.columns)): return
        self.snap()
        while len(df.columns) <= c: df[f"C{len(df.columns) + 1}"] = np.nan
        if r >= len(df): self.df = df = df.reindex(range(r + 1))
        name = df.columns[c]; col = df[name].astype(object).copy(); col.iloc[r] = np.nan if text == "" else text; conv = pd.to_numeric(col, errors="coerce")
        df[name] = conv if (conv.notna() == col.notna()).all() else col.map(lambda v: v if isinstance(v, str) or pd.isna(v) else f"{v:g}"); self.refresh()
    def rename_col(self, c, val):
        df = self.df; val = val.strip() or f"C{c + 1}"
        while len(df.columns) <= c: df[f"C{len(df.columns) + 1}"] = np.nan
        old = df.columns[c]
        if val != old and val in df.columns: messagebox.showerror("ZamTab", f"A column named '{val}' already exists."); return
        self.snap(); df.rename(columns={old: val}, inplace=True); self.refresh()
    def rename_dialog(self):
        c = self.sheet.sel[1]; v = simpledialog.askstring("Rename Column", f"Name for column C{c+1}:", parent=self)
        if v is not None: self.rename_col(c, v)
    def store(self, name, values):
        self.snap(); s = pd.Series(values.values if hasattr(values, "values") else values)
        if len(s) > len(self.df): self.df = self.df.reindex(range(len(s)))
        self.df[name] = s.reindex(range(len(self.df))).values; self.refresh()
    def insert_rows(self, n=1):
        self.snap(); r = self.sheet.sel[0]; top, bot = self.df.iloc[:r], self.df.iloc[r:]; self.df = pd.concat([top, pd.DataFrame(index=range(int(n)), columns=self.df.columns), bot]).reset_index(drop=True); self.refresh()
    def delete_row(self):
        r = self.sheet.sel[0]
        if r < len(self.df): self.snap(); self.df = self.df.drop(self.df.index[r]).reset_index(drop=True); self.refresh()
    def insert_cols(self, n=1):
        self.snap(); c = self.sheet.sel[1]
        for i in range(int(n)): nm = f"C{len(self.df.columns) + 1}"; self.df.insert(min(c, len(self.df.columns)), nm, np.nan)
        self.refresh()
    def find(self):
        t = simpledialog.askstring("Find", "Find text in worksheet:", parent=self)
        if not t: return
        r0, c0 = self.sheet.sel; df = self.df; n = len(df) * len(df.columns); start = r0 * len(df.columns) + c0 + 1
        for k in range(n):
            idx = (start + k) % n; r, c = divmod(idx, len(df.columns))
            if t.lower() in str(df.iat[r, c]).lower(): self.sheet.sel = (r, c); self.sheet.selcol = None; self.sheet.redraw(); return
        messagebox.showinfo("Find", "Text not found.")
    def sample(self): self.set_df(pd.read_csv(os.path.join(ROOT, "data", "sample.csv")), "sample.csv")
    def try_(self, fn):
        try: fn()
        except Exception as ex: messagebox.showerror("ZamTab", str(ex))

    # ---------- file ----------
    def new_project(self):
        self.sheets, self.cur, self.proj, self.undo = [{"name": "Worksheet 1", "df": pd.DataFrame()}], 0, None, []; self.out.delete("1.0", "end"); self.last = None; [w.destroy() for w in self.gwins if w.winfo_exists()]; self.refresh()
    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Worksheets", "*.csv *.xlsx *.xls *.tsv *.txt"), ("All files", "*.*")])
        if p:
            def go():
                d = pd.read_excel(p) if p.lower().endswith(("xlsx", "xls")) else pd.read_csv(p, sep=None, engine="python")
                if self.df.empty: self.set_df(d, os.path.basename(p), p)
                else: self.new_ws(None, os.path.basename(p)); self.set_df(d, os.path.basename(p), p)
            self.try_(go)
    def save_ws(self):
        if not self.need(): return
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")])
        if p: self.try_(lambda: self.df.to_excel(p, index=False) if p.endswith("xlsx") else self.df.to_csv(p, index=False))
    def save_project(self, ask=False):
        p = self.proj if self.proj and not ask else filedialog.asksaveasfilename(defaultextension=".zamtab", filetypes=[("ZamTab project", "*.zamtab")])
        if p: self.try_(lambda: (json.dump({"sheets": [{"name": s["name"], "df": s["df"].to_json(orient="split")} for s in self.sheets], "session": self.out.get("1.0", "end")}, open(p, "w", encoding="utf-8")), setattr(self, "proj", p), self.refresh()))
    def save_project_as(self): self.save_project(True)
    def open_project(self):
        p = filedialog.askopenfilename(filetypes=[("ZamTab project", "*.zamtab")])
        if p:
            def go():
                d = json.load(open(p, encoding="utf-8")); self.sheets = [{"name": s["name"], "df": pd.read_json(__import__("io").StringIO(s["df"]), orient="split")} for s in d["sheets"]]; self.cur = 0; self.proj = p
                self.out.delete("1.0", "end"); self.out.insert("end", d.get("session", "")); self.refresh()
            self.try_(go)

    # ---------- command runners ----------
    def proc(self, title, fields, fn, subs=(), graphs=None, need=True, initial=None):
        if need and not self.need(): return
        d = McDialog(self, title, fields, subs, initial=initial or self.lastvals.get(title)); r = d.result
        if r is None: return
        self.lastvals[title] = d.raw; self.lastcmd = lambda: self.proc(title, fields, fn, subs, graphs, need, d.raw)
        def go():
            out = fn(r)
            if out: self.say(*out)
            for t, f in (graphs(r) if graphs else []): self.open_graph(t, [(t, f)], r)
        self.try_(go)
    def gallery(self, title, variants, fields_fn, build_fn, subs=(), initial=None, kind=None, need=True):
        if need and not self.need(): return
        g = Gallery(self, title, variants, kind); k = g.result
        if k is None: return
        d = McDialog(self, f"{title} - {k}", fields_fn(k), list(subs), initial=initial or self.lastvals.get(title + k)); r = d.result
        if r is None: return
        self.lastvals[title + k] = d.raw; self.lastcmd = lambda: self.gallery(title, variants, fields_fn, build_fn, subs, d.raw, k, need)
        self.try_(lambda: [self.open_graph(t, [(t, f)], r) for t, f in build_fn(k, r)])
    def edit_last(self):
        if self.lastcmd: self.lastcmd()
    def open_graph(self, title, jobs, deco=None, live=None):
        w = GraphWindow(self, title, jobs, deco, live); self.gwins.append(w); w.bind("<Destroy>", lambda e, w=w: self.after(50, self.refresh) if e.widget is w else None); self.refresh(); return w
    def visualize(self):
        if not self.need(): return
        d = McDialog(self, "Graph All (live)", [("x", "Variable (X):", "any"), ("y", "Second variable (optional):", "opt")], note="Every graph that fits your columns opens as tabs.\nThe graphs update automatically when you change the data."); r = d.result
        if r is None: return
        live = lambda: G.plan(self.df, r["x"], r["y"]); self.try_(lambda: self.open_graph("All graphs (live)", live(), None, live))
    def update_live(self):
        for w in list(self.gwins):
            if w.winfo_exists() and w.live:
                try: jobs = w.live()
                except Exception: continue
                if jobs: w.build(jobs)
