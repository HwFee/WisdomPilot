"""
生成知识点汇总表
"""
import sqlite3
import json

conn = sqlite3.connect('../data.db')
cursor = conn.cursor()

# 获取所有章节、小节和知识点的完整数据
data = []

# 获取所有章节
cursor.execute('SELECT id, title FROM chapters ORDER BY id')
chapters = cursor.fetchall()

for chapter in chapters:
    chapter_id, chapter_title = chapter

    # 获取该章节下的所有小节
    cursor.execute('SELECT id, title FROM sections WHERE chapter_id = ? ORDER BY order_index', (chapter_id,))
    sections = cursor.fetchall()

    for section in sections:
        section_id, section_title = section

        # 获取该小节下的所有知识点
        cursor.execute('SELECT id, name, order_index FROM section_knowledge_points WHERE section_id = ? ORDER BY order_index', (section_id,))
        knowledge_points = cursor.fetchall()

        for kp in knowledge_points:
            kp_id, kp_name, kp_order = kp
            data.append({
                'chapter_id': chapter_id,
                'chapter_title': chapter_title,
                'section_id': section_id,
                'section_title': section_title,
                'knowledge_point_id': kp_id,
                'knowledge_point_name': kp_name,
                'knowledge_point_order': kp_order
            })

# 生成 Markdown 表格
md_content = '''# 知识点汇总表

数据来源：数据库 `section_knowledge_points` 表

## 按章节统计

| 章节 | 小节数 | 知识点数 |
|------|--------|----------|
'''

# 按章节统计
cursor.execute('''
    SELECT c.id, c.title, COUNT(DISTINCT s.id) as section_count, COUNT(kp.id) as kp_count
    FROM chapters c
    LEFT JOIN sections s ON s.chapter_id = c.id
    LEFT JOIN section_knowledge_points kp ON kp.section_id = s.id
    GROUP BY c.id
    ORDER BY c.id
''')
stats = cursor.fetchall()
total_sections = 0
total_kps = 0
for stat in stats:
    chapter_id, chapter_title, section_count, kp_count = stat
    total_sections += section_count
    total_kps += kp_count
    md_content += f'| 第{chapter_id}章 {chapter_title} | {section_count} | {kp_count} |\n'

md_content += f'| **合计** | **{total_sections}** | **{total_kps}** |\n'

md_content += '''
## 详细知识点列表

| 章节 | 小节 | 知识点ID | 知识点名称 |
|------|------|----------|------------|
'''

for item in data:
    md_content += f"| 第{item['chapter_id']}章 {item['chapter_title']} | {item['section_id']}. {item['section_title']} | {item['knowledge_point_id']} | {item['knowledge_point_name']} |\n"

# 写入文件
output_path = '../../知识点汇总表.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f'文件已保存到: {output_path}')
print()
print('第一章第1节(section_id=1)的知识点:')
for item in data:
    if item['section_id'] == 1:
        print(f"  - {item['knowledge_point_name']}")

conn.close()
