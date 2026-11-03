"""Minitab-17-style dialogs: column list + variable boxes + Options/Graphs/Storage sub-dialogs, and gallery chooser."""
import re, shlex
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

BG = "#f0f0f0"
COLK = ("num", "cat", "any", "opt", "optnum")
isnum = lambda s: pd.api.types.is_numeric_dtype(s)
LABELS_SUB = ("Labels...", [("t_title", "Title:", "text", ""), ("t_sub", "Subtitle:", "text", ""), ("t_foot", "Footnote:", "text", "")])
SCALE_SUB = ("Scale...", [("xmin", "X axis minimum:", "float", None), ("xmax", "X axis maximum:", "float", None), ("ymin", "Y axis minimum:", "float", None), ("ymax", "Y axis maximum:", "float", None), ("xlog", "Log scale for X", "check", False), ("ylog", "Log scale for Y", "check", False)])

class McDialog(tk.Toplevel):
    """fields: (key, label, kind[, extra]).  kind: num|cat|any|opt|optnum (column boxes, extra=True -> several columns), float|text (extra=default), check (extra=default), combo (extra=choices)."""
    def __init__(self, app, title, fields, subs=(), initial=None, note=None):
        super().__init__(app); self.title(title); self.configure(bg=BG); self.resizable(False, False); self.transient(app)
        self.app, self.fields, self.subs, self.result, self.cur, self.raw = app, list(fields), list(subs), None, None, {}; self.vars = {}
        for f in self.fields + [g for _, sf in self.subs for g in sf]: self.vars[f[0]] = self._var(f)
        for k, v in (initial or {}).items():
            if k in self.vars: self.vars[k][0].set(v)
        df = app.df; has_cols = any(f[2] in COLK for f in self.fields)
        if has_cols:
            left = tk.Frame(self, bg=BG); left.grid(row=0, column=0, padx=(10, 6), pady=10, sticky="ns")
            self.lb = tk.Listbox(left, width=24, height=14, exportselection=False, font=("Segoe UI", 9), activestyle="none", bg="white", selectbackground="#3a73b8"); sb = tk.Scrollbar(left, command=self.lb.yview); self.lb.configure(yscrollcommand=sb.set)
            for i, c in enumerate(df.columns): self.lb.insert("end", f"C{i+1}{'' if isnum(df[c]) else '-T'}   {c}")
            self.lb.pack(side="left", fill="y"); sb.pack(side="left", fill="y"); self.lb.bind("<Double-1>", lambda e: self.select())
        right = tk.Frame(self, bg=BG); right.grid(row=0, column=1, padx=(6, 12), pady=10, sticky="n"); r = 0
        if note: tk.Label(right, text=note, bg=BG, justify="left", fg="#333").grid(row=r, column=0, sticky="w", pady=(0, 6)); r += 1
        self.build(right, self.fields, r, True)
        bt = tk.Frame(self, bg=BG); bt.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        if has_cols: tk.Button(bt, text="Select", width=9, command=self.select).pack(side="left")
        tk.Button(bt, text="Help", width=7, command=lambda: messagebox.showinfo("Help", "Double-click a column on the left (or press Select) to put it in the active box.\nYou can also type column names or C-numbers (C1, C2...).", parent=self)).pack(side="left", padx=8)
        tk.Button(bt, text="Cancel", width=9, command=self.destroy).pack(side="right"); tk.Button(bt, text="OK", width=9, command=self.ok, default="active").pack(side="right", padx=6)
        for lbl, sf in reversed(self.subs): tk.Button(bt, text=lbl, width=11, command=lambda l=lbl, s=sf: self.open_sub(l, s)).pack(side="right", padx=3)
        self.bind("<Return>", lambda e: self.ok()); self.bind("<Escape>", lambda e: self.destroy()); self.update_idletasks()
        self.geometry(f"+{app.winfo_rootx() + 150}+{app.winfo_rooty() + 80}"); self.grab_set(); self.wait_window()
    def _var(self, f):
        key, label, kind = f[:3]; extra = f[3] if len(f) > 3 else None
        if kind == "check": v = tk.BooleanVar(value=bool(extra))
        elif kind == "combo": v = tk.StringVar(value=extra[0])
        elif kind in COLK: v = tk.StringVar()
        else: v = tk.StringVar(value="" if extra is None else str(extra))
        return (v, kind, bool(extra) if kind in COLK else False)
    def build(self, parent, fields, r, track):
        for f in fields:
            key, label, kind = f[:3]; extra = f[3] if len(f) > 3 else None; v = self.vars[key][0]
            if kind == "check": tk.Checkbutton(parent, text=label, variable=v, bg=BG, anchor="w").grid(row=r, column=0, sticky="w", pady=2); r += 1; continue
            tk.Label(parent, text=label, bg=BG).grid(row=r, column=0, sticky="w", pady=(6, 0)); r += 1
            if kind == "combo": w = ttk.Combobox(parent, textvariable=v, values=extra, state="readonly", width=32)
            else: w = tk.Entry(parent, textvariable=v, width=36, font=("Segoe UI", 9))
            w.grid(row=r, column=0, sticky="ew", ipady=2); r += 1
            if track and kind in COLK:
                w.bind("<FocusIn>", lambda e, k=key: setattr(self, "cur", k))
                if self.cur is None: self.cur = key
    def open_sub(self, label, sf):
        snap = {f[0]: self.vars[f[0]][0].get() for f in sf}; w = tk.Toplevel(self); w.title(label.replace("...", "")); w.configure(bg=BG); w.transient(self); w.resizable(False, False)
        body = tk.Frame(w, bg=BG, padx=12, pady=10); body.pack(); self.build(body, sf, 0, False); bt = tk.Frame(w, bg=BG); bt.pack(fill="x", padx=12, pady=(0, 10))
        def cancel(): [self.vars[k][0].set(v) for k, v in snap.items()]; w.destroy()
        tk.Button(bt, text="Cancel", width=9, command=cancel).pack(side="right"); tk.Button(bt, text="OK", width=9, command=w.destroy).pack(side="right", padx=6)
        w.geometry(f"+{self.winfo_rootx() + 60}+{self.winfo_rooty() + 40}"); w.grab_set(); w.wait_window()
    def select(self):
        sel = self.lb.curselection()
        if not sel or not self.cur: return
        name = str(self.app.df.columns[sel[0]]); v, kind, multi = self.vars[self.cur]; q = f"'{name}'" if " " in name else name
        v.set((v.get() + " " + q).strip() if multi else q)
    def resolve(self, tok):
        cols = [str(c) for c in self.app.df.columns]
        if tok in cols: return tok
        m = re.fullmatch(r"[Cc](\d+)(?:-[TtDd])?", tok)
        return cols[int(m.group(1)) - 1] if m and 0 < int(m.group(1)) <= len(cols) else None
    def ok(self):
        out = {}; raw = {}
        for key, (v, kind, multi) in self.vars.items():
            raw[key] = v.get()
            if kind == "check": out[key] = bool(v.get()); continue
            s = v.get().strip() if isinstance(v.get(), str) else v.get()
            if kind == "float":
                try: out[key] = float(s) if s != "" else None
                except ValueError: messagebox.showerror("ZamTab", f"'{s}' is not a number.", parent=self); return
                continue
            if kind in ("text", "combo"): out[key] = s; continue
            try: toks = shlex.split(s)
            except ValueError: toks = s.split()
            if not toks:
                if kind in ("opt", "optnum"): out[key] = [] if multi else None; continue
                messagebox.showerror("ZamTab", "Please select a column for every required box.", parent=self); return
            names = []
            for t in toks:
                n = self.resolve(t)
                if n is None: messagebox.showerror("ZamTab", f"Column '{t}' not found.", parent=self); return
                if kind in ("num", "optnum") and not isnum(self.app.df[n]): messagebox.showerror("ZamTab", f"Column '{n}' is text; a numeric column is required.", parent=self); return
                if kind == "cat" and isnum(self.app.df[n]) and self.app.df[n].nunique() > 25: messagebox.showerror("ZamTab", f"Column '{n}' has too many different numbers to be categorical.", parent=self); return
                names.append(n)
            out[key] = names if multi else names[0]
        self.result, self.raw = out, raw; self.destroy()

