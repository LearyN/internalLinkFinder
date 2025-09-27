"""
Internal Link Finder — desktop GUI (Tkinter)

What it does
- Loads a CSV or Excel with at least two columns: one for page URL (default: "Address") and one for page content (default: "content").
- Builds a TF‑IDF model and computes cosine similarities between pages.
- Outputs candidate internal links for each page above a threshold, optionally limited to Top‑N per page.
- Saves results to CSV: source_url, candidate_url, similarity_score.

How to run (dev)
1) python -m venv .venv && .venv\Scripts\activate   (Windows)
2) pip install -r requirements.txt
3) python internal_link_finder.py

How to package to an .exe (Windows)
1) pip install pyinstaller
2) pyinstaller --onefile --noconsole --name "InternalLinkFinder" internal_link_finder.py
   (the .exe will be in dist/)

requirements.txt
-------------------------------------------------
pandas
scikit-learn
openpyxl

Note: Tkinter is part of standard Python on Windows/macOS. If missing on Linux, install tk.
"""

import os
import sys
import math
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import List, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

APP_TITLE = "Internal Link Finder"
DEFAULT_URL_COL = "Address"
DEFAULT_CONTENT_COL = "content"

# ------------------------
# Utility functions
# ------------------------

def log(msg: str, widget: tk.Text):
    widget.configure(state=tk.NORMAL)
    widget.insert(tk.END, msg + "\n")
    widget.see(tk.END)
    widget.configure(state=tk.DISABLED)
    widget.update_idletasks()


def read_table(path: str, sheet: str | None = None) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xlsm", ".xlsb", ".xls"]:
        return pd.read_excel(path, sheet_name=sheet) if sheet else pd.read_excel(path)
    elif ext in [".csv", ".tsv"]:
        sep = "," if ext == ".csv" else "\t"
        return pd.read_csv(path, sep=sep)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use CSV or Excel.")


def normalize_columns(df: pd.DataFrame, url_col: str, content_col: str) -> pd.DataFrame:
    # Allow some common variants
    cols = {c.lower(): c for c in df.columns}
    def pick(name: str) -> str:
        return cols.get(name.lower(), name)

    url_c = pick(url_col)
    content_c = pick(content_col)
    if url_c not in df.columns:
        raise KeyError(f"URL column '{url_col}' not found. Got: {list(df.columns)}")
    if content_c not in df.columns:
        # Try 'Content' as fallback
        if 'Content' in df.columns:
            content_c = 'Content'
        else:
            raise KeyError(f"Content column '{content_col}' not found. Got: {list(df.columns)}")

    out = df[[url_c, content_c]].copy()
    out.columns = ["Address", "content"]
    out["Address"] = out["Address"].astype(str).str.strip()
    out["content"] = out["content"].astype(str).fillna("").str.replace("\s+", " ", regex=True).str.strip()
    # drop rows with empty content or url
    out = out[(out["Address"] != "") & (out["content"] != "")]
    out = out.drop_duplicates(subset=["Address"])  # dedupe URLs
    out = out.reset_index(drop=True)
    return out


def build_tfidf(contents: List[str], analyzer_mode: str = "word"):
    """Build TF-IDF matrix.
    analyzer_mode: 'word' (default) or 'char' (for CJK-heavy corpora).
    """
    if analyzer_mode == "char":
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=2, max_features=80000)
    else:
        # Avoid English stopwords to keep multilingual content intact
        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, max_features=80000)
    X = vectorizer.fit_transform(contents)
    return vectorizer, X


def auto_analyzer_choice(contents: List[str]) -> str:
    # crude heuristic: if >30% of characters are CJK, prefer char-ngrams
    total = sum(len(c) for c in contents)
    if total == 0:
        return "word"
    cjk = 0
    for text in contents:
        for ch in text:
            # CJK Unified ranges
            if ("\u4e00" <= ch <= "\u9fff") or ("\u3400" <= ch <= "\u4dbf"):
                cjk += 1
    return "char" if (cjk / max(total, 1)) >= 0.30 else "word"


def top_similar_for_row(X, idx: int, threshold: float, top_n: int) -> List[Tuple[int, float]]:
    # Compute cosine similarities for row idx to all docs efficiently
    sims = cosine_similarity(X[idx], X).ravel()  # 1 x n -> array(n)
    sims[idx] = 0.0  # exclude self
    # Filter by threshold first
    candidates = [(i, float(s)) for i, s in enumerate(sims) if s >= threshold]
    # Sort by score desc and trim to top_n (if >0)
    candidates.sort(key=lambda t: t[1], reverse=True)
    if top_n > 0:
        candidates = candidates[:top_n]
    return candidates


