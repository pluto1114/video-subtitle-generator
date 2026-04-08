"""测试字幕生成并与参考字幕对比"""
import logging
from pathlib import Path
from src.video_subtitle.config import Config, ModelConfig, VADProfile, AudioEnhanceProfile, QualityMode
from src.video_subtitle.processor import VideoProcessor
from src.video_subtitle.subtitle import Subtitle

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_reference_subtitle(path: str) -> Subtitle:
    """加载参考字幕文件"""
    from src.video_subtitle.subtitle import Subtitle, SubtitleSegment
    import re
    
    subtitle = Subtitle(title="Reference")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                timestamp_line = lines[1]
                text = '\n'.join(lines[2:])
                
                time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
                if time_match:
                    h1, m1, s1, ms1 = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3)), int(time_match.group(4))
                    h2, m2, s2, ms2 = int(time_match.group(5)), int(time_match.group(6)), int(time_match.group(7)), int(time_match.group(8))
                    
                    start_ms = h1 * 3600000 + m1 * 60000 + s1 * 1000 + ms1
                    end_ms = h2 * 3600000 + m2 * 60000 + s2 * 1000 + ms2
                    
                    subtitle.add_segment(start_ms, end_ms, text)
            except Exception as e:
                print(f"解析字幕块失败：{e}")
                continue
    
    return subtitle

def compare_subtitles(generated: Subtitle, reference: Subtitle, tolerance_ms: int = 500):
    """对比生成字幕和参考字幕"""
    print("\n" + "="*80)
    print("字幕对比结果")
    print("="*80)
    
    gen_segments = generated.segments
    ref_segments = reference.segments
    
    print(f"\n生成字幕片段数：{len(gen_segments)}")
    print(f"参考字幕片段数：{len(ref_segments)}")
    
    matched = 0
    partial_matched = 0
    unmatched = 0
    
    ref_matched = set()
    
    for i, gen_seg in enumerate(gen_segments):
        best_match_idx = None
        best_overlap = 0
        
        for j, ref_seg in enumerate(ref_segments):
            if j in ref_matched:
                continue
            
            overlap_start = max(gen_seg.start_ms, ref_seg.start_ms)
            overlap_end = min(gen_seg.end_ms, ref_seg.end_ms)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_match_idx = j
        
        if best_match_idx is not None:
            ref_seg = ref_segments[best_match_idx]
            gen_text = gen_seg.text.strip()
            ref_text = ref_seg.text.strip()
            
            duration_gen = gen_seg.end_ms - gen_seg.start_ms
            duration_ref = ref_seg.end_ms - ref_seg.start_ms
            
            time_diff_start = abs(gen_seg.start_ms - ref_seg.start_ms)
            time_diff_end = abs(gen_seg.end_ms - ref_seg.end_ms)
            
            if gen_text == ref_text:
                if time_diff_start <= tolerance_ms and time_diff_end <= tolerance_ms:
                    matched += 1
                    ref_matched.add(best_match_idx)
                    print(f"✓ 片段 {i+1}: 完全匹配 (时间差：开始{time_diff_start}ms, 结束{time_diff_end}ms)")
                else:
                    partial_matched += 1
                    ref_matched.add(best_match_idx)
                    print(f"~ 片段 {i+1}: 文本匹配但时间有差异 (时间差：开始{time_diff_start}ms, 结束{time_diff_end}ms)")
            else:
                unmatched += 1
                print(f"✗ 片段 {i+1}: 文本不匹配")
                print(f"  生成：{gen_text[:50]}...")
                print(f"  参考：{ref_text[:50]}...")
        else:
            unmatched += 1
            print(f"✗ 片段 {i+1}: 未找到匹配")
    
    print("\n" + "="*80)
    print("统计结果")
    print("="*80)
    print(f"完全匹配：{matched} ({matched/len(gen_segments)*100:.1f}%)")
    print(f"部分匹配：{partial_matched} ({partial_matched/len(gen_segments)*100:.1f}%)")
    print(f"不匹配：{unmatched} ({unmatched/len(gen_segments)*100:.1f}%)")
    print("="*80)

def main():
    video_path = Path(r"d:\AI-dev\video-subtitle-generator\video\[Kamigami&VCB-Studio] Boku dake ga Inai Machi [01][720p][x264_aac].mp4")
    reference_path = Path(r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt")
    
    if not video_path.exists():
        print(f"错误：视频文件不存在：{video_path}")
        return
    
    if not reference_path.exists():
        print(f"错误：参考字幕文件不存在：{reference_path}")
        return
    
    print(f"视频文件：{video_path}")
    print(f"参考字幕：{reference_path}")
    
    config = Config.voice_priority_template()
    config.model_config.language = "ja"
    config.model_config.model_name = "large-v3-turbo"
    config.use_vad = False
    config.vad_profile = VADProfile.SENSITIVE
    config.audio_enhance_profile = AudioEnhanceProfile.OFF
    
    print("\n配置信息:")
    print(f"  语言：{config.model_config.language}")
    print(f"  模型：{config.model_config.model_name}")
    print(f"  VAD: {config.use_vad}")
    print(f"  VAD Profile: {config.vad_profile}")
    print(f"  音频增强：{config.audio_enhance_profile}")
    
    processor = VideoProcessor(config)
    
    print("\n开始生成字幕...")
    subtitle = processor.process_video(str(video_path))
    
    output_path = video_path.parent / "generated_test.srt"
    processor.save_subtitle(subtitle, str(output_path))
    print(f"\n生成的字幕已保存到：{output_path}")
    
    print("\n加载参考字幕...")
    reference = load_reference_subtitle(str(reference_path))
    
    compare_subtitles(subtitle, reference, tolerance_ms=500)

if __name__ == "__main__":
    main()
