"""
数据库迁移脚本：添加段位系统字段到 user_arena_profiles 表

运行方法：
    cd backend
    python scripts/migrate_add_tier_fields.py
"""

import sqlite3
import os
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data.db')


def migrate():
    """执行迁移"""
    print("=" * 50)
    print("段位系统字段迁移脚本")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_arena_profiles'")
    if not cursor.fetchone():
        print("[ERROR] user_arena_profiles 表不存在")
        conn.close()
        return False

    print("[OK] user_arena_profiles 表存在")

    # 2. 获取现有列
    cursor.execute("PRAGMA table_info(user_arena_profiles)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"   现有列: {existing_columns}")

    # 3. 定义要添加的新列
    new_columns = [
        ("sub_tier", "INTEGER DEFAULT 4", "小段位 (1=I, 2=II, 3=III, 4=IV, 5=V)"),
        ("stars", "INTEGER DEFAULT 0", "当前星星数"),
        ("protection_remaining", "INTEGER DEFAULT 3", "剩余段位保护次数"),
        ("highest_tier", "VARCHAR(20) DEFAULT NULL", "历史最高段位"),
        ("highest_sub_tier", "INTEGER DEFAULT NULL", "历史最高小段位"),
    ]

    # 4. 添加新列
    added = []
    skipped = []

    for col_name, col_type, col_comment in new_columns:
        if col_name in existing_columns:
            skipped.append(col_name)
            print(f"   [SKIP] 列 {col_name} 已存在，跳过")
        else:
            try:
                sql = f"ALTER TABLE user_arena_profiles ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                added.append(col_name)
                print(f"   [ADD] 添加列 {col_name} ({col_comment})")
            except sqlite3.OperationalError as e:
                print(f"   [FAIL] 添加列 {col_name} 失败: {e}")

    # 5. 提交更改
    conn.commit()

    # 6. 验证迁移结果
    print("\n" + "=" * 50)
    print("迁移结果验证")
    print("=" * 50)

    cursor.execute("PRAGMA table_info(user_arena_profiles)")
    final_columns = {row[1] for row in cursor.fetchall()}

    all_present = True
    for col_name, _, _ in new_columns:
        if col_name in final_columns:
            print(f"   [OK] {col_name}: 已添加")
        else:
            print(f"   [FAIL] {col_name}: 缺失")
            all_present = False

    # 7. 统计数据
    cursor.execute("SELECT COUNT(*) FROM user_arena_profiles")
    profile_count = cursor.fetchone()[0]
    print(f"\n   user_arena_profiles 记录数: {profile_count}")

    conn.close()

    print("\n" + "=" * 50)
    if all_present:
        print("[SUCCESS] 迁移成功完成！")
    else:
        print("[WARNING] 迁移完成，但部分列缺失")
    print("=" * 50)

    return all_present


if __name__ == "__main__":
    migrate()
