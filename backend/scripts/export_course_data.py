"""
数据库导出脚本 - 将课程数据导出为JSON文件

运行方法：
    cd backend
    python scripts/export_course_data.py

导出的数据包括：
    - 课程 (courses)
    - 章节 (chapters)
    - 小节 (sections)
    - 练习题 (exercises) - 不含 embedding
    - 基础题目 (chapter_base_questions)
    - 关卡 (stages)
"""

import sqlite3
import json
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'seed_data')

# 要排除的字段（太大或不需要导出）
EXCLUDE_FIELDS = {
    'exercises': ['embedding'],  # embedding 字段太大，不导出
}


def export_table(cursor, table_name, order_by='id', exclude_fields=None):
    """导出单个表的数据"""
    exclude_fields = exclude_fields or []

    try:
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        all_columns = [row[1] for row in cursor.fetchall()]

        # 过滤要导出的列
        export_columns = [col for col in all_columns if col not in exclude_fields]
        columns_str = ', '.join(export_columns)

        cursor.execute(f"SELECT {columns_str} FROM {table_name} ORDER BY {order_by}")
        rows = cursor.fetchall()

        result = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(export_columns):
                value = row[i]
                # 处理 datetime 类型
                if isinstance(value, str) and 'T' in value:
                    try:
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                        row_dict[col] = value
                    except:
                        row_dict[col] = value
                else:
                    row_dict[col] = value
            result.append(row_dict)

        excluded_info = f" (排除: {exclude_fields})" if exclude_fields else ""
        print(f"  [{table_name}] 导出 {len(result)} 条记录{excluded_info}")
        return result
    except sqlite3.OperationalError as e:
        print(f"  [{table_name}] 表不存在或查询失败: {e}")
        return []


def export_all_data():
    """导出所有课程相关数据"""
    print("=" * 50)
    print("课程数据导出脚本")
    print("=" * 50)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 数据库文件不存在: {DB_PATH}")
        return False

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 定义要导出的表（按依赖顺序）
    tables_to_export = [
        ('courses', 'id', []),
        ('chapters', 'id', []),
        ('sections', 'id', []),
        ('exercises', 'id', EXCLUDE_FIELDS.get('exercises', [])),
        ('chapter_base_questions', 'id', []),
        ('stages', 'id', []),
    ]

    all_data = {}

    for table_name, order_by, exclude_fields in tables_to_export:
        data = export_table(cursor, table_name, order_by, exclude_fields)
        if data:
            all_data[table_name] = data

    conn.close()

    # 保存为单个合并文件
    output_file = os.path.join(OUTPUT_DIR, 'course_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 数据已导出到: {output_file}")

    # 同时保存为单独的文件（方便查看）
    for table_name, data in all_data.items():
        table_file = os.path.join(OUTPUT_DIR, f'{table_name}.json')
        with open(table_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] 各表数据已单独保存到: {OUTPUT_DIR}/")

    # 输出统计信息
    print("\n" + "=" * 50)
    print("导出统计")
    print("=" * 50)
    for table_name, data in all_data.items():
        print(f"  {table_name}: {len(data)} 条记录")

    return True


if __name__ == "__main__":
    export_all_data()
