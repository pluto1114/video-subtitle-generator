"""使用优化参数重新测试字幕生成"""
import logging
from pathlib import Path
from src.video_subtitle.config import Config, ModelConfig, VADProfile, AudioEnhanceProfile, QualityMode
from src.video_subtitle.processor import VideoProcessor
from src.video_subtitle.subtitle import Subtitle
from analyze_subtitle_diff import load_srt, compare_texts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    video_path = Path(r"d:\AI-dev\video-subtitle-generator\video\[Kamigami&VCB-Studio] Boku dake ga Inai Machi [01][720p][x264_aac].mp4")
    reference_path = Path(r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt")
    
    if not video_path.exists():
        print(f"错误：视频文件不存在：{video_path}")
        return
    
    print("="*80)
    print("使用优化参数重新测试字幕生成")
    print("="*80)
    
    config = Config()
    config.model_config.language = "ja"
    config.model_config.model_name = "large-v3-turbo"
    config.use_vad = True
    config.vad_profile = VADProfile.SENSITIVE
    config.vad_config.vad_min_speech_ms = 10
    config.vad_config.vad_max_speech_s = 30.0
    config.vad_config.vad_min_silence_ms = 30
    config.vad_config.vad_speech_pad_ms = 200
    config.audio_enhance_profile = AudioEnhanceProfile.OFF
    
    print(f"\n优化配置:")
    print(f"  语言：{config.model_config.language}")
    print(f"  模型：{config.model_config.model_name}")
    print(f"  VAD: {config.use_vad} (启用更精细的分段)")
    print(f"  VAD 最小语音时长：{config.vad_config.vad_min_speech_ms}ms")
    print(f"  VAD 最大语音时长：{config.vad_config.vad_max_speech_s}s")
    print(f"  VAD 最小静音时长：{config.vad_config.vad_min_silence_ms}ms")
    
    processor = VideoProcessor(config)
    
    print("\n开始生成字幕...")
    subtitle = processor.process_video(str(video_path))
    
    output_path = video_path.parent / "optimized_test.srt"
    processor.save_subtitle(subtitle, str(output_path))
    print(f"\n生成的字幕已保存到：{output_path}")
    
    print("\n加载参考字幕进行对比...")
    gen_segments = load_srt(output_path)
    ref_segments = load_srt(reference_path)
    
    print(f"\n生成字幕片段数：{len(gen_segments)}")
    print(f"参考字幕片段数（仅主文本）: {len(ref_segments)}")
    
    matches = []
    ref_matched = set()
    
    for i, gen_seg in enumerate(gen_segments):
        best_match_idx = None
        best_score = 0
        
        for j, ref_seg in enumerate(ref_segments):
            if j in ref_matched:
                continue
            
            overlap_start = max(gen_seg['start_ms'], ref_seg['start_ms'])
            overlap_end = min(gen_seg['end_ms'], ref_seg['end_ms'])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > 0:
                similarity = compare_texts(gen_seg['text'], ref_seg['text'])
                score = overlap * (1 + similarity)
                
                if score > best_score:
                    best_score = score
                    best_match_idx = j
                    best_similarity = similarity
        
        if best_match_idx is not None:
            ref_seg = ref_segments[best_match_idx]
            matches.append({
                'gen_index': i,
                'ref_index': best_match_idx,
                'gen_text': gen_seg['text'],
                'ref_text': ref_seg['text'],
                'similarity': best_similarity,
                'time_diff_start': abs(gen_seg['start_ms'] - ref_seg['start_ms']),
                'time_diff_end': abs(gen_seg['end_ms'] - ref_seg['end_ms'])
            })
            ref_matched.add(best_match_idx)
    
    print(f"\n匹配到的片段数：{len(matches)}")
    
    high_quality = sum(1 for m in matches if m['similarity'] >= 0.9)
    medium_quality = sum(1 for m in matches if 0.7 <= m['similarity'] < 0.9)
    low_quality = sum(1 for m in matches if m['similarity'] < 0.7)
    
    print(f"\n匹配质量分析:")
    print(f"  高质量（相似度≥90%）: {high_quality} ({high_quality/len(matches)*100:.1f}%)")
    print(f"  中等质量（70%-90%）: {medium_quality} ({medium_quality/len(matches)*100:.1f}%)")
    print(f"  低质量（<70%）: {low_quality} ({low_quality/len(matches)*100:.1f}%)")
    
    avg_similarity = sum(m['similarity'] for m in matches) / len(matches) if matches else 0
    print(f"\n平均文本相似度：{avg_similarity:.2%}")
    
    time_accurate = sum(1 for m in matches if m['time_diff_start'] <= 500 and m['time_diff_end'] <= 500)
    print(f"时间轴精确匹配（误差≤500ms）: {time_accurate} ({time_accurate/len(matches)*100:.1f}%)")
    
    print("\n" + "="*80)
    print("优化建议:")
    print("="*80)
    if avg_similarity < 0.85:
        print("1. 文本相似度较低，建议:")
        print("   - 检查音频质量，考虑使用音频增强")
        print("   - 尝试使用更大的模型（如 large-v3）")
        print("   - 调整 temperature 参数增加多样性")
    
    if time_accurate / len(matches) < 0.5:
        print("2. 时间轴精度较低，建议:")
        print("   - 减小 VAD 最小语音时长阈值")
        print("   - 启用 word_timestamps 进行更精细的分段")
        print("   - 调整 chunk_length 参数")

if __name__ == "__main__":
    main()
