import sqlite3
conn = sqlite3.connect('/app/data/data.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('=== 所有表 ===')
for t in tables:
    if t == 'sqlite_sequence':
        continue
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t}: {cursor.fetchone()[0]}")

print('\n=== 关键表 ===')
key_tables = ['users', 'user_stage_progress', 'chapter_progress', 'learning_sessions', 'knowledge_point_mastery', 'exercises', 'stages', 'chapters']
for t in key_tables:
    if t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {cursor.fetchone()[0]}")

print('\n=== 用户学习进度 ===')
try:
    cursor.execute("SELECT user_id, stage_id, status FROM user_stage_progress LIMIT 5")
    for r in cursor.fetchall():
        print(r)
except:
    print('user_stage_progress 表查询失败')

conn.close()
