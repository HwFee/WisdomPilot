"""
数据库迁移脚本：删除 level 字段，新增 mastery_xp 和 mastery_level 字段

运行方法：
    cd backend
    python scripts/migrate_mastery_xp.py
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
    print("精进之路 XP 字段迁移脚本")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("[ERROR] users 表不存在")
        conn.close()
        return False

    print("[OK] users 表存在")

    # 2. 获取现有列
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"   现有列: {existing_columns}")

    # 3. 添加新列
    new_columns = [
        ("mastery_xp", "INTEGER DEFAULT 0", "精进之路经验值"),
        ("mastery_level", "VARCHAR(20) DEFAULT '入门'", "精进等级"),
    ]

    added = []
    for col_name, col_type, col_comment in new_columns:
        if col_name in existing_columns:
            print(f"   [SKIP] 列 {col_name} 已存在，跳过")
        else:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                added.append(col_name)
                print(f"   [ADD] 添加列 {col_name} ({col_comment})")
            except sqlite3.OperationalError as e:
                print(f"   [FAIL] 添加列 {col_name} 失败: {e}")

    # 4. 删除 level 列 (SQLite 不支持 DROP COLUMN，需要重建表)
    # 注意：SQLite 3.35.0+ 支持 DROP COLUMN，但为了兼容性使用重建方式
    if 'level' in existing_columns:
        print("\n   [INFO] 删除 level 列需要重建表...")

        # 先添加新列（如果还没添加）
        for col_name, col_type, col_comment in new_columns:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"   [ADD] 添加列 {col_name} ({col_comment})")
                except sqlite3.OperationalError as e:
                    print(f"   [WARN] 添加列 {col_name} 时出错: {e}")

        # 重新获取列列表
        cursor.execute("PRAGMA table_info(users)")
        updated_columns = {row[1] for row in cursor.fetchall()}

        # 获取当前所有列（除了 level）
        columns_to_keep = [col for col in updated_columns if col != 'level']
        columns_str = ', '.join(columns_to_keep)

        # 创建临时表
        cursor.execute(f"""
            CREATE TABLE users_backup AS SELECT {columns_str} FROM users
        """)

        # 删除原表
        cursor.execute("DROP TABLE users")

        # 重命名临时表
        cursor.execute("ALTER TABLE users_backup RENAME TO users")

        # 重建索引（如果需要的话）
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)")
        except Exception as e:
            print(f"   [WARN] 重建索引时出错: {e}")

        print("   [OK] level 列已删除")

    # 5. 提交更改
    conn.commit()

    # 6. 验证迁移结果
    print("\n" + "=" * 50)
    print("迁移结果验证")
    print("=" * 50)

    cursor.execute("PRAGMA table_info(users)")
    final_columns = {row[1] for row in cursor.fetchall()}

    # 检查新列
    all_present = True
    for col_name, _, _ in new_columns:
        if col_name in final_columns:
            print(f"   [OK] {col_name}: 已添加")
        else:
            print(f"   [FAIL] {col_name}: 缺失")
            all_present = False

    # 检查 level 列已删除
    if 'level' not in final_columns:
        print("   [OK] level: 已删除")
    else:
        print("   [WARN] level: 仍然存在")
        all_present = False

    # 7. 统计数据
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"\n   users 记录数: {user_count}")

    conn.close()

    print("\n" + "=" * 50)
    if all_present:
        print("[SUCCESS] 迁移成功完成！")
    else:
        print("[WARNING] 迁移完成，但存在问题")
    print("=" * 50)

    return all_present


if __name__ == "__main__":
    migrate()
