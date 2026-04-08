import re

# 读取文件
with open('01.Jpn&furigana.srt', 'r', encoding='utf-8') as f:
    content = f.read()

# 分割成行
lines = content.split('\n')

# 解析字幕片段
segments = []
i = 0
while i < len(lines):
    # 跳过空行
    if not lines[i].strip():
        i += 1
        continue
    
    # 检查是否是序号行
    if re.match(r'^\d+$', lines[i].strip()):
        segment_num = int(lines[i].strip())
        # 检查下一行是否是时间轴
        if i + 1 < len(lines) and re.match(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', lines[i + 1]):
            # 收集这个片段的所有文本行
            text_lines = []
            j = i + 2
            while j < len(lines) and lines[j].strip() and not re.match(r'^\d+$', lines[j].strip()):
                text_lines.append(lines[j])
                j += 1
            
            segments.append({
                'num': segment_num,
                'time': lines[i + 1],
                'text': text_lines,
                'start_line': i
            })
            i = j
        else:
            i += 1
    else:
        i += 1

# 删除前 7 个片段
segments_to_keep = segments[7:]

# 重新编号
for idx, segment in enumerate(segments_to_keep, start=1):
    segment['num'] = idx

# 重建文件内容
new_lines = []
for idx, segment in enumerate(segments_to_keep):
    if idx > 0:
        new_lines.append('')  # 片段之间加空行
    new_lines.append(str(segment['num']))
    new_lines.append(segment['time'])
    new_lines.extend(segment['text'])

# 写入文件
with open('01.Jpn&furigana.srt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f'已删除前 7 个片段，剩余 {len(segments_to_keep)} 个片段')
print(f'新的片段序号范围：1-{len(segments_to_keep)}')
