"""Graphical user interface for Video Subtitle Generator."""

import logging
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Optional

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError(
        "customtkinter is not installed. Please install it with: pip install customtkinter"
    )

from .config import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    SubtitleFormat,
)
from .processor import VideoProcessor
from .config_manager import ConfigManager
from .i18n import (
    _,
    get_i18n_manager,
    init_i18n,
    Language,
    LANGUAGE_NAMES,
)

class GUILogHandler(logging.Handler):
    """Custom logging handler that sends logs to GUI."""
    
    def __init__(self, gui_instance):
        super().__init__(level=logging.INFO)
        self.gui = gui_instance
    
    def emit(self, record):
        """Emit a log record."""
        msg = self.format(record)
        if hasattr(self.gui, '_log_message'):
            self.gui.after(0, lambda: self.gui._log_message(msg))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class VideoSubtitleGUI(ctk.CTk):
    """Main GUI window for Video Subtitle Generator."""

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.config_manager = ConfigManager()
        self.video_files: list[str] = []
        self.processor: Optional[VideoProcessor] = None
        self.is_processing = False
        
        self._start_time: Optional[float] = None
        self._step_times: dict[str, tuple[float, float]] = {}
        self._current_step: Optional[str] = None

        self._initialize_i18n()
        self._load_last_config()
        self._setup_ui()

    def _initialize_i18n(self) -> None:
        """Initialize internationalization system."""
        init_i18n()
        self.i18n_manager = get_i18n_manager()
        self.i18n_manager.register_callback(self._on_language_changed)

    def _load_last_config(self) -> None:
        """Load last used configuration."""
        if self.config_manager.config_exists():
            try:
                self.config = self.config_manager.load_config()
                if self.config.language:
                    try:
                        lang = Language(self.config.language)
                        self.i18n_manager.set_language(lang)
                    except ValueError:
                        pass
                logger.info(_("loaded_last_config"))
            except Exception as e:
                logger.warning(_("failed_load_config", error=e))

    def _setup_ui(self) -> None:
        """Setup the entire user interface."""
        self._apply_translate_window()
        self._setup_colors()
        self._create_ui()
        
        gui_handler = GUILogHandler(self)
        logging.getLogger().addHandler(gui_handler)

    def _apply_translate_window(self) -> None:
        """Apply translation to window properties."""
        self.title(_("app_title"))
        self.geometry("1300x850")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _setup_colors(self) -> None:
        """Setup color scheme."""
        self.COLORS = {
            "primary": "#5B8DEE",
            "primary_hover": "#4A7BD6",
            "success": "#65C3C8",
            "success_hover": "#4FB3BA",
            "warning": "#F0B429",
            "warning_hover": "#D99D1A",
            "danger": "#E7766E",
            "danger_hover": "#D66159",
            "neutral": "#8B95A1",
            "neutral_hover": "#718096",
            "bg_dark": "#121826",
            "bg_medium": "#1E293B",
            "bg_light": "#334155",
            "border": "#475569",
            "text": "#E5E7EB",
            "text_dim": "#9CA3AF",
        }

    def _create_ui(self) -> None:
        """Create the user interface."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color=self.COLORS["bg_dark"], corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        self._create_top_bar(main_frame)
        self._create_file_panel(main_frame, 1, 0)
        self._create_control_panel(main_frame, 1, 1)
        self._create_config_panel(main_frame, 2, 0)
        self._create_output_panel(main_frame, 2, 1)

    def _create_top_bar(self, parent: ctk.CTkFrame) -> None:
        """Create top bar with language selector."""
        top_bar = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=0)
        top_bar.grid_columnconfigure(0, weight=1)

        lang_label = ctk.CTkLabel(
            top_bar,
            text=_("language_selection"),
            text_color=self.COLORS["text_dim"],
        )
        lang_label.grid(row=0, column=0, sticky="e", padx=12, pady=8)

        self.language_var = ctk.StringVar(value=LANGUAGE_NAMES[self.i18n_manager.get_language()])
        lang_combo = ctk.CTkComboBox(
            top_bar,
            variable=self.language_var,
            values=list(LANGUAGE_NAMES.values()),
            width=180,
            corner_radius=8,
            command=self._on_language_selected,
        )
        lang_combo.grid(row=0, column=1, sticky="e", padx=12, pady=8)

    def _on_language_selected(self, _) -> None:
        """Handle language selection change."""
        selected_name = self.language_var.get()
        for lang, name in LANGUAGE_NAMES.items():
            if name == selected_name:
                self.i18n_manager.set_language(lang)
                self.config.language = lang.value
                self.config_manager.save_config(self.config)
                break

    def _on_language_changed(self) -> None:
        """Update all UI elements when language changes."""
        self.title(_("app_title"))
        self.language_var.set(LANGUAGE_NAMES[self.i18n_manager.get_language()])
        self._recreate_ui()

    def _recreate_ui(self) -> None:
        """Recreate the entire UI with new language."""
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()

    def _create_file_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create file list panel."""
        file_frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_medium"], corner_radius=12)
        file_frame.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            file_frame, 
            text=_("file_panel_title"), 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.file_listbox = tk.Listbox(
            file_frame,
            selectmode=tk.EXTENDED,
            font=("Segoe UI", 11),
            bg=self.COLORS["bg_light"],
            fg=self.COLORS["text"],
            selectbackground=self.COLORS["primary"],
            selectforeground="#FFFFFF",
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        self.file_listbox.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=8
        )

        scrollbar = ttk.Scrollbar(
            file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview
        )
        scrollbar.grid(row=1, column=1, sticky="ns", pady=8)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 12))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        add_btn = ctk.CTkButton(
            btn_frame, 
            text=_("add_files"), 
            command=self._add_files, 
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            fg_color=self.COLORS["primary"],
            hover_color=self.COLORS["primary_hover"],
            border_spacing=0
        )
        add_btn.grid(row=0, column=0, padx=4)

        remove_btn = ctk.CTkButton(
            btn_frame, 
            text=_("remove_selected"), 
            command=self._remove_selected, 
            height=36,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            fg_color=self.COLORS["neutral"],
            hover_color=self.COLORS["neutral_hover"],
            border_color=self.COLORS["border"],
            border_width=1
        )
        remove_btn.grid(row=0, column=1, padx=4)

        clear_btn = ctk.CTkButton(
            btn_frame, 
            text=_("clear_list"), 
            command=self._clear_files, 
            height=36,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.COLORS["bg_light"],
            border_color=self.COLORS["danger"],
            border_width=1,
            text_color=self.COLORS["danger"]
        )
        clear_btn.grid(row=0, column=2, padx=4)

    def _create_config_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create configuration panel."""
        config_frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_medium"], corner_radius=12)
        config_frame.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        config_frame.grid_rowconfigure(0, weight=1)
        config_frame.grid_columnconfigure(0, weight=1)

        scrollable_frame = ctk.CTkScrollableFrame(
            config_frame, 
            fg_color="transparent",
            corner_radius=0
        )
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        title_label = ctk.CTkLabel(
            scrollable_frame,
            text=_("config_panel_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 15))

        row_idx = 1
        row_idx = self._create_basic_config_section(scrollable_frame, row_idx)
        row_idx = self._create_advanced_config_section(scrollable_frame, row_idx)

    def _create_basic_config_section(
        self, parent, start_row: int
    ) -> int:
        """Create basic configuration section."""
        basic_label = ctk.CTkLabel(
            parent, 
            text=_("basic_config"), 
            font=ctk.CTkFont(weight="bold", size=15),
            text_color=self.COLORS["primary"]
        )
        basic_label.grid(row=start_row, column=0, sticky="w", pady=(10, 8), columnspan=3)
        start_row += 1

        model_label = ctk.CTkLabel(parent, text=_("model"), text_color=self.COLORS["text_dim"])
        model_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.model_var = ctk.StringVar(value=self.config.model_config.model_name)
        model_combo = ctk.CTkComboBox(
            parent,
            variable=self.model_var,
            values=[
                "large-v3-turbo",
                "large-v3",
                "medium",
                "small",
                "base",
                "tiny",
            ],
            width=320,
            corner_radius=8,
        )
        model_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        lang_label = ctk.CTkLabel(parent, text=_("language"), text_color=self.COLORS["text_dim"])
        lang_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.lang_var = ctk.StringVar(value=self.config.model_config.language)
        lang_combo = ctk.CTkComboBox(
            parent,
            variable=self.lang_var,
            values=[
                "auto",
                "zh",
                "en",
                "ja",
                "es",
                "fr",
                "ru",
                "de",
                "it",
                "pt",
            ],
            width=320,
            corner_radius=8,
        )
        lang_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        format_label = ctk.CTkLabel(parent, text=_("subtitle_format"), text_color=self.COLORS["text_dim"])
        format_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.format_var = ctk.StringVar(value=self.config.subtitle_format.value)
        format_combo = ctk.CTkComboBox(
            parent,
            variable=self.format_var,
            values=["srt", "ass"],
            width=320,
            corner_radius=8,
        )
        format_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        output_label = ctk.CTkLabel(parent, text=_("output_dir"), text_color=self.COLORS["text_dim"])
        output_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.output_var = ctk.StringVar(value=self.config.output_dir or "")
        output_entry = ctk.CTkEntry(
            parent, 
            textvariable=self.output_var, 
            width=230,
            corner_radius=8
        )
        output_entry.grid(row=start_row, column=1, padx=12, pady=6)
        output_btn = ctk.CTkButton(
            parent, 
            text=_("browse"), 
            command=self._browse_output, 
            width=80,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self.COLORS["bg_light"],
            border_color=self.COLORS["border"],
            border_width=1
        )
        output_btn.grid(row=start_row, column=2, padx=0, pady=6)
        start_row += 1

        return start_row

    def _create_advanced_config_section(
        self, parent, start_row: int
    ) -> int:
        """Create advanced configuration section."""
        advanced_label = ctk.CTkLabel(
            parent, 
            text=_("advanced_config"), 
            font=ctk.CTkFont(weight="bold", size=15),
            text_color=self.COLORS["primary"]
        )
        advanced_label.grid(row=start_row, column=0, sticky="w", pady=(15, 8), columnspan=3)
        start_row += 1

        quality_label = ctk.CTkLabel(parent, text=_("quality_mode"), text_color=self.COLORS["text_dim"])
        quality_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.quality_var = ctk.StringVar(value=self.config.quality_mode.value)
        quality_combo = ctk.CTkComboBox(
            parent,
            variable=self.quality_var,
            values=["pro", "quality", "balanced", "speed"],
            width=320,
            corner_radius=8,
        )
        quality_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        enhance_label = ctk.CTkLabel(parent, text=_("audio_enhance"), text_color=self.COLORS["text_dim"])
        enhance_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.enhance_var = ctk.StringVar(
            value=self.config.audio_enhance_profile.value
        )
        enhance_combo = ctk.CTkComboBox(
            parent,
            variable=self.enhance_var,
            values=["off", "voice", "strong"],
            width=320,
            corner_radius=8,
        )
        enhance_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        vad_label = ctk.CTkLabel(parent, text=_("vad_config"), text_color=self.COLORS["text_dim"])
        vad_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.vad_var = ctk.StringVar(value=self.config.vad_profile.value)
        vad_combo = ctk.CTkComboBox(
            parent,
            variable=self.vad_var,
            values=["voice_focus", "balanced", "noise_robust", "fast", "sensitive", "ultra_sensitive"],
            width=320,
            corner_radius=8,
        )
        vad_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        self.vad_enabled_var = ctk.BooleanVar(value=self.config.use_vad)
        vad_check = ctk.CTkCheckBox(
            parent, 
            text=_("enable_vad"), 
            variable=self.vad_enabled_var,
            text_color=self.COLORS["text"],
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6
        )
        vad_check.grid(row=start_row, column=0, columnspan=3, sticky="w", padx=0, pady=8)
        start_row += 1

        device_label = ctk.CTkLabel(parent, text=_("device_selection"), text_color=self.COLORS["text_dim"])
        device_label.grid(row=start_row, column=0, sticky="w", pady=6)
        self.device_var = ctk.StringVar(value=self.config.model_config.device)
        device_combo = ctk.CTkComboBox(
            parent,
            variable=self.device_var,
            values=["auto", "cuda", "cpu"],
            width=320,
            corner_radius=8,
        )
        device_combo.grid(row=start_row, column=1, padx=12, pady=6, columnspan=2)
        start_row += 1

        self.overwrite_var = ctk.BooleanVar(value=self.config.overwrite)
        overwrite_check = ctk.CTkCheckBox(
            parent, 
            text=_("overwrite_existing"), 
            variable=self.overwrite_var,
            text_color=self.COLORS["text"],
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6
        )
        overwrite_check.grid(
            row=start_row, column=0, columnspan=3, sticky="w", padx=0, pady=8
        )
        start_row += 1

        voice_priority_btn = ctk.CTkButton(
            parent,
            text=_("voice_priority_template"),
            command=self._apply_voice_priority,
            width=200,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLORS["success"],
            hover_color=self.COLORS["success_hover"],
            border_spacing=0
        )
        voice_priority_btn.grid(
            row=start_row, column=0, columnspan=3, padx=0, pady=(12, 5)
        )
        start_row += 1

        return start_row

    def _create_control_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create control panel."""
        control_frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_medium"], corner_radius=12)
        control_frame.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_rowconfigure(2, weight=1)

        title_label = ctk.CTkLabel(
            control_frame,
            text=_("control_panel_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 10))

        self.start_btn = ctk.CTkButton(
            control_frame,
            text=_("start_processing"),
            command=self._start_processing,
            height=52,
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=10,
            fg_color=self.COLORS["success"],
            hover_color=self.COLORS["success_hover"],
            border_spacing=0
        )
        self.start_btn.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="ew")

        self.stop_btn = ctk.CTkButton(
            control_frame,
            text=_("stop"),
            command=self._stop_processing,
            height=52,
            font=ctk.CTkFont(size=18, weight="bold"),
            state="disabled",
            corner_radius=10,
            fg_color=self.COLORS["danger"],
            hover_color=self.COLORS["danger_hover"],
            border_spacing=0
        )
        self.stop_btn.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="ew")

        progress_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        progress_container.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_container, height=10)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container, 
            text=_("ready"), 
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["text_dim"]
        )
        self.progress_label.grid(row=1, column=0, sticky="w")
        
        self.total_time_label = ctk.CTkLabel(
            progress_container, 
            text=_("total_time", time="0.0"), 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLORS["primary"]
        )
        self.total_time_label.grid(row=1, column=0, sticky="e")

    def _create_output_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create output panel."""
        output_frame = ctk.CTkFrame(parent, fg_color=self.COLORS["bg_medium"], corner_radius=12)
        output_frame.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_rowconfigure(3, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            output_frame, 
            text=_("output_panel_title"), 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.process_log_text = ctk.CTkTextbox(
            output_frame, 
            state="normal", 
            height=200,
            corner_radius=8,
            fg_color=self.COLORS["bg_light"],
            border_color=self.COLORS["border"],
            border_width=1
        )
        self.process_log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
        
        steps_title = ctk.CTkLabel(
            output_frame, 
            text=_("steps_timing"), 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.COLORS["text"]
        )
        steps_title.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 8))
        
        self.steps_text = ctk.CTkTextbox(
            output_frame, 
            state="normal", 
            height=120,
            corner_radius=8,
            fg_color=self.COLORS["bg_light"],
            border_color=self.COLORS["border"],
            border_width=1
        )
        self.steps_text.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 12))

    def _add_files(self) -> None:
        """Add video files to the list."""
        filetypes = [
            (_("video_files"), "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm"),
            (_("all_files"), "*.*"),
        ]
        files = filedialog.askopenfilenames(
            title=_("select_video_files"),
            filetypes=filetypes,
        )

        for file in files:
            if file not in self.video_files:
                self.video_files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)

    def _remove_selected(self) -> None:
        """Remove selected files from the list."""
        selected = list(self.file_listbox.curselection())
        for index in reversed(selected):
            self.video_files.pop(index)
            self.file_listbox.delete(index)

    def _clear_files(self) -> None:
        """Clear all files from the list."""
        self.video_files.clear()
        self.file_listbox.delete(0, tk.END)

    def _browse_output(self) -> None:
        """Browse for output directory."""
        directory = filedialog.askdirectory(title=_("select_output_dir"))
        if directory:
            self.output_var.set(directory)

    def _apply_voice_priority(self) -> None:
        """Apply voice priority template."""
        self.quality_var.set("pro")
        self.enhance_var.set("voice")
        self.vad_var.set("sensitive")
        self.vad_enabled_var.set(False)
        self._log_message(_("applied_voice_priority"))

    def _create_config_from_ui(self) -> Config:
        """Create Config object from UI values."""
        config = Config()
        config.model_config.model_name = self.model_var.get()
        config.model_config.language = self.lang_var.get()
        config.model_config.device = self.device_var.get()
        config.subtitle_format = SubtitleFormat(self.format_var.get())
        config.output_dir = self.output_var.get() or None
        config.quality_mode = QualityMode(self.quality_var.get())
        config.audio_enhance_profile = AudioEnhanceProfile(self.enhance_var.get())
        config.vad_profile = VADProfile(self.vad_var.get())
        config.use_vad = self.vad_enabled_var.get()
        config.overwrite = self.overwrite_var.get()
        config.language = self.config.language

        Config.apply_quality_mode(config, config.quality_mode)
        Config.apply_vad_profile(config, config.vad_profile)
        Config.apply_audio_enhance_profile(config, config.audio_enhance_profile)

        return config

    def _start_processing(self) -> None:
        """Start processing video files."""
        if not self.video_files:
            messagebox.showwarning(_("warning"), _("please_add_files"))
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        self._reset_timing()
        self._start_time = time.time()

        config = self._create_config_from_ui()
        self.processor = VideoProcessor(config)

        def progress_callback(stage: str, progress: float):
            self.after(
                0,
                lambda: self.progress_bar.set(progress / 100),
            )
            self.after(
                0,
                lambda: self.progress_label.configure(text=f"{progress:5.1f}% - {stage}"),
            )
            self.after(0, lambda: self._record_step(stage, progress))

        self.processor.set_progress_callback(progress_callback)

        def process_thread():
            try:
                if len(self.video_files) == 1:
                    subtitle = self.processor.process_video(self.video_files[0])
                    output_path = self.processor.save_subtitle(
                        subtitle,
                        self.output_var.get() or str(
                            Path(self.video_files[0]).parent
                        ),
                        video_path=self.video_files[0],
                    )
                    self.after(
                        0,
                        lambda: self._log_message(_("subtitle_saved", path=output_path)),
                    )
                else:
                    output_dir = self.output_var.get() or str(
                        Path(self.video_files[0]).parent
                    )
                    results = self.processor.process_batch(
                        self.video_files, output_dir=output_dir
                    )
                    self.after(
                        0,
                        lambda: self._log_message(
                            _("batch_complete", count=len(results))
                        ),
                    )
                    for video_path, subtitle_path in results:
                        self.after(
                            0,
                            lambda vp=video_path, sp=subtitle_path: self._log_message(
                                f"{Path(vp).name} -> {Path(sp).name}"
                            ),
                        )

                self.after(0, self._processing_complete)
            except Exception as e:
                self.after(
                    0, lambda: self._log_message(f"错误：{str(e)}")
                )
                self.after(0, self._processing_complete)

        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()

    def _stop_processing(self) -> None:
        """Stop processing."""
        self.is_processing = False
        self._log_message(_("processing_stopped"))
        self._processing_complete()

    def _processing_complete(self) -> None:
        """Handle processing completion."""
        self.is_processing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.set(1)
        self.progress_label.configure(text=_("processing_complete"))
        
        if self._start_time:
            total_time = time.time() - self._start_time
            self.total_time_label.configure(text=_("total_time", time=f"{total_time:.1f}"))
            self._log_message(_("processing_complete_msg", time=f"{total_time:.1f}"))
            self._update_steps_display()

        config = self._create_config_from_ui()
        self.config_manager.save_config(config)

    def _log_message(self, message: str) -> None:
        """Log message to output panel."""
        self.process_log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        msg_color = self.COLORS["text"]
        
        if "✅" in message or _("processing_complete") in message or _("asr_complete").split()[0] in message:
            msg_color = self.COLORS["success"]
        elif "❌" in message or "错误" in message or "Error" in message or "Exception" in message:
            msg_color = self.COLORS["danger"]
        elif "⚠️" in message or _("warning") in message:
            msg_color = self.COLORS["warning"]
        elif "ℹ️" in message or "🔍" in message or "📥" in message or "📊" in message:
            msg_color = self.COLORS["primary"]
        
        self.process_log_text.insert("end", f"[{timestamp}] ", ("timestamp",))
        self.process_log_text.insert("end", f"{message}\n", ("message",))
        
        self.process_log_text.tag_config("timestamp", foreground=self.COLORS["text_dim"])
        self.process_log_text.tag_config("message", foreground=msg_color)
        
        self.process_log_text.configure(state="disabled")
        self.process_log_text.see("end")
    
    def _record_step(self, stage: str, progress: float) -> None:
        """Record step timing."""
        current_time = time.time()
        
        step_name = stage.split('|')[0].strip()
        
        if step_name != self._current_step:
            if self._current_step and self._current_step in self._step_times:
                start_time, _ = self._step_times[self._current_step]
                self._step_times[self._current_step] = (start_time, current_time)
            
            self._current_step = step_name
            self._step_times[step_name] = (current_time, None)
        
        self._update_steps_display()
    
    def _update_steps_display(self) -> None:
        """Update the steps timing display."""
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        
        total_time = 0.0
        completed_steps = []
        current_step_info = None
        
        for step_name, (start_time, end_time) in self._step_times.items():
            if end_time is not None:
                duration = end_time - start_time
                total_time += duration
                completed_steps.append((step_name, duration, True))
            elif step_name == self._current_step:
                current_duration = time.time() - start_time
                current_step_info = (step_name, current_duration, False)
        
        estimated_total = total_time
        if current_step_info:
            estimated_total += current_step_info[1]
        
        step_icons = {
            _("load_model"): "🧠",
            _("extract_audio"): "🎵",
            _("speech_recognition"): "🎙️",
            _("generate_subtitle"): "📝",
            _("save_subtitle"): "💾",
            _("processing"): "⚡",
        }
        
        for step_name, duration, is_completed in completed_steps:
            icon = step_icons.get(step_name, "✅")
            percentage = (duration / estimated_total * 100) if estimated_total > 0 else 0
            
            bar_length = 40
            filled = int(bar_length * (duration / estimated_total)) if estimated_total > 0 else 0
            bar = "▓" * filled + "░" * (bar_length - filled)
            
            self.steps_text.insert("end", f"{icon} {step_name}\n", ("step_title",))
            self.steps_text.insert("end", f"   {bar} {percentage:4.1f}%  {duration:5.1f}s\n", ("step_detail",))
        
        if current_step_info:
            step_name, duration, is_completed = current_step_info
            icon = step_icons.get(step_name, "🔄")
            percentage = (duration / estimated_total * 100) if estimated_total > 0 else 0
            
            bar_length = 40
            filled = int(bar_length * (duration / estimated_total)) if estimated_total > 0 else 0
            bar = "▓" * filled + "▒" + "░" * (bar_length - filled - 1)
            
            self.steps_text.insert("end", f"\n{icon} {step_name}{_('current_step')}\n", ("current_title",))
            self.steps_text.insert("end", f"   {bar} {percentage:4.1f}%  {duration:5.1f}s\n", ("current_detail",))
        
        if estimated_total > 0:
            self.steps_text.insert("end", "\n" + "─" * 55 + "\n", ("divider",))
            
            total_icon = "⏱️"
            self.steps_text.insert("end", f"{total_icon} {_('total_elapsed', time=f'{estimated_total:.1f}')}\n", ("total",))
            
            self.total_time_label.configure(text=_("total_time", time=f"{estimated_total:.1f}"))
        
        self.steps_text.tag_config("step_title", foreground=self.COLORS["success"])
        self.steps_text.tag_config("step_detail", foreground=self.COLORS["text_dim"])
        self.steps_text.tag_config("current_title", foreground=self.COLORS["primary"])
        self.steps_text.tag_config("current_detail", foreground=self.COLORS["text"])
        self.steps_text.tag_config("divider", foreground=self.COLORS["border"])
        self.steps_text.tag_config("total", foreground=self.COLORS["primary"])
        
        self.steps_text.configure(state="disabled")
        self.steps_text.see("end")
    
    def _reset_timing(self) -> None:
        """Reset timing information."""
        self._start_time = None
        self._step_times.clear()
        self._current_step = None
        self.total_time_label.configure(text=_("total_time", time="0.0"))
        self.process_log_text.configure(state="normal")
        self.process_log_text.delete("1.0", "end")
        self.process_log_text.configure(state="disabled")
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        self.steps_text.configure(state="disabled")


def main() -> None:
    """Main entry point for GUI."""
    app = VideoSubtitleGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
