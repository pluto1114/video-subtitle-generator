#!/usr/bin/env python
"""Analyze subtitle content."""

import re

filename = "[Dynamis One] 青梅竹馬的戀愛喜劇無法成立 - 11 (Baha 1920x1080 AVC AAC MP4) [C5284A77].srt"
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
timestamp_lines = [l for l in lines if '-->' in l]

# 统计包含"あっ"的片段
a_count = 0
for line in lines:
    if 'あっ' in line:
        a_count += 1

print(f"总片段数：{len(timestamp_lines)}")
print(f"包含\"あっ\"的片段数：{a_count}")
print(f"占比：{a_count/len(timestamp_lines)*100:.1f}%")
print()

# 找出 12:30-15:45 之间的所有片段
print("=== 12:30-15:45 之间的片段统计 ===")
count_12_15 = 0
a_count_12_15 = 0
for ts in timestamp_lines:
    match = re.search(r'(\d{2}):(\d{2}):(\d{2})', ts)
    if match:
        h, m, s = match.groups()
        minute = int(h) * 60 + int(m)
        second = int(s)
        total_seconds = minute * 60 + second
        
        # 12:30 = 750 秒，15:45 = 945 秒
        if 750 <= total_seconds <= 945:
            count_12_15 += 1
            idx = lines.index(ts)
            if idx + 1 < len(lines):
                dialog = lines[idx + 1].strip()
                if 'あっ' in dialog:
                    a_count_12_15 += 1

print(f"12:30-15:45 之间的片段数：{count_12_15}")
print(f"包含\"あっ\"的片段数：{a_count_12_15}")
print(f"占比：{a_count_12_15/count_12_15*100:.1f}%")
print()

print("结论:")
if a_count_12_15 / count_12_15 > 0.8:
    print("这段视频可能真的没有对话，或者 ASR 引擎出现了幻觉")
    print("建议检查原始视频或使用更强力的 ASR 模型")
else:
    print("这段视频有正常对话，需要进一步优化 ASR 参数")
