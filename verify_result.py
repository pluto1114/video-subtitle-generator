#!/usr/bin/env python
"""Verify subtitle quality."""

import re

filename = "[Dynamis One] 青梅竹馬的戀愛喜劇無法成立 - 11 (Baha 1920x1080 AVC AAC MP4) [C5284A77].srt"
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
timestamp_lines = [l for l in lines if '-->' in l]
total_segments = len(timestamp_lines)

text_segments = []
for l in lines:
    if l.strip() and not l.strip().isdigit() and '-->' not in l:
        text_segments.append(l.strip())

valid_segments = len([t for t in text_segments if len(t) > 1])
short_segments = len([t for t in text_segments if len(t) <= 1])

print("=== 字幕统计 ===")
print(f"总片段数：{total_segments}")
print(f"文本片段数：{len(text_segments)}")
print(f"有效对话片段 (>1 字符): {valid_segments}")
print(f"短片段 (≤1 字符): {short_segments}")
if total_segments > 0:
    print(f"有效率：{valid_segments/total_segments*100:.1f}%")

print("\n=== 评估结果 ===")
if valid_segments >= 300:
    print(f"✅ 达标：有效片段数 {valid_segments} >= 300")
else:
    print(f"❌ 未达标：有效片段数 {valid_segments} < 300")

# 检查时间覆盖
if timestamp_lines:
    last_timestamp = timestamp_lines[-1]
    match = re.search(r'(\d{2}):(\d{2}):(\d{2})', last_timestamp)
    if match:
        end_minute = int(match.group(1)) * 60 + int(match.group(2))
        end_second = int(match.group(3))
        print(f"\n最后时间戳：{last_timestamp}")
        print(f"覆盖时长：{end_minute}分{end_second}秒")
