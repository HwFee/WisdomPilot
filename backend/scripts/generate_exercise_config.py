"""
生成题目配置文件 - 每道题覆盖多个知识点，每小节不超过10道题
"""
import sqlite3
import json
import os

conn = sqlite3.connect('../data.db')
cursor = conn.cursor()

# 获取所有章节
cursor.execute('SELECT id, title FROM chapters ORDER BY id')
chapters = cursor.fetchall()

config_dir = '../../习题生成配置'
os.makedirs(config_dir, exist_ok=True)

total_exercises = 0
total_kps = 0

for chapter in chapters:
    chapter_id, chapter_title = chapter

    # 获取该章节下的所有小节
    cursor.execute('SELECT id, title FROM sections WHERE chapter_id = ? ORDER BY order_index', (chapter_id,))
    sections = cursor.fetchall()

    for section in sections:
        section_id, section_title = section

        # 获取该小节下的所有知识点
        cursor.execute('SELECT id, name FROM section_knowledge_points WHERE section_id = ? ORDER BY order_index', (section_id,))
        knowledge_points = cursor.fetchall()

        if not knowledge_points:
            continue

        total_kps += len(knowledge_points)

        # 生成题目配置
        # 策略：将知识点分组，每道题覆盖1-3个相关知识点
        exercises = []
        kp_list = list(knowledge_points)

        # 计算需要多少道题
        # 目标：每小节不超过10道题，每个知识点至少被覆盖2次
        num_kps = len(kp_list)

        if num_kps <= 3:
            # 3个及以下知识点：每道题覆盖1个知识点，共 num_kps * 2 道
            # 但合并为 num_kps 道题，每道覆盖1个知识点，做2次
            for i, (kp_id, kp_name) in enumerate(kp_list):
                exercises.append({
                    'exercise_number': i + 1,
                    'knowledge_points': [kp_id],
                    'knowledge_point_names': [kp_name],
                    'description': f'考察知识点：{kp_name}',
                    'bkt_params': {
                        'p_l0': 0.30,
                        'p_t': 0.15,
                        'p_g': 0.20,
                        'p_s': 0.05
                    }
                })
        elif num_kps <= 6:
            # 4-6个知识点：分2-3组，每组2个知识点
            group_size = 2
            ex_num = 1
            for i in range(0, num_kps, group_size):
                group = kp_list[i:i+group_size]
                kp_ids = [g[0] for g in group]
                kp_names = [g[1] for g in group]
                exercises.append({
                    'exercise_number': ex_num,
                    'knowledge_points': kp_ids,
                    'knowledge_point_names': kp_names,
                    'description': f'考察知识点：{"、".join(kp_names)}',
                    'bkt_params': {
                        'p_l0': 0.30,
                        'p_t': 0.15,
                        'p_g': 0.20,
                        'p_s': 0.05
                    }
                })
                ex_num += 1
            # 再加一轮确保每个知识点被覆盖2次
            for i in range(0, num_kps, group_size):
                group = kp_list[i:i+group_size]
                kp_ids = [g[0] for g in group]
                kp_names = [g[1] for g in group]
                exercises.append({
                    'exercise_number': ex_num,
                    'knowledge_points': kp_ids,
                    'knowledge_point_names': kp_names,
                    'description': f'考察知识点：{"、".join(kp_names)}（进阶）',
                    'bkt_params': {
                        'p_l0': 0.30,
                        'p_t': 0.15,
                        'p_g': 0.20,
                        'p_s': 0.05
                    }
                })
                ex_num += 1
        else:
            # 7个及以上知识点：分3组，每道题覆盖2-3个知识点
            # 确保覆盖次数：第一轮分组，第二轮错位分组
            group_size = 3

            # 第一轮
            ex_num = 1
            for i in range(0, num_kps, group_size):
                group = kp_list[i:i+group_size]
                kp_ids = [g[0] for g in group]
                kp_names = [g[1] for g in group]
                exercises.append({
                    'exercise_number': ex_num,
                    'knowledge_points': kp_ids,
                    'knowledge_point_names': kp_names,
                    'description': f'考察知识点：{"、".join(kp_names)}',
                    'bkt_params': {
                        'p_l0': 0.30,
                        'p_t': 0.15,
                        'p_g': 0.20,
                        'p_s': 0.05
                    }
                })
                ex_num += 1

            # 第二轮：错位分组确保覆盖
            # 从中间位置开始
            offset = group_size // 2 + 1
            for i in range(0, num_kps, group_size):
                start = (i + offset) % num_kps
                end = start + group_size
                if end <= num_kps:
                    group = kp_list[start:end]
                else:
                    # 循环取
                    indices = list(range(start, num_kps)) + list(range(0, end - num_kps))
                    group = [kp_list[j] for j in indices]

                kp_ids = [g[0] for g in group]
                kp_names = [g[1] for g in group]
                exercises.append({
                    'exercise_number': ex_num,
                    'knowledge_points': kp_ids,
                    'knowledge_point_names': kp_names,
                    'description': f'考察知识点：{"、".join(kp_names)}（进阶）',
                    'bkt_params': {
                        'p_l0': 0.30,
                        'p_t': 0.15,
                        'p_g': 0.20,
                        'p_s': 0.05
                    }
                })
                ex_num += 1

        # 限制最多10道题
        exercises = exercises[:10]

        # 统计每个知识点被覆盖次数
        kp_coverage = {}
        for ex in exercises:
            for kp_id in ex['knowledge_points']:
                kp_coverage[kp_id] = kp_coverage.get(kp_id, 0) + 1

        total_exercises += len(exercises)

        # 生成配置
        config = {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'section_id': section_id,
            'section_title': section_title,
            'total_knowledge_points': num_kps,
            'total_exercises': len(exercises),
            'knowledge_point_coverage': {str(k): v for k, v in kp_coverage.items()},
            'knowledge_points': [
                {'id': kp[0], 'name': kp[1]} for kp in kp_list
            ],
            'exercises': exercises
        }

        # 保存配置文件
        filename = f'第{chapter_id}章第{section_id}节_{section_title}.json'
        filepath = os.path.join(config_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f'{filename}: {num_kps}个知识点, {len(exercises)}道题')

conn.close()
print()
print(f'完成! 总计: {total_kps}个知识点, {total_exercises}道题')
