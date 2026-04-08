"""清理参考字幕文件，删除假名注音片段（优化版）"""
import re
from pathlib import Path

def is_furigana_segment(text: str) -> bool:
    """判断文本是否为假名注音或制作信息等非主文本内容"""
    text = text.strip()
    
    if not text:
        return True
    
    # 1. 长度很短（1-2 个字符）的片段
    if len(text) <= 2:
        # 全是假名（平假名或片假名）
        if re.match(r'^[\u3040-\u309F\u30A0-\u30FF]+$', text):
            return True
        # 单个汉字（通常是注音）
        if len(text) == 1 and re.match(r'^[\u4E00-\u9FFF]$', text):
            return True
    
    # 2. 长度 3-4 个字符，主要是假名
    if len(text) <= 4:
        hiragana_katakana_count = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        if hiragana_katakana_count >= len(text) * 0.7:
            return True
    
    # 3. 检查是否包含常见制作信息关键词（这些应该保留）
   制作信息关键词 = ['校对', '时间轴', '压制', '负责人', '字幕', '注音']
    for keyword in 制作信息关键词:
        if keyword in text:
            return False
    
    # 4. 长度<=2 且包含汉字的短文本（可能是注音）
    if len(text) <= 2:
        kanji_count = len(re.findall(r'[\u4E00-\u9FFF]', text))
        if kanji_count > 0:
            return True
    
    return False

def clean_srt(input_path: str, output_path: str):
    """清理 SRT 文件，删除假名注音片段"""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    
    cleaned_blocks = []
    removed_count = 0
    kept_count = 0
    
    for i, block in enumerate(blocks):
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        try:
            index = int(lines[0])
            timestamp_line = lines[1]
            text = '\n'.join(lines[2:])
            
            # 检查是否为假名注音
            if is_furigana_segment(text):
                removed_count += 1
            else:
                kept_count += 1
                # 重新编号
                new_index = kept_count
                lines[0] = str(new_index)
                cleaned_blocks.append('\n'.join(lines))
                
        except Exception as e:
            print(f"解析片段失败：{e}")
            continue
    
    # 写入清理后的文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(cleaned_blocks))
        f.write('\n')
    
    print(f"\n清理完成!")
    print(f"原始片段数：{len(blocks)}")
    print(f"删除假名注音：{removed_count}")
    print(f"保留主文本：{kept_count}")
    print(f"输出文件：{output_path}")

def main():
    input_path = Path(r"d:\AI-dev\video-subtitle-generator\video\01.Jpn&furigana.srt")
    output_path = input_path.parent / "01.cleaned.srt"
    
    if not input_path.exists():
        print(f"错误：文件不存在：{input_path}")
        return
    
    print(f"处理文件：{input_path}")
    clean_srt(str(input_path), str(output_path))
    
    # 显示清理后的前 30 条作为示例
    print(f"\n清理后的前 30 条字幕预览:")
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    for i, block in enumerate(blocks[:30]):
        lines = block.split('\n')
        print(f"{lines[0]}. {lines[2][:60]}")

if __name__ == "__main__":
    main()
