"""清理参考字幕文件，删除假名注音和制作人员名单，只保留对话和旁白"""
import re
from pathlib import Path

def is_dialogue_or_narration(text: str) -> bool:
    """
    判断文本是否为对话或旁白（而非注音或制作人员信息）
    
    对话/旁白的特征：
    1. 完整的句子结构
    2. 包含助词（は、が、を、に、で、等）
    3. 长度适中（通常>4 个字符）
    4. 不是单个词语
    """
    text = text.strip()
    
    if not text:
        return False
    
    # 排除明显的制作人员信息
    staff_keywords = [
        '校对', '时间轴', '压制', '负责人', '注音', '字幕', '翻译', '听译', '特效',
        '制作', '总监', '策划', '监督', '导演', '脚本', '原画', '动画', '摄影',
        '美术', '音乐', '音响', '录音', '编辑', '出品', '发行', '版权所有'
    ]
    
    for keyword in staff_keywords:
        if keyword in text:
            return False
    
    # 排除纯假名短词（通常是注音）
    # 统计字符类型
    kanji_count = 0
    kana_count = 0
    other_count = 0
    
    for char in text:
        char_code = ord(char)
        # 汉字
        if 0x4E00 <= char_code <= 0x9FFF:
            kanji_count += 1
        # 平假名
        elif 0x3040 <= char_code <= 0x309F:
            kana_count += 1
        # 片假名
        elif 0x30A0 <= char_code <= 0x30FF:
            kana_count += 1
        # 标点、数字、拉丁字母等
        else:
            other_count += 1
    
    # 判断规则
    
    # 1. 包含汉字且长度>3，很可能是完整句子
    if kanji_count >= 1 and len(text) > 3:
        # 检查是否包含常见助词或句末助词
        common_particles = ['は', 'が', 'を', 'に', 'で', 'と', 'も', 'の', 'て', 'ね', 'よ', 'な', 'か', 'も', 'から', 'まで', 'って', 'だ', 'です', 'ます', 'た', 'だ', 'る', 'う', 'く', 'ぐ', 'す', 'ず', 'つ', 'づ', 'ぬ', 'ふ', 'ぶ', 'ぷ', 'む', 'ゆ', 'ら', 'り', 'る', 'れ', 'ろ']
        for particle in common_particles:
            if particle in text:
                return True
        
        # 或者长度>6
        if len(text) > 6:
            return True
    
    # 2. 纯假名但长度>8，且包含标点
    if kana_count > 8 and other_count >= 1:
        return True
    
    # 3. 包含英文字母和数字的专有名词
    if (any(c.isalpha() for c in text) or any(c.isdigit() for c in text)) and len(text) > 4:
        return True
    
    return False

def clean_reference_subtitle(input_path: str, output_path: str):
    """
    清理参考字幕文件，删除假名注音和制作人员名单，只保留对话和旁白
    
    Args:
        input_path: 输入字幕文件路径
        output_path: 输出清理后的字幕文件路径
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    cleaned_blocks = []
    removed_count = 0
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            removed_count += 1
            continue
        
        try:
            # 解析字幕块
            index = int(lines[0])
            timestamp_line = lines[1]
            text_lines = lines[2:]
            
            # 合并所有文本行
            full_text = '\n'.join(text_lines)
            
            # 检查是否为对话或旁白
            if not is_dialogue_or_narration(full_text):
                removed_count += 1
                continue
            
            # 保留这个字幕块
            cleaned_block = f"{len(cleaned_blocks) + 1}\n{timestamp_line}\n{full_text}"
            cleaned_blocks.append(cleaned_block)
            
        except Exception as e:
            print(f"解析字幕块失败：{e}")
            removed_count += 1
            continue
    
    # 写入清理后的文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(cleaned_blocks))
    
    print(f"清理完成！")
    print(f"原始片段数：{len(blocks)}")
    print(f"清理后片段数：{len(cleaned_blocks)}")
    print(f"删除片段数：{removed_count}")
    print(f"输出文件：{output_path}")

if __name__ == "__main__":
    input_file = r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt"
    output_file = r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.cleaned.srt"
    
    clean_reference_subtitle(input_file, output_file)