class Gallery(tk.Toplevel):
    """Minitab-style graph gallery: choose Simple / With Groups / ..."""
    def __init__(self, app, title, variants, default=None):
        super().__init__(app); self.title(title); self.configure(bg=BG); self.resizable(False, False); self.transient(app); self.result = None
        tk.Label(self, text="Select a graph type:", bg=BG, anchor="w").pack(fill="x", padx=14, pady=(12, 4)); self.v = tk.StringVar(value=default or variants[0])
        box = tk.Frame(self, bg="white", bd=1, relief="sunken"); box.pack(padx=14, fill="x")
        for x in variants: tk.Radiobutton(box, text=x, variable=self.v, value=x, bg="white", anchor="w", activebackground="#cfe0f7").pack(fill="x", padx=6, pady=1)
        bt = tk.Frame(self, bg=BG); bt.pack(fill="x", padx=14, pady=12); tk.Button(bt, text="Cancel", width=9, command=self.destroy).pack(side="right"); tk.Button(bt, text="OK", width=9, command=self.ok).pack(side="right", padx=6)
        self.bind("<Return>", lambda e: self.ok()); self.geometry(f"+{app.winfo_rootx() + 200}+{app.winfo_rooty() + 100}"); self.grab_set(); self.wait_window()
    def ok(self): self.result = self.v.get(); self.destroy()
