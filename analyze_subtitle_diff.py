"""分析生成字幕与参考字幕的差异"""
import re
from pathlib import Path

def load_srt(path):
    """加载 SRT 文件并提取主要文本（忽略振り仮名）"""
    segments = []
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
                
                # 只保留主文本行（较长的完整句子）
                # 振り仮名通常是单个假名，很短
                main_text_lines = []
                for line in text.split('\n'):
                    if len(line.strip()) > 2:  # 主文本通常较长
                        main_text_lines.append(line.strip())
                
                if main_text_lines:
                    time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
                    if time_match:
                        h1, m1, s1, ms1 = int(time_match.group(1)), int(time_match.group(2)), int(time_match.group(3)), int(time_match.group(4))
                        h2, m2, s2, ms2 = int(time_match.group(5)), int(time_match.group(6)), int(time_match.group(7)), int(time_match.group(8))
                        
                        start_ms = h1 * 3600000 + m1 * 60000 + s1 * 1000 + ms1
                        end_ms = h2 * 3600000 + m2 * 60000 + s2 * 1000 + ms2
                        
                        main_text = ' '.join(main_text_lines)
                        segments.append({
                            'index': index,
                            'start_ms': start_ms,
                            'end_ms': end_ms,
                            'text': main_text
                        })
            except Exception as e:
                continue
    
    return segments

def normalize_text(text):
    """标准化文本以便比较"""
    # 移除空格和标点符号的差异
    text = text.strip()
    # 统一标点
    text = text.replace('、', ',').replace('。', '.').replace('？', '?').replace('！', '!')
    text = text.replace(',', '').replace('.', '').replace('?', '').replace('!', '').replace(' ', '')
    return text

def compare_texts(gen_text, ref_text):
    """比较两个文本的相似度"""
    gen_norm = normalize_text(gen_text)
    ref_norm = normalize_text(ref_text)
    
    if gen_norm == ref_norm:
        return 1.0
    
    # 计算编辑距离
    def edit_distance(s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + 1)
        return dp[m][n]
    
    dist = edit_distance(gen_norm, ref_norm)
    max_len = max(len(gen_norm), len(ref_norm))
    similarity = 1 - dist / max_len if max_len > 0 else 1.0
    return similarity

def main():
    gen_path = Path(r"d:\AI-dev\video-subtitle-generator\video\generated_test.srt")
    ref_path = Path(r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt")
    
    gen_segments = load_srt(gen_path)
    ref_segments = load_srt(ref_path)
    
    print(f"生成字幕片段数（仅主文本）: {len(gen_segments)}")
    print(f"参考字幕片段数（仅主文本）: {len(ref_segments)}")
    
    # 基于时间重叠进行匹配
    matches = []
    ref_matched = set()
    
    for i, gen_seg in enumerate(gen_segments):
        best_match_idx = None
        best_overlap = 0
        best_similarity = 0
        
        for j, ref_seg in enumerate(ref_segments):
            if j in ref_matched:
                continue
            
            # 计算时间重叠
            overlap_start = max(gen_seg['start_ms'], ref_seg['start_ms'])
            overlap_end = min(gen_seg['end_ms'], ref_seg['end_ms'])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > 0:
                similarity = compare_texts(gen_seg['text'], ref_seg['text'])
                # 综合考虑时间重叠和文本相似度
                score = overlap * (1 + similarity)
                
                if score > best_overlap:
                    best_overlap = score
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
    
    # 分析匹配质量
    high_quality = sum(1 for m in matches if m['similarity'] >= 0.9)
    medium_quality = sum(1 for m in matches if 0.7 <= m['similarity'] < 0.9)
    low_quality = sum(1 for m in matches if m['similarity'] < 0.7)
    
    print(f"\n匹配质量分析:")
    print(f"  高质量（相似度≥90%）: {high_quality} ({high_quality/len(matches)*100:.1f}%)")
    print(f"  中等质量（70%-90%）: {medium_quality} ({medium_quality/len(matches)*100:.1f}%)")
    print(f"  低质量（<70%）: {low_quality} ({low_quality/len(matches)*100:.1f}%)")
    
    # 显示低质量匹配示例
    print(f"\n低质量匹配示例（前 10 个）:")
    low_quality_matches = [m for m in matches if m['similarity'] < 0.7]
    for i, m in enumerate(low_quality_matches[:10]):
        print(f"\n{i+1}. 相似度：{m['similarity']:.2f}")
        print(f"   生成：{m['gen_text'][:60]}...")
        print(f"   参考：{m['ref_text'][:60]}...")
        print(f"   时间差：开始{m['time_diff_start']}ms, 结束{m['time_diff_end']}ms")
    
    # 计算平均相似度
    avg_similarity = sum(m['similarity'] for m in matches) / len(matches) if matches else 0
    print(f"\n平均文本相似度：{avg_similarity:.2%}")
    
    # 时间轴精度分析
    time_accurate = sum(1 for m in matches if m['time_diff_start'] <= 500 and m['time_diff_end'] <= 500)
    print(f"时间轴精确匹配（误差≤500ms）: {time_accurate} ({time_accurate/len(matches)*100:.1f}%)")

if __name__ == "__main__":
    main()