def compute_internal_links(df: pd.DataFrame, threshold: float = 0.6, top_n: int = 10,
                           analyzer_mode: str | None = None) -> pd.DataFrame:
    contents = df["content"].astype(str).tolist()
    mode = analyzer_mode or auto_analyzer_choice(contents)
    vectorizer, X = build_tfidf(contents, analyzer_mode=mode)

    rows: List[dict] = []
    for idx, row in df.iterrows():
        cands = top_similar_for_row(X, idx, threshold=threshold, top_n=top_n)
        for j, score in cands:
            rows.append({
                "source_url": row["Address"],
                "candidate_url": df.iloc[j]["Address"],
                "similarity_score": round(score, 6)
            })
    return pd.DataFrame(rows)


# ------------------------
# GUI App
# ------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("780x560")
        self.resizable(True, True)

        # Vars
        self.file_path = tk.StringVar()
        self.sheet_name = tk.StringVar()
        self.url_col = tk.StringVar(value=DEFAULT_URL_COL)
        self.content_col = tk.StringVar(value=DEFAULT_CONTENT_COL)
        self.threshold = tk.DoubleVar(value=0.60)
        self.top_n = tk.IntVar(value=10)
        self.analyzer_mode = tk.StringVar(value="auto")  # auto/word/char

        # UI
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, **pad)

        ttk.Label(frm, text="Input file (CSV/XLSX):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.file_path, width=60).grid(row=0, column=1, sticky="we")
        ttk.Button(frm, text="Browse", command=self._pick_file).grid(row=0, column=2)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="Sheet name (Excel, optional):").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.sheet_name, width=20).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="URL column:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.url_col, width=20).grid(row=2, column=1, sticky="w")

        ttk.Label(frm, text="Content column:").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.content_col, width=20).grid(row=3, column=1, sticky="w")

        ttk.Label(frm, text="Similarity threshold (0-1):").grid(row=4, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.threshold, width=10).grid(row=4, column=1, sticky="w")

        ttk.Label(frm, text="Top N per page (0 = no cap):").grid(row=5, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.top_n, width=10).grid(row=5, column=1, sticky="w")

        ttk.Label(frm, text="Analyzer mode:").grid(row=6, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=self.analyzer_mode, values=["auto", "word", "char"], state="readonly", width=10).grid(row=6, column=1, sticky="w")

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, **pad)
        ttk.Button(btns, text="Run", command=self._run).pack(side=tk.LEFT)
        ttk.Button(btns, text="Save Results", command=self._save).pack(side=tk.LEFT, padx=6)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=tk.X, **pad)

        self.log_box = tk.Text(self, height=18, state=tk.DISABLED)
        self.log_box.pack(fill=tk.BOTH, expand=True, **pad)

        self.results_df: pd.DataFrame | None = None
        self.df_loaded: pd.DataFrame | None = None

    def _pick_file(self):
        path = filedialog.askopenfilename(filetypes=[
            ("Spreadsheets", "*.xlsx;*.xlsm;*.xlsb;*.xls;*.csv;*.tsv"),
            ("All Files", "*.*")
        ])
        if path:
            self.file_path.set(path)

    def _run(self):
        path = self.file_path.get().strip()
        if not path:
            messagebox.showwarning(APP_TITLE, "Please choose an input file.")
            return
        sheet = self.sheet_name.get().strip() or None
        url_col = self.url_col.get().strip() or DEFAULT_URL_COL
        content_col = self.content_col.get().strip() or DEFAULT_CONTENT_COL
        threshold = float(self.threshold.get())
        top_n = int(self.top_n.get())
        analyzer = self.analyzer_mode.get().strip()
        analyzer_mode = None if analyzer == "auto" else analyzer

        def task():
            try:
                self.progress.start(10)
                log(f"Reading table: {path}", self.log_box)
                df = read_table(path, sheet)
                log(f"Loaded {len(df):,} rows. Normalizing columns...", self.log_box)
                df = normalize_columns(df, url_col, content_col)
                log(f"Using columns: Address, content. Rows after cleanup: {len(df):,}", self.log_box)
                if len(df) == 0:
                    raise ValueError("No usable rows after cleanup.")

                log("Building TF-IDF (this may take a bit)...", self.log_box)
                results = compute_internal_links(df, threshold=threshold, top_n=top_n, analyzer_mode=analyzer_mode)
                self.results_df = results
                self.df_loaded = df
                log(f"Done. {len(results):,} link opportunities generated.", self.log_box)
                if len(results) == 0:
                    log("Tip: try lowering the threshold or increasing Top N.", self.log_box)
            except Exception as e:
                messagebox.showerror(APP_TITLE, f"Error: {e}")
                log(f"ERROR: {e}", self.log_box)
            finally:
                self.progress.stop()

        threading.Thread(target=task, daemon=True).start()

    def _save(self):
        if self.results_df is None or self.results_df.empty:
            messagebox.showinfo(APP_TITLE, "No results to save yet.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not out_path:
            return
        try:
            self.results_df.to_csv(out_path, index=False, encoding="utf-8-sig")
            messagebox.showinfo(APP_TITLE, f"Saved: {out_path}")
            log(f"Saved results to: {out_path}", self.log_box)
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Failed to save: {e}")
            log(f"Save error: {e}", self.log_box)


if __name__ == "__main__":
    app = App()
    app.mainloop()
