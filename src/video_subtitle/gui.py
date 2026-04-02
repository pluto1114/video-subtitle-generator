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

# 自定义日志处理器，用于将日志发送到 GUI
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

        self.title("视频字幕生成器 - Video Subtitle Generator")
        self.geometry("1300x850")
        
        # 设置主题和配色
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 配色方案 - 更加专业协调
        self.COLORS = {
            "primary": "#6366F1",
            "primary_hover": "#4F46E5",
            "success": "#22C55E",
            "success_hover": "#16A34A",
            "warning": "#F97316",
            "warning_hover": "#EA580C",
            "danger": "#EF4444",
            "danger_hover": "#DC2626",
            "neutral": "#6B7280",
            "neutral_hover": "#4B5563",
            "bg_dark": "#0F172A",
            "bg_medium": "#1E293B",
            "bg_light": "#334155",
            "border": "#475569",
            "text": "#F8FAFC",
            "text_dim": "#94A3B8",
        }

        self.config = Config()
        self.config_manager = ConfigManager()
        self.video_files: list[str] = []
        self.processor: Optional[VideoProcessor] = None
        self.is_processing = False
        
        # 计时相关
        self._start_time: Optional[float] = None
        self._step_times: dict[str, tuple[float, float]] = {}  # step_name -> (start_time, end_time)
        self._current_step: Optional[str] = None

        self._load_last_config()
        self._create_ui()

    def _load_last_config(self) -> None:
        """Load last used configuration."""
        if self.config_manager.config_exists():
            try:
                self.config = self.config_manager.load_config()
                logger.info("Loaded last configuration")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

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

        self._create_file_panel(main_frame, 0, 0)
        self._create_config_panel(main_frame, 1, 0)
        self._create_control_panel(main_frame, 0, 1)
        self._create_output_panel(main_frame, 1, 1)
        
        # 添加 GUI 日志处理器
        gui_handler = GUILogHandler(self)
        logging.getLogger().addHandler(gui_handler)

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
            text="📁 视频文件列表", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        # 使用自定义样式的Listbox
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
            text="➕ 添加文件", 
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
            text="🗑️ 移除选中", 
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
            text="🆑 清空列表", 
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
            text="⚙️ 参数配置",
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
            text="📋 基础参数", 
            font=ctk.CTkFont(weight="bold", size=15),
            text_color=self.COLORS["primary"]
        )
        basic_label.grid(row=start_row, column=0, sticky="w", pady=(10, 8), columnspan=3)
        start_row += 1

        model_label = ctk.CTkLabel(parent, text="模型:", text_color=self.COLORS["text_dim"])
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

        lang_label = ctk.CTkLabel(parent, text="语言:", text_color=self.COLORS["text_dim"])
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

        format_label = ctk.CTkLabel(parent, text="字幕格式:", text_color=self.COLORS["text_dim"])
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

        output_label = ctk.CTkLabel(parent, text="输出目录:", text_color=self.COLORS["text_dim"])
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
            text="浏览", 
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
            text="🔧 高级参数", 
            font=ctk.CTkFont(weight="bold", size=15),
            text_color=self.COLORS["primary"]
        )
        advanced_label.grid(row=start_row, column=0, sticky="w", pady=(15, 8), columnspan=3)
        start_row += 1

        quality_label = ctk.CTkLabel(parent, text="质量模式:", text_color=self.COLORS["text_dim"])
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

        enhance_label = ctk.CTkLabel(parent, text="音频增强:", text_color=self.COLORS["text_dim"])
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

        vad_label = ctk.CTkLabel(parent, text="VAD 配置:", text_color=self.COLORS["text_dim"])
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
            text="启用 VAD", 
            variable=self.vad_enabled_var,
            text_color=self.COLORS["text"],
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6
        )
        vad_check.grid(row=start_row, column=0, columnspan=3, sticky="w", padx=0, pady=8)
        start_row += 1

        device_label = ctk.CTkLabel(parent, text="设备选择:", text_color=self.COLORS["text_dim"])
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
            text="覆盖已存在文件", 
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
            text="🎤 人声优先模板",
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
            text="🎮 控制面板",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 10))

        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ 开始处理",
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
            text="⏹️ 停止",
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

        # 进度条区域
        progress_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        progress_container.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_container, height=10)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container, 
            text="就绪", 
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["text_dim"]
        )
        self.progress_label.grid(row=1, column=0, sticky="w")
        
        # 总用时显示
        self.total_time_label = ctk.CTkLabel(
            progress_container, 
            text="⏱️ 总用时：0.0s", 
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
            text="📝 处理过程", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS["text"]
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        # 执行过程日志
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
        
        # 步骤用时统计
        steps_title = ctk.CTkLabel(
            output_frame, 
            text="⏱️ 步骤用时统计", 
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
            ("视频文件", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm"),
            ("所有文件", "*.*"),
        ]
        files = filedialog.askopenfilenames(
            title="选择视频文件",
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
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_var.set(directory)

    def _apply_voice_priority(self) -> None:
        """Apply voice priority template (now uses default config)."""
        # 现在默认配置已经是优化后的参数
        self.quality_var.set("pro")
        self.enhance_var.set("off")
        self.vad_var.set("sensitive")
        self.vad_enabled_var.set(False)
        self._log_message("已应用优化后的默认配置（人声优先）")

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

        Config.apply_quality_mode(config, config.quality_mode)
        Config.apply_vad_profile(config, config.vad_profile)

        return config

    def _start_processing(self) -> None:
        """Start processing video files."""
        if not self.video_files:
            messagebox.showwarning("警告", "请先添加视频文件")
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # 重置计时和日志
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
            # 记录步骤信息并更新显示
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
                        lambda: self._log_message(f"字幕已保存：{output_path}"),
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
                            f"批量处理完成：{len(results)} 个文件"
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
        """Stop processing (placeholder)."""
        self.is_processing = False
        self._log_message("处理已停止")
        self._processing_complete()

    def _processing_complete(self) -> None:
        """Handle processing completion."""
        self.is_processing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_bar.set(1)
        self.progress_label.configure(text="处理完成")
        
        # 更新最终时间
        if self._start_time:
            total_time = time.time() - self._start_time
            self.total_time_label.configure(text=f"总用时：{total_time:.1f}s")
            self._log_message(f"✅ 处理完成，总用时：{total_time:.1f}s")
            self._update_steps_display()

        config = self._create_config_from_ui()
        self.config_manager.save_config(config)

    def _log_message(self, message: str) -> None:
        """Log message to output panel with color coding."""
        self.process_log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        
        # 确定消息类型和对应颜色
        msg_color = self.COLORS["text"]
        
        if "✅" in message or "成功" in message or "完成" in message:
            msg_color = self.COLORS["success"]
        elif "❌" in message or "错误" in message or "Error" in message or "Exception" in message:
            msg_color = self.COLORS["danger"]
        elif "⚠️" in message or "警告" in message or "Warning" in message:
            msg_color = self.COLORS["warning"]
        elif "ℹ️" in message or "🔍" in message or "📥" in message or "📊" in message or "检测" in message or "正在" in message:
            msg_color = self.COLORS["primary"]
        
        # 添加时间戳（灰色）
        self.process_log_text.insert("end", f"[{timestamp}] ", ("timestamp",))
        # 添加消息主体（带颜色）
        self.process_log_text.insert("end", f"{message}\n", ("message",))
        
        # 配置标签
        self.process_log_text.tag_config("timestamp", foreground=self.COLORS["text_dim"])
        self.process_log_text.tag_config("message", foreground=msg_color)
        
        self.process_log_text.configure(state="disabled")
        self.process_log_text.see("end")
    
    def _record_step(self, stage: str, progress: float) -> None:
        """Record step timing information from progress callback."""
        current_time = time.time()
        
        # 从阶段文本中提取步骤名称（去除时间信息）
        step_name = stage.split('|')[0].strip()
        
        # 如果开始新步骤，记录开始时间
        if step_name != self._current_step:
            # 结束上一个步骤
            if self._current_step and self._current_step in self._step_times:
                start_time, _ = self._step_times[self._current_step]
                self._step_times[self._current_step] = (start_time, current_time)
            
            # 开始新步骤
            self._current_step = step_name
            self._step_times[step_name] = (current_time, None)
        
        # 更新显示
        self._update_steps_display()
    
    def _log_process_step(self, step_name: str, message: str) -> None:
        """Log a process step with timing."""
        current_time = time.time()
        
        # 如果开始新步骤，记录开始时间
        if step_name != self._current_step:
            # 结束上一个步骤
            if self._current_step and self._current_step in self._step_times:
                start_time, _ = self._step_times[self._current_step]
                self._step_times[self._current_step] = (start_time, current_time)
            
            # 开始新步骤
            self._current_step = step_name
            self._step_times[step_name] = (current_time, None)
        
        self._log_message(f"{step_name}: {message}")
    
    def _update_steps_display(self) -> None:
        """Update the steps timing display with enhanced visuals."""
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        
        total_time = 0.0
        completed_steps = []
        current_step_info = None
        
        # 收集步骤信息
        for step_name, (start_time, end_time) in self._step_times.items():
            if end_time is not None:
                duration = end_time - start_time
                total_time += duration
                completed_steps.append((step_name, duration, True))
            elif step_name == self._current_step:
                current_duration = time.time() - start_time
                current_step_info = (step_name, current_duration, False)
        
        # 计算预估总时间
        estimated_total = total_time
        if current_step_info:
            estimated_total += current_step_info[1]
        
        # 显示完成的步骤
        step_icons = {
            "加载模型": "🧠",
            "提取音频": "🎵",
            "语音识别": "🎙️",
            "生成字幕": "📝",
            "保存字幕": "💾",
            "处理": "⚡",
        }
        
        for step_name, duration, is_completed in completed_steps:
            icon = step_icons.get(step_name, "✅")
            percentage = (duration / estimated_total * 100) if estimated_total > 0 else 0
            
            # 进度条
            bar_length = 40
            filled = int(bar_length * (duration / estimated_total)) if estimated_total > 0 else 0
            bar = "▓" * filled + "░" * (bar_length - filled)
            
            # 插入带样式的文本
            self.steps_text.insert("end", f"{icon} {step_name}\n", ("step_title",))
            self.steps_text.insert("end", f"   {bar} {percentage:4.1f}%  {duration:5.1f}s\n", ("step_detail",))
        
        # 显示当前进行中的步骤
        if current_step_info:
            step_name, duration, is_completed = current_step_info
            icon = step_icons.get(step_name, "🔄")
            percentage = (duration / estimated_total * 100) if estimated_total > 0 else 0
            
            bar_length = 40
            filled = int(bar_length * (duration / estimated_total)) if estimated_total > 0 else 0
            bar = "▓" * filled + "▒" + "░" * (bar_length - filled - 1)
            
            self.steps_text.insert("end", f"\n{icon} {step_name} (进行中)\n", ("current_title",))
            self.steps_text.insert("end", f"   {bar} {percentage:4.1f}%  {duration:5.1f}s\n", ("current_detail",))
        
        # 显示总计
        if estimated_total > 0:
            self.steps_text.insert("end", "\n" + "─" * 55 + "\n", ("divider",))
            
            total_icon = "⏱️"
            self.steps_text.insert("end", f"{total_icon} 总用时：{estimated_total:.1f}s\n", ("total",))
            
            # 更新顶部总时间标签
            self.total_time_label.configure(text=f"⏱️ 总用时：{estimated_total:.1f}s")
        
        # 配置标签样式
        self.steps_text.tag_config("step_title", foreground=self.COLORS["success"], font=("Segoe UI", 11, "bold"))
        self.steps_text.tag_config("step_detail", foreground=self.COLORS["text_dim"], font=("Consolas", 10))
        self.steps_text.tag_config("current_title", foreground=self.COLORS["primary"], font=("Segoe UI", 11, "bold"))
        self.steps_text.tag_config("current_detail", foreground=self.COLORS["text"], font=("Consolas", 10))
        self.steps_text.tag_config("divider", foreground=self.COLORS["border"])
        self.steps_text.tag_config("total", foreground=self.COLORS["primary"], font=("Segoe UI", 12, "bold"))
        
        self.steps_text.configure(state="disabled")
        self.steps_text.see("end")
    
    def _reset_timing(self) -> None:
        """Reset timing information."""
        self._start_time = None
        self._step_times.clear()
        self._current_step = None
        self.total_time_label.configure(text="⏱️ 总用时：0.0s")
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
