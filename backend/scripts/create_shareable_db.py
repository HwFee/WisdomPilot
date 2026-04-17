"""
创建精简版数据库 - 用于分享给团队

运行方法：
    cd backend
    python scripts/create_shareable_db.py

输出的数据库会排除：
    - exercises.embedding (7.66 MB)
    - exercises.test_cases (948 MB) - 这个太大了

这些字段会在用户运行时通过 AI 重新生成
"""

import sqlite3
import os
import shutil

# 路径配置
SOURCE_DB = os.path.join(os.path.dirname(__file__), '..', 'data.db')
OUTPUT_DB = os.path.join(os.path.dirname(__file__), '..', 'data_shareable.db')


def create_shareable_db():
    """创建精简版数据库"""
    print("=" * 50)
    print("创建精简版数据库")
    print("=" * 50)

    if not os.path.exists(SOURCE_DB):
        print(f"[ERROR] 源数据库不存在: {SOURCE_DB}")
        return False

    # 复制数据库
    print(f"\n正在复制数据库...")
    shutil.copy2(SOURCE_DB, OUTPUT_DB)

    # 打开复制的数据库，删除大字段
    print(f"正在清理大字段...")
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()

    # 清空 exercises 表的 embedding 和 test_cases 字段
    cursor.execute("UPDATE exercises SET embedding = NULL, test_cases = NULL")
    updated = cursor.rowcount
    print(f"  已清空 {updated} 条 exercises 记录的 embedding 和 test_cases")

    # 提交更改
    conn.commit()
    conn.close()

    # 执行 VACUUM 压缩数据库（需要在单独连接中执行）
    print("正在压缩数据库...")
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()
    cursor.execute("VACUUM")
    conn.close()

    # 检查结果
    source_size = os.path.getsize(SOURCE_DB) / 1024 / 1024
    output_size = os.path.getsize(OUTPUT_DB) / 1024 / 1024

    print("\n" + "=" * 50)
    print("完成")
    print("=" * 50)
    print(f"  原始数据库: {source_size:.2f} MB")
    print(f"  精简数据库: {output_size:.2f} MB")
    print(f"  节省空间: {source_size - output_size:.2f} MB ({(1 - output_size/source_size)*100:.1f}%)")
    print(f"\n  输出文件: {OUTPUT_DB}")

    return True


if __name__ == "__main__":
    create_shareable_db()
