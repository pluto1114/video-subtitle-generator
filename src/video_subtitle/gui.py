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

        self.title("Video Subtitle Generator")
        self.geometry("1200x800")

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

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

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
        file_frame = ctk.CTkFrame(parent)
        file_frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            file_frame, text="视频文件列表", font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.file_listbox = tk.Listbox(
            file_frame,
            selectmode=tk.EXTENDED,
            font=("Arial", 10),
        )
        self.file_listbox.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=5
        )

        scrollbar = ttk.Scrollbar(
            file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview
        )
        scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        add_btn = ctk.CTkButton(
            btn_frame, text="添加文件", command=self._add_files, width=100
        )
        add_btn.grid(row=0, column=0, padx=5)

        remove_btn = ctk.CTkButton(
            btn_frame, text="移除选中", command=self._remove_selected, width=100
        )
        remove_btn.grid(row=0, column=1, padx=5)

        clear_btn = ctk.CTkButton(
            btn_frame, text="清空列表", command=self._clear_files, width=100
        )
        clear_btn.grid(row=0, column=2, padx=5)

    def _create_config_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create configuration panel."""
        config_frame = ctk.CTkFrame(parent)
        config_frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        config_frame.grid_rowconfigure(0, weight=1)
        config_frame.grid_columnconfigure(0, weight=1)

        scrollable_frame = ctk.CTkScrollableFrame(config_frame)
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        title_label = ctk.CTkLabel(
            scrollable_frame,
            text="参数配置",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", pady=10)

        row_idx = 1

        row_idx = self._create_basic_config_section(scrollable_frame, row_idx)
        row_idx = self._create_advanced_config_section(scrollable_frame, row_idx)

    def _create_basic_config_section(
        self, parent, start_row: int
    ) -> int:
        """Create basic configuration section."""
        basic_label = ctk.CTkLabel(
            parent, text="基础参数", font=ctk.CTkFont(weight="bold")
        )
        basic_label.grid(row=start_row, column=0, sticky="w", pady=5)
        start_row += 1

        model_label = ctk.CTkLabel(parent, text="模型:")
        model_label.grid(row=start_row, column=0, sticky="w", pady=2)
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
            width=300,
        )
        model_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        lang_label = ctk.CTkLabel(parent, text="语言:")
        lang_label.grid(row=start_row, column=0, sticky="w", pady=2)
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
            width=300,
        )
        lang_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        format_label = ctk.CTkLabel(parent, text="字幕格式:")
        format_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.format_var = ctk.StringVar(value=self.config.subtitle_format.value)
        format_combo = ctk.CTkComboBox(
            parent,
            variable=self.format_var,
            values=["srt", "ass"],
            width=300,
        )
        format_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        output_label = ctk.CTkLabel(parent, text="输出目录:")
        output_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.output_var = ctk.StringVar(value=self.config.output_dir or "")
        output_entry = ctk.CTkEntry(parent, textvariable=self.output_var, width=300)
        output_entry.grid(row=start_row, column=1, padx=10, pady=2)
        output_btn = ctk.CTkButton(
            parent, text="浏览", command=self._browse_output, width=80
        )
        output_btn.grid(row=start_row, column=2, padx=5, pady=2)
        start_row += 1

        return start_row

    def _create_advanced_config_section(
        self, parent, start_row: int
    ) -> int:
        """Create advanced configuration section."""
        advanced_label = ctk.CTkLabel(
            parent, text="高级参数", font=ctk.CTkFont(weight="bold")
        )
        advanced_label.grid(row=start_row, column=0, sticky="w", pady=10)
        start_row += 1

        quality_label = ctk.CTkLabel(parent, text="质量模式:")
        quality_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.quality_var = ctk.StringVar(value=self.config.quality_mode.value)
        quality_combo = ctk.CTkComboBox(
            parent,
            variable=self.quality_var,
            values=["pro", "quality", "balanced", "speed"],
            width=300,
        )
        quality_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        enhance_label = ctk.CTkLabel(parent, text="音频增强:")
        enhance_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.enhance_var = ctk.StringVar(
            value=self.config.audio_enhance_profile.value
        )
        enhance_combo = ctk.CTkComboBox(
            parent,
            variable=self.enhance_var,
            values=["off", "voice", "strong"],
            width=300,
        )
        enhance_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        vad_label = ctk.CTkLabel(parent, text="VAD 配置:")
        vad_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.vad_var = ctk.StringVar(value=self.config.vad_profile.value)
        vad_combo = ctk.CTkComboBox(
            parent,
            variable=self.vad_var,
            values=["voice_focus", "balanced", "noise_robust", "fast", "sensitive", "ultra_sensitive"],
            width=300,
        )
        vad_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        self.vad_enabled_var = ctk.BooleanVar(value=self.config.use_vad)
        vad_check = ctk.CTkCheckBox(
            parent, text="启用 VAD", variable=self.vad_enabled_var
        )
        vad_check.grid(row=start_row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        start_row += 1

        device_label = ctk.CTkLabel(parent, text="设备选择:")
        device_label.grid(row=start_row, column=0, sticky="w", pady=2)
        self.device_var = ctk.StringVar(value=self.config.model_config.device)
        device_combo = ctk.CTkComboBox(
            parent,
            variable=self.device_var,
            values=["auto", "cuda", "cpu"],
            width=300,
        )
        device_combo.grid(row=start_row, column=1, padx=10, pady=2)
        start_row += 1

        self.overwrite_var = ctk.BooleanVar(value=self.config.overwrite)
        overwrite_check = ctk.CTkCheckBox(
            parent, text="覆盖已存在文件", variable=self.overwrite_var
        )
        overwrite_check.grid(
            row=start_row, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )
        start_row += 1

        voice_priority_btn = ctk.CTkButton(
            parent,
            text="人声优先模板",
            command=self._apply_voice_priority,
            width=150,
        )
        voice_priority_btn.grid(
            row=start_row, column=0, columnspan=2, padx=10, pady=10
        )
        start_row += 1

        return start_row

    def _create_control_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create control panel."""
        control_frame = ctk.CTkFrame(parent)
        control_frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        control_frame.grid_columnconfigure(0, weight=1)

        self.start_btn = ctk.CTkButton(
            control_frame,
            text="开始处理",
            command=self._start_processing,
            height=50,
            font=ctk.CTkFont(size=18),
        )
        self.start_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="停止",
            command=self._stop_processing,
            height=50,
            font=ctk.CTkFont(size=18),
            state="disabled",
        )
        self.stop_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(control_frame)
        self.progress_bar.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            control_frame, text="就绪", font=ctk.CTkFont(size=14)
        )
        self.progress_label.grid(row=3, column=0, padx=10, pady=5)
        
        # 总用时显示
        self.total_time_label = ctk.CTkLabel(
            control_frame, 
            text="总用时：0.0s", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2196F3"
        )
        self.total_time_label.grid(row=4, column=0, padx=10, pady=5)

    def _create_output_panel(
        self, parent: ctk.CTkFrame, row: int, column: int
    ) -> None:
        """Create output panel."""
        output_frame = ctk.CTkFrame(parent)
        output_frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        output_frame.grid_rowconfigure(2, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            output_frame, text="处理过程", font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # 执行过程日志
        self.process_log_text = ctk.CTkTextbox(output_frame, state="normal", height=300)
        self.process_log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # 步骤用时统计
        steps_title = ctk.CTkLabel(
            output_frame, 
            text="步骤用时统计", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        steps_title.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.steps_text = ctk.CTkTextbox(output_frame, state="normal", height=150)
        self.steps_text.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

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
        """Log message to output panel."""
        self.process_log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.process_log_text.insert("end", f"[{timestamp}] {message}\n")
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
        """Update the steps timing display."""
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        
        total_time = 0.0
        for step_name, (start_time, end_time) in self._step_times.items():
            if end_time is not None:
                duration = end_time - start_time
                total_time += duration
                bar_length = min(30, int(duration))
                bar = "█" * bar_length + "░" * (30 - bar_length)
                self.steps_text.insert("end", f"{bar} {step_name}: {duration:.1f}s\n")
        
        if self._current_step and self._current_step in self._step_times:
            start_time, _ = self._step_times[self._current_step]
            current_duration = time.time() - start_time
            total_time += current_duration
            bar_length = min(30, int(current_duration))
            bar = "█" * bar_length + "░" * (30 - bar_length)
            self.steps_text.insert("end", f"{bar} {self._current_step}: {current_duration:.1f}s (进行中)\n")
        
        if total_time > 0:
            self.steps_text.insert("end", "\n" + "="*50 + "\n")
            self.steps_text.insert("end", f"总用时：{total_time:.1f}s\n")
            self.total_time_label.configure(text=f"总用时：{total_time:.1f}s")
        
        self.steps_text.configure(state="disabled")
        self.steps_text.see("end")
    
    def _reset_timing(self) -> None:
        """Reset timing information."""
        self._start_time = None
        self._step_times.clear()
        self._current_step = None
        self.total_time_label.configure(text="总用时：0.0s")
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
