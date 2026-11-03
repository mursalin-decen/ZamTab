"""Minitab-style Worksheet grid: C-labels, name row, row numbers, gridlines, in-cell editing."""
import re
import tkinter as tk
import numpy as np, pandas as pd

CW, RH, RNW, HH = 92, 20, 46, 20
GRID, HDR, SEL, BLUE = "#c8c8c8", "#ececec", "#d6e6f7", "#3a73b8"

class Sheet(tk.Frame):
    def __init__(self, master, app):
        global CW, RH, RNW, HH
        if not getattr(Sheet, "_scaled", False):
            k = max(master.winfo_fpixels("1i") / 96.0, 1.0); CW, RH, RNW, HH = [int(v * k) for v in (CW, RH, RNW, HH)]; Sheet._scaled = True
        super().__init__(master, bg="white"); self.app = app; self.sel = (0, 0); self.selcol = None; self.entry = None
        self.corner = tk.Canvas(self, width=RNW, height=HH * 2, bg=HDR, highlightthickness=0)
        self.hdr = tk.Canvas(self, height=HH * 2, bg=HDR, highlightthickness=0)
        self.rn = tk.Canvas(self, width=RNW, bg=HDR, highlightthickness=0)
        self.body = tk.Canvas(self, bg="white", highlightthickness=0)
        self.vb = tk.Scrollbar(self, orient="vertical", command=self.yview); self.hb = tk.Scrollbar(self, orient="horizontal", command=self.xview)
        self.corner.grid(row=0, column=0); self.hdr.grid(row=0, column=1, sticky="ew"); self.rn.grid(row=1, column=0, sticky="ns")
        self.body.grid(row=1, column=1, sticky="nsew"); self.vb.grid(row=1, column=2, sticky="ns"); self.hb.grid(row=2, column=1, sticky="ew")
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(1, weight=1)
        self.body.configure(xscrollcommand=self._xs, yscrollcommand=self._ys)
        self.body.bind("<Button-1>", self.click); self.body.bind("<Button-3>", self.ctx); self.rn.bind("<Button-3>", self.ctx); self.body.bind("<Double-1>", lambda e: self.edit()); self.hdr.bind("<Button-1>", self.click_hdr); self.hdr.bind("<Double-1>", self.dbl_hdr)
        self.body.bind("<Configure>", lambda e: self.redraw()); self.body.bind("<MouseWheel>", self.wheel); self.body.bind("<Button-4>", lambda e: self.wheel(e, 1)); self.body.bind("<Button-5>", lambda e: self.wheel(e, -1))
        for w in (self.body, self.hdr, self.rn):
            w.bind("<Key>", self.key); w.bind("<Control-c>", lambda e: self.copy()); w.bind("<Control-v>", lambda e: self.paste()); w.bind("<Delete>", lambda e: self.clear_cell())
        self.body.configure(takefocus=1); self.redraw()

    # ---- geometry ----
    def dims(self):
        df = self.app.df; return max(len(df) + 40, 60), max(len(df.columns) + 6, 20)
    def _xs(self, a, b): self.hb.set(a, b)
    def _ys(self, a, b): self.vb.set(a, b)
    def xview(self, *a): self.body.xview(*a); self.hdr.xview(*a); self.redraw()
    def yview(self, *a): self.body.yview(*a); self.rn.yview(*a); self.redraw()
    def wheel(self, e, d=None):
        d = d if d is not None else (1 if e.delta > 0 else -1); self.yview("scroll", -3 * d, "units")

    # ---- drawing ----
    def cell_text(self, v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "*" if isinstance(v, float) else ""
        if isinstance(v, (float, np.floating)): return str(int(v)) if float(v).is_integer() and abs(v) < 1e12 else f"{v:.6g}"
        return str(v)
    def label(self, ci):
        df = self.app.df
        if ci >= len(df.columns): return f"C{ci+1}"
        return f"C{ci+1}" + ("" if pd.api.types.is_numeric_dtype(df.iloc[:, ci]) else "-T")
    def name(self, ci):
        df = self.app.df; n = str(df.columns[ci]) if ci < len(df.columns) else ""; return "" if re.fullmatch(r"C\d+", n) else n
    def redraw(self):
        if self.entry: return
        df = self.app.df; nr, nc = self.dims(); W, H = nc * CW, nr * RH
        for c, reg in ((self.body, (0, 0, W, H)), (self.hdr, (0, 0, W, HH * 2)), (self.rn, (0, 0, RNW, H))): c.delete("all"); c.configure(scrollregion=reg)
        y0, x0 = int(self.body.canvasy(0)), int(self.body.canvasx(0)); vh, vw = self.body.winfo_height(), self.body.winfo_width()
        r0, r1 = max(y0 // RH - 1, 0), min((y0 + vh) // RH + 2, nr); c0, c1 = max(x0 // CW - 1, 0), min((x0 + vw) // CW + 2, nc)
        for ci in range(c0, c1):
            x = ci * CW; sc = (self.selcol == ci); bg = BLUE if sc else HDR; fg = "white" if sc else "black"
            self.hdr.create_rectangle(x, 0, x + CW, HH, fill=bg, outline=GRID); self.hdr.create_text(x + CW / 2, HH / 2, text=self.label(ci), fill=fg, font=("Segoe UI", 9, "bold"))
            self.hdr.create_rectangle(x, HH, x + CW, HH * 2, fill="white", outline=GRID); self.hdr.create_text(x + 5, HH * 1.5, text=self.name(ci), anchor="w", font=("Segoe UI", 9))
        for ri in range(r0, r1):
            y = ri * RH; self.rn.create_rectangle(0, y, RNW, y + RH, fill=HDR, outline=GRID); self.rn.create_text(RNW - 6, y + RH / 2, text=str(ri + 1), anchor="e", font=("Segoe UI", 9))
            for ci in range(c0, c1):
                x = ci * CW; fill = SEL if self.selcol == ci else "white"; self.body.create_rectangle(x, y, x + CW, y + RH, fill=fill, outline=GRID)
                if ri < len(df) and ci < len(df.columns):
                    v = df.iat[ri, ci]; t = self.cell_text(v)
                    if t: isn = isinstance(v, (int, float, np.number)); self.body.create_text(x + CW - 5 if isn else x + 5, y + RH / 2, text=t, anchor="e" if isn else "w", font=("Segoe UI", 9))
        r, c = self.sel; self.body.create_rectangle(c * CW + 1, r * RH + 1, (c + 1) * CW - 1, (r + 1) * RH - 1, outline="black", width=2)
        self.hdr.xview_moveto(self.body.xview()[0]); self.rn.yview_moveto(self.body.yview()[0])

    # ---- interaction ----
    def ctx(self, e):
        self.body.focus_set(); self.close_entry()
        if e.widget is self.body: self.sel = self.cell_at(e); self.selcol = None; self.redraw()
        m = tk.Menu(self, tearoff=0); a = self.app
        for lbl, cmd in (("Cut Cells", lambda: (self.copy(), self.clear_cell())), ("Copy Cells", self.copy), ("Paste Cells", self.paste), None, ("Clear Cells", self.clear_cell), ("Insert Rows", lambda: a.insert_rows(1)), ("Delete Row", a.delete_row), ("Insert Column", lambda: a.insert_cols(1)), None, ("Rename Column...", a.rename_dialog)):
            m.add_separator() if lbl is None else m.add_command(label=lbl, command=cmd)
        m.tk_popup(e.x_root, e.y_root)
    def cell_at(self, e): return int(self.body.canvasy(e.y) // RH), int(self.body.canvasx(e.x) // CW)
    def click(self, e): self.body.focus_set(); self.close_entry(); self.sel = self.cell_at(e); self.selcol = None; self.redraw()
    def click_hdr(self, e):
        self.body.focus_set(); self.close_entry(); c = int(self.hdr.canvasx(e.x) // CW)
        if e.y < HH: self.selcol = c; self.sel = (0, c)
        else: self.sel = (0, c); self.selcol = None
        self.redraw()
    def dbl_hdr(self, e):
        c = int(self.hdr.canvasx(e.x) // CW)
        if e.y >= HH: self.sel = (0, c); self.edit(name=True)
    def move(self, dr, dc):
        r, c = self.sel; nr, nc = self.dims(); self.sel = (min(max(r + dr, 0), nr - 1), min(max(c + dc, 0), nc - 1)); self.selcol = None
        top, bot = self.body.canvasy(0), self.body.canvasy(self.body.winfo_height())
        if self.sel[0] * RH < top: self.body.yview_moveto(self.sel[0] * RH / (nr * RH))
        elif (self.sel[0] + 1) * RH > bot: self.body.yview_moveto(((self.sel[0] + 2) * RH - self.body.winfo_height()) / (nr * RH))
        self.redraw()
    def key(self, e):
        k = e.keysym
        if k in ("Up", "Down", "Left", "Right"): self.move({"Up": -1, "Down": 1}.get(k, 0), {"Left": -1, "Right": 1}.get(k, 0))
        elif k in ("Return", "F2"): self.edit()
        elif k == "Tab": self.move(0, 1)
        elif len(e.char) == 1 and e.char.isprintable() and not (e.state & 4): self.edit(initial=e.char)
    def edit(self, initial=None, name=False):
        self.close_entry(); r, c = self.sel
        if name: x, y, w, h, cv, txt = c * CW, HH, CW, HH, self.hdr, self.name(c)
        else:
            x, y, w, h, cv = c * CW, r * RH, CW, RH, self.body; df = self.app.df
            txt = self.cell_text(df.iat[r, c]) if r < len(df) and c < len(df.columns) else ""
            if txt == "*": txt = ""
        e = tk.Entry(cv, font=("Segoe UI", 9), bd=1, relief="solid"); cv.create_window(x, y, window=e, anchor="nw", width=w, height=h, tags="ent")
        e.insert(0, initial if initial is not None else txt); e.focus_set(); e.icursor("end"); self.entry = e
        def done(_=None, move=True):
            if self.entry is None: return
            val = e.get(); self.entry = None; e.destroy(); cv.delete("ent")
            (self.app.rename_col(c, val) if name else self.app.set_cell(r, c, val))
            if move and not name: self.sel = (r + 1, c)
            self.redraw()
        e.bind("<Return>", done); e.bind("<Tab>", lambda ev: (done(move=False), self.move(0, 1), "break")[2]); e.bind("<FocusOut>", lambda ev: done(move=False)); e.bind("<Escape>", lambda ev: self.cancel())
    def cancel(self):
        e, self.entry = self.entry, None
        if e: e.destroy(); self.body.delete("ent"); self.hdr.delete("ent"); self.redraw()
    def close_entry(self):
        if self.entry: self.entry.event_generate("<FocusOut>")
    def clear_cell(self): self.app.set_cell(*self.sel, ""); self.redraw()
    def copy(self):
        r, c = self.sel; df = self.app.df
        if r < len(df) and c < len(df.columns): self.clipboard_clear(); self.clipboard_append(self.cell_text(df.iat[r, c]))
    def paste(self):
        try: txt = self.clipboard_get()
        except tk.TclError: return
        r0, c0 = self.sel
        for i, line in enumerate(txt.splitlines()):
            for j, v in enumerate(line.split("\t")): self.app.set_cell(r0 + i, c0 + j, v.strip())
        self.redraw()
