"""
Insightron GUI — single window, three modes: file, batch, live.

Wires the real batch and realtime services (not placeholders).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, List, Optional

import customtkinter as ctk

from insightron.core.config import APP_VERSION
from insightron.ui.components.audio_visualizer import AudioVisualizer
from insightron.ui.themes.design_tokens import get_layout_mode
from insightron.ui.themes.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

_BODY_SPLIT_PX = 980


class InsightronGUI:
    """Tabbed GUI: shared settings, mode tabs, activity panel (sidebar or stacked)."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.theme = ThemeManager.get_theme()
        self.root.title(f"Insightron · v{APP_VERSION}")
        self.root.geometry("900x740")
        self.root.minsize(480, 600)
        self.root.configure(fg_color=self.theme.background)
        
        # Start invisible for fade-in animation
        # Note: -alpha is supported on Windows/macOS
        try:
            self.root.attributes("-alpha", 0.0)
        except Exception:
            pass

        self.batch_files: List[str] = []
        self.is_batch_running = False
        self._live_running = False

        self._pipeline = None
        self._realtime = None
        self._last_live_model: Optional[str] = None

        self._layout_wide: Optional[bool] = None

        self._setup_theme()
        self._setup_ui()
        self._bind_resize()
        self._init_pipeline_async()

        logger.info("GUI initialized")
        self._animate_fade_in()

    def _animate_fade_in(self, alpha: float = 0.0):
        """Smooth fade-in animation for the main window."""
        try:
            if alpha < 1.0:
                alpha += 0.08
                self.root.attributes("-alpha", min(alpha, 1.0))
                self.root.after(16, lambda: self._animate_fade_in(alpha))
        except Exception:
            pass

    def _setup_theme(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

    def _bind_resize(self):
        self._last_configure_w = 0

        def on_configure(event=None):
            if event is not None and event.widget != self.root:
                return
            w = self.root.winfo_width()
            if w < 400 or w == self._last_configure_w:
                return
            self._last_configure_w = w
            ThemeManager.set_layout_mode(get_layout_mode(w))
            self._apply_body_layout(w)

        self.root.bind("<Configure>", on_configure)

    def _apply_body_layout(self, w: int):
        wide = w >= _BODY_SPLIT_PX
        if self._layout_wide == wide:
            return
        self._layout_wide = wide
        pad = ThemeManager.get_spacing("md")

        if wide:
            self._body.grid_rowconfigure(0, weight=1)
            self._body.grid_rowconfigure(1, weight=0)
            self._body.grid_columnconfigure(0, weight=2, minsize=360)
            self._body.grid_columnconfigure(1, weight=1, minsize=280)
            self.tabview.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=(0, pad), pady=0)
            self._activity_card.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=0, pady=0)
        else:
            self._body.grid_columnconfigure(0, weight=1)
            self._body.grid_columnconfigure(1, weight=0)
            self._body.grid_rowconfigure(0, weight=2)
            self._body.grid_rowconfigure(1, weight=1)
            self.tabview.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
            self._activity_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(pad, 0))

    def _init_pipeline_async(self):
        def init():
            self._ui(self._set_status, "Loading transcription engine…")
            from insightron.services.pipeline import get_pipeline

            self._pipeline = get_pipeline("medium", "auto")
            self._ui(self._set_status, "Ready")

        threading.Thread(target=init, daemon=True).start()

    def _ui(self, fn: Callable, *args, **kwargs):
        self.root.after(0, lambda: fn(*args, **kwargs))

    def _set_status(self, text: str):
        self.status.configure(text=text)

    def _section_label(self, master, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master,
            text=text,
            font=ctk.CTkFont(size=ThemeManager.get_font_size("caption"), weight="bold"),
            text_color=self.theme.text_secondary,
        )

    def _style_entry(self, entry: ctk.CTkEntry):
        entry.configure(
            height=40,
            corner_radius=ThemeManager.get_radius("md"),
            border_width=1,
            border_color=self.theme.border,
            fg_color=self.theme.surface,
        )

    def _style_option(self, menu: ctk.CTkOptionMenu, accent: str = "primary"):
        hover = self.theme.primary_hover if accent == "primary" else self.theme.secondary_hover
        btn = self.theme.primary if accent == "primary" else self.theme.secondary
        menu.configure(
            height=36,
            corner_radius=ThemeManager.get_radius("md"),
            fg_color=self.theme.surface,
            button_color=btn,
            button_hover_color=hover,
            dropdown_fg_color=self.theme.surface_light,
            dropdown_hover_color=self.theme.surface,
            dropdown_text_color=self.theme.text_primary,
        )

    def _accent_button(self, master, text, command, **kw):
        h = ThemeManager.get_button_height("md")
        fg = kw.pop("fg_color", self.theme.primary)
        hover = kw.pop("hover_color", self.theme.primary_hover)
        return ctk.CTkButton(
            master,
            text=text,
            command=command,
            height=h,
            corner_radius=ThemeManager.get_radius("md"),
            fg_color=fg,
            hover_color=hover,
            text_color=self.theme.text_primary,
            font=ctk.CTkFont(size=ThemeManager.get_font_size("h3"), weight="bold"),
            **kw,
        )

    def _ghost_button(self, master, text, command):
        h = ThemeManager.get_button_height("sm")
        return ctk.CTkButton(
            master,
            text=text,
            command=command,
            height=h,
            fg_color=self.theme.surface_light,
            hover_color=self.theme.surface,
            text_color=self.theme.text_secondary,
            border_width=1,
            border_color=self.theme.border,
            corner_radius=ThemeManager.get_radius("sm"),
        )

    def _clear_log(self):
        self.results.delete("1.0", "end")

    def _setup_ui(self):
        pad = ThemeManager.get_spacing("md")
        lg = ThemeManager.get_spacing("lg")
        r = ThemeManager.get_radius("md")

        self.main = ctk.CTkFrame(
            self.root,
            fg_color=self.theme.surface,
            corner_radius=ThemeManager.get_radius("lg"),
            border_width=0,
        )
        self.main.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        header_block = ctk.CTkFrame(self.main, fg_color="transparent")
        header_block.grid(row=0, column=0, sticky="ew", padx=lg, pady=(lg, sm := ThemeManager.get_spacing("sm")))

        accent_bar = ctk.CTkFrame(header_block, fg_color=self.theme.primary, corner_radius=ThemeManager.get_radius("sm"), height=4)
        accent_bar.pack(fill="x", pady=(0, sm))

        title_row = ctk.CTkFrame(header_block, fg_color="transparent")
        title_row.pack(fill="x")
        ctk.CTkLabel(
            title_row,
            text="Insightron",
            font=ctk.CTkFont(size=ThemeManager.get_font_size("hero"), weight="bold"),
            text_color=self.theme.text_primary,
        ).pack(side="left")
        ctk.CTkLabel(
            title_row,
            text=f"  v{APP_VERSION}",
            font=ctk.CTkFont(size=ThemeManager.get_font_size("caption")),
            text_color=self.theme.text_secondary,
        ).pack(side="left", pady=(8, 0))

        ctk.CTkLabel(
            header_block,
            text="Single file, batch queue, or live microphone — same engine, your machine.",
            font=ctk.CTkFont(size=ThemeManager.get_font_size("body_small")),
            text_color=self.theme.text_secondary,
            wraplength=720,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        settings = ctk.CTkFrame(
            self.main,
            fg_color=self.theme.surface_light,
            corner_radius=r,
            border_width=0,
        )
        settings.grid(row=1, column=0, sticky="ew", padx=lg, pady=(0, pad))
        settings.grid_columnconfigure(7, weight=1)

        self._section_label(settings, "Engine").grid(row=0, column=0, padx=(pad, 4), pady=pad, sticky="w")
        self.model_var = ctk.StringVar(value="medium")
        self.model_menu = ctk.CTkOptionMenu(
            settings,
            values=["tiny", "base", "small", "medium", "large"],
            variable=self.model_var,
        )
        self.model_menu.grid(row=0, column=1, padx=4, pady=pad, sticky="w")
        self._style_option(self.model_menu, "primary")

        self._section_label(settings, "Language").grid(row=0, column=2, padx=(lg, 4), pady=pad, sticky="w")
        self.lang_var = ctk.StringVar(value="auto")
        self.lang_menu = ctk.CTkOptionMenu(
            settings,
            values=["auto", "en", "es", "fr", "de", "it", "pt", "ja", "zh"],
            variable=self.lang_var,
        )
        self.lang_menu.grid(row=0, column=3, padx=4, pady=pad, sticky="w")
        self._style_option(self.lang_menu, "secondary")

        self._body = ctk.CTkFrame(self.main, fg_color="transparent")
        self._body.grid(row=2, column=0, sticky="nsew", padx=lg, pady=(0, lg))

        self.tabview = ctk.CTkTabview(
            self._body,
            fg_color=self.theme.surface,
            segmented_button_fg_color=self.theme.surface_light,
            segmented_button_selected_color=self.theme.primary,
            segmented_button_selected_hover_color=self.theme.primary_hover,
            segmented_button_unselected_color=self.theme.surface,
            segmented_button_unselected_hover_color=self.theme.surface_light,
            text_color=self.theme.text_primary,
            corner_radius=r,
            border_width=0,
        )

        self._activity_card = ctk.CTkFrame(
            self._body,
            fg_color=self.theme.surface_light,
            corner_radius=r,
            border_width=0,
        )
        self._activity_card.grid_rowconfigure(3, weight=1)
        self._activity_card.grid_columnconfigure(0, weight=1)

        act_pad = ThemeManager.get_spacing("sm")
        act_top = ctk.CTkFrame(self._activity_card, fg_color="transparent")
        act_top.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, act_pad))
        act_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            act_top,
            text="Activity",
            font=ctk.CTkFont(size=ThemeManager.get_font_size("h2"), weight="bold"),
            text_color=self.theme.text_primary,
        ).grid(row=0, column=0, sticky="w")
        self._ghost_button(act_top, "Clear log", self._clear_log).grid(row=0, column=1, sticky="e")

        self.progress = ctk.CTkProgressBar(
            self._activity_card,
            progress_color=self.theme.accent,
            fg_color=self.theme.surface,
            height=10,
            corner_radius=ThemeManager.get_radius("sm"),
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=pad, pady=(0, act_pad))
        self.progress.set(0)

        self.status = ctk.CTkLabel(
            self._activity_card,
            text="Ready",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=ThemeManager.get_font_size("body_small")),
        )
        self.status.grid(row=2, column=0, sticky="w", padx=pad, pady=(0, act_pad))

        self.results = ctk.CTkTextbox(
            self._activity_card,
            font=ctk.CTkFont(family="Consolas", size=ThemeManager.get_font_size("mono")),
            fg_color=self.theme.surface,
            text_color=self.theme.text_primary,
            border_width=0,
            corner_radius=r,
        )
        self.results.grid(row=3, column=0, sticky="nsew", padx=pad, pady=(0, pad))

        self._build_tab_files()
        self._build_tab_live()

        w0 = self.root.winfo_width()
        self._apply_body_layout(w0 if w0 >= 400 else _BODY_SPLIT_PX + 120)
        self.root.after(120, lambda: self._apply_body_layout(self.root.winfo_width()))

    def _build_tab_files(self):
        tab = self.tabview.add("Audio Files")
        inner = ctk.CTkFrame(tab, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=ThemeManager.get_spacing("md"), pady=ThemeManager.get_spacing("md"))

        ctk.CTkLabel(
            inner,
            text="Add audio files. Each completed job writes to your configured transcription folder.",
            text_color=self.theme.text_secondary,
            font=ctk.CTkFont(size=ThemeManager.get_font_size("body_small")),
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        self._section_label(inner, "Queue").pack(anchor="w", pady=(0, 6))
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 8))
        self._ghost_button(btns, "Add files…", self._batch_add_files).pack(side="left", padx=(0, 8))
        self._ghost_button(btns, "Clear queue", self._batch_clear).pack(side="left")

        self.batch_list = ctk.CTkTextbox(
            inner,
            height=160,
            font=ctk.CTkFont(size=ThemeManager.get_font_size("body_small")),
            fg_color=self.theme.surface,
            text_color=self.theme.text_primary,
            border_width=0,
            corner_radius=ThemeManager.get_radius("md"),
        )
        self.batch_list.pack(fill="both", expand=True, pady=(0, 12))
        self.batch_list.configure(state="disabled")

        self._section_label(inner, "Run").pack(anchor="w", pady=(0, 6))
        self.batch_btn = self._accent_button(inner, "Transcribe Files", self._start_batch)
        self.batch_btn.pack(fill="x")

    def _build_tab_live(self):
        tab = self.tabview.add("Live mic")
        inner = ctk.CTkFrame(tab, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=ThemeManager.get_spacing("md"), pady=ThemeManager.get_spacing("md"))

        self._section_label(inner, "Input level").pack(anchor="w", pady=(0, 6))
        self.visualizer = AudioVisualizer(inner, num_bars=40, height=112)
        self.visualizer.pack(fill="x", pady=(0, 12))

        self._section_label(inner, "Microphone").pack(anchor="w", pady=(0, 6))
        mic_row = ctk.CTkFrame(inner, fg_color="transparent")
        mic_row.pack(fill="x", pady=(0, 12))
        self.mic_var = ctk.StringVar(value="Loading…")
        self.mic_menu = ctk.CTkOptionMenu(mic_row, values=["Default"], variable=self.mic_var)
        self.mic_menu.pack(side="left", fill="x", expand=True)
        self._style_option(self.mic_menu, "primary")
        self.mic_menu.configure(fg_color=self.theme.surface_light)

        self._section_label(inner, "Live transcript").pack(anchor="w", pady=(0, 6))
        self.live_transcript = ctk.CTkTextbox(
            inner,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=ThemeManager.get_font_size("body_small")),
            fg_color=self.theme.surface,
            text_color=self.theme.text_primary,
            border_width=0,
            corner_radius=ThemeManager.get_radius("md"),
        )
        self.live_transcript.pack(fill="both", expand=True, pady=(0, 12))

        self._section_label(inner, "Session").pack(anchor="w", pady=(0, 6))
        live_btns = ctk.CTkFrame(inner, fg_color="transparent")
        live_btns.pack(fill="x")
        self.live_start_btn = self._accent_button(
            live_btns, "Start listening", self._live_start, fg_color=self.theme.accent, hover_color=self.theme.accent_hover
        )
        self.live_start_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.live_stop_btn = ctk.CTkButton(
            live_btns,
            text="Stop",
            command=self._live_stop,
            height=ThemeManager.get_button_height("md"),
            corner_radius=ThemeManager.get_radius("md"),
            fg_color=self.theme.surface,
            hover_color=self.theme.surface_light,
            text_color=self.theme.error,
            border_width=2,
            border_color=self.theme.error,
            state="disabled",
        )
        self.live_stop_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.root.after(200, self._refresh_mics)

    def _batch_add_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.flac *.mp4 *.ogg *.aac"), ("All", "*.*")]
        )
        if not paths:
            return
        for p in paths:
            rp = str(Path(p).resolve())
            if rp not in self.batch_files:
                self.batch_files.append(rp)
        self._batch_list_refresh()

    def _batch_clear(self):
        self.batch_files.clear()
        self._batch_list_refresh()

    def _batch_list_refresh(self):
        self.batch_list.configure(state="normal")
        self.batch_list.delete("1.0", "end")
        for f in self.batch_files:
            self.batch_list.insert("end", f + "\n")
        self.batch_list.configure(state="disabled")

    def _refresh_mics(self):
        def load():
            try:
                import sounddevice as sd

                devices = []
                for i, dev in enumerate(sd.query_devices()):
                    if dev.get("max_input_channels", 0) > 0:
                        devices.append(
                            {"index": i, "name": dev.get("name", "Input"), "host_api": dev.get("hostapi")}
                        )
            except Exception as e:
                logger.exception("Mic list failed")
                self._ui(self._apply_mic_list, [], str(e))
                return
            self._ui(self._apply_mic_list, devices, None)

        threading.Thread(target=load, daemon=True).start()

    def _apply_mic_list(self, devices, err: Optional[str]):
        labels: List[str] = []
        self._mic_index_by_label = {}
        if err:
            labels = ["(unavailable)"]
            self._mic_index_by_label["(unavailable)"] = -1
            self.mic_menu.configure(values=labels)
            self.mic_var.set(labels[0])
            self._log_line(f"[mic] {err}")
            return
        for d in devices:
            name = f"{d.get('index', -1)} — {d.get('name', 'Device')}"
            labels.append(name)
            self._mic_index_by_label[name] = int(d.get("index", -1))
        if not labels:
            labels = ["Default"]
            self._mic_index_by_label["Default"] = -1
        self.mic_menu.configure(values=labels)
        self.mic_var.set(labels[0])

    def _log_line(self, text: str):
        self.results.insert("end", text + "\n")
        self.results.see("end")

    def _ensure_pipeline(self):
        from insightron.services.pipeline import get_pipeline

        m = self.model_var.get()
        lang = self.lang_var.get()
        self._pipeline = get_pipeline(m, lang)

    def _start_batch(self):
        if not self.batch_files:
            messagebox.showerror("Insightron", "Add at least one file to the batch list.")
            return
        if self.is_batch_running:
            return
        self.is_batch_running = True
        self.batch_btn.configure(state="disabled")
        self.progress.set(0)
        self._log_line(f"[batch] Starting {len(self.batch_files)} file(s)…")

        files = list(self.batch_files)
        model = self.model_var.get()
        lang = self.lang_var.get()

        def run():
            try:
                from insightron.services.batch.batch_processor import BatchTranscriber

                def prog(done: int, total: int, name: str):
                    frac = done / max(total, 1)
                    self._ui(self.progress.set, frac)
                    self._ui(self._set_status, f"Batch {done}/{total}: {name}")
                    self._ui(self._log_line, f"[batch] {done}/{total} — {name}")

                bt = BatchTranscriber(model_size=model, language=lang)
                summary = bt.transcribe_batch(files, progress_callback=prog)
                self._ui(self.progress.set, 1.0)
                ok = len(summary.get("successful", []))
                bad = len(summary.get("failed", []))
                self._ui(self._set_status, f"Batch done — {ok} ok, {bad} failed")
                sp = summary.get("summary_path")
                if sp:
                    self._ui(self._log_line, f"[batch] Summary: {sp}")
                for f in summary.get("failed", []):
                    self._ui(
                        self._log_line,
                        f"[batch] FAIL {f.get('file')}: {f.get('error')}",
                    )
            except Exception as e:
                logger.exception("Batch failed")
                self._ui(lambda: messagebox.showerror("Insightron", str(e)))
            finally:
                self.is_batch_running = False
                self._ui(self.batch_btn.configure, state="normal")

        threading.Thread(target=run, daemon=True).start()

    def _live_start(self):
        if self._live_running:
            return
        label = self.mic_var.get()
        device_index = getattr(self, "_mic_index_by_label", {}).get(label, -1)
        if label == "(unavailable)":
            messagebox.showerror("Insightron", "No microphone available.")
            return

        model = self.model_var.get()
        lang = self.lang_var.get()

        self.live_transcript.delete("1.0", "end")
        self._log_line("[live] Starting… (first inference may take a moment)")

        def run():
            try:
                from insightron.services.realtime import RealtimeTranscriber

                self._ui(self._set_status, "Loading live model…")
                if self._realtime is not None and self._last_live_model != model:
                    try:
                        self._realtime.stop_transcription()
                    except Exception:
                        pass
                    self._realtime = None

                if self._realtime is None:
                    self._realtime = RealtimeTranscriber(
                        model_size=model, language=lang if lang != "auto" else "auto"
                    )
                    self._last_live_model = model

                def on_text(chunk: str):
                    def append():
                        self.live_transcript.insert("end", chunk + " ")
                        self.live_transcript.see("end")

                    self._ui(append)

                def on_level(level: float):
                    self._ui(self.visualizer.set_level, level)

                self._realtime.start_transcription(device_index, on_text, on_level)
                self._live_running = True
                self._ui(self._set_status, "Listening…")
                self._ui(self.live_start_btn.configure, state="disabled")
                self._ui(self.live_stop_btn.configure, state="normal")
            except Exception as e:
                logger.exception("Live start failed")
                self._live_running = False
                self._ui(lambda: messagebox.showerror("Insightron", str(e)))
                self._ui(self.live_start_btn.configure, state="normal")
                self._ui(self.live_stop_btn.configure, state="disabled")

        threading.Thread(target=run, daemon=True).start()

    def _live_stop(self):
        if not self._live_running and self._realtime is None:
            return

        def run():
            try:
                if self._realtime:
                    self._realtime.stop_transcription()
            finally:
                self._live_running = False
                self._ui(self.visualizer.reset)
                self._ui(self._set_status, "Ready")
                self._ui(self.live_start_btn.configure, state="normal")
                self._ui(self.live_stop_btn.configure, state="disabled")
                self._log_line("[live] Stopped.")

        threading.Thread(target=run, daemon=True).start()
