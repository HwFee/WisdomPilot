"""修复选项格式：将 {key, text} 对象格式转换为简单字符串数组"""

import re

def convert_options(match):
    """将 [{"key": "A", "text": "xxx"}, ...] 转换为 ["xxx", ...]"""
    options_str = match.group(1)

    # 提取所有 text 值
    text_pattern = r'\{"key":\s*"[^"]*",\s*"text":\s*"([^"]*)"\}'
    texts = re.findall(text_pattern, options_str)

    if texts:
        # 构建新的字符串数组格式
        new_options = ', '.join(f'"{t}"' for t in texts)
        return f'"options": [{new_options}]'

    return match.group(0)  # 保持原样

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 "options": [...] 块
    pattern = r'"options":\s*\[(?:\{[^]]*\](?:\s*,\s*\{[^]]*\})*|\s*)\]'

    # 更精确的模式：匹配包含 {key, text} 的选项数组
    pattern = r'"options":\s*\[(\s*\{[^]]*\}(?:\s*,\s*\{[^]]*\})*\s*)\]'

    new_content = re.sub(pattern, convert_options, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # 统计修改数量
    old_count = len(re.findall(r'\{"key":', content))
    new_count = len(re.findall(r'\{"key":', new_content))

    print(f"处理完成: {filepath}")
    print(f"  原有对象格式选项: {old_count}")
    print(f"  剩余对象格式选项: {new_count}")
    print(f"  已转换: {old_count - new_count}")

if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "004_add_c_course_data.py"
    fix_file(filepath)
