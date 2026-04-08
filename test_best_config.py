"""使用智能对齐算法优化字幕匹配"""
import logging
from pathlib import Path
from src.video_subtitle.config import Config, ModelConfig, VADProfile, AudioEnhanceProfile
from src.video_subtitle.processor import VideoProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    video_path = Path(r"d:\AI-dev\video-subtitle-generator\video\[Kamigami&VCB-Studio] Boku dake ga Inai Machi [01][720p][x264_aac].mp4")
    reference_path = Path(r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt")
    
    print("="*80)
    print("使用最佳参数配置测试字幕生成")
    print("="*80)
    
    config = Config()
    config.model_config.language = "ja"
    config.model_config.model_name = "large-v3-turbo"
    config.use_vad = False
    config.audio_enhance_profile = AudioEnhanceProfile.OFF
    
    print(f"\n配置参数:")
    print(f"  语言：{config.model_config.language}")
    print(f"  模型：{config.model_config.model_name}")
    print(f"  VAD: {config.use_vad} (关闭以避免过度分段)")
    print(f"  音频增强：{config.audio_enhance_profile}")
    print(f"  后处理：启用智能分段")
    
    processor = VideoProcessor(config)
    
    print("\n开始生成字幕...")
    subtitle = processor.process_video(str(video_path))
    
    output_path = video_path.parent / "best_test.srt"
    processor.save_subtitle(subtitle, str(output_path))
    print(f"\n生成的字幕已保存到：{output_path}")
    print(f"生成的字幕片段数：{len(subtitle.segments)}")
    
    print("\n前 20 条字幕预览:")
    for i, seg in enumerate(subtitle.segments[:20]):
        time_str = f"{seg.start_ms//1000//60}:{seg.start_ms//1000%60:02d}:{seg.start_ms%1000:03d} --> {seg.end_ms//1000//60}:{seg.end_ms//1000%60:02d}:{seg.end_ms%1000:03d}"
        print(f"{i+1}. [{time_str}] {seg.text[:50]}")

if __name__ == "__main__":
    main()
