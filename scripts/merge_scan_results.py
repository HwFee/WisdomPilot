#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

with open('docs/superpowers/plans/python-issues.json', 'r', encoding='utf-8') as f:
    py = json.load(f)
with open('docs/superpowers/plans/ts-issues.json', 'r', encoding='utf-8') as f:
    ts = json.load(f)

merged = {
    'scan_date': '2026-06-10',
    'backend': {
        'total_files_scanned': len(set(i['file'] for i in py['issues'])),
        'total_issues': py['total_issues'],
        'summary': py['summary'],
    },
    'frontend': {
        'total_files_scanned': len(set(i['file'] for i in ts['issues'])),
        'total_issues': ts['total_issues'],
        'summary': ts['summary'],
    },
    'combined': {
        'total_issues': py['total_issues'] + ts['total_issues'],
        'critical': py['summary']['crit'] + ts['summary']['crit'],
        'warning': py['summary']['warn'] + ts['summary']['warn'],
    },
}

crit_files = Counter()
for i in py['issues'] + ts['issues']:
    if i['severity'] == 'crit':
        crit_files[i['file']] += 1

merged['top_critical_files'] = [
    {'file': f, 'critical_issues': c}
    for f, c in crit_files.most_common(20)
]

out_path = Path('docs/superpowers/plans/refactor-agents-compliance-issues.md')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('# 重构问题清单\n\n')
    f.write('> 由 scan_python_structure.py + scan_ts_structure.py 自动生成\n\n')
    f.write('## 汇总\n\n')
    f.write(f"- **Backend** (backend/): {py['total_issues']} 个问题，{merged['backend']['total_files_scanned']} 个文件\n")
    f.write(f"- **Frontend** (frontend/): {ts['total_issues']} 个问题，{merged['frontend']['total_files_scanned']} 个文件\n")
    f.write(f"- **合计**: {merged['combined']['total_issues']} 个问题\n")
    f.write(f"  - Critical: {merged['combined']['critical']}\n")
    f.write(f"  - Warning: {merged['combined']['warning']}\n\n")
    f.write('## 最严重文件（Critical 问题数 Top 20）\n\n')
    f.write('| 文件 | Critical 问题数 |\n')
    f.write('|------|----------------|\n')
    for item in merged['top_critical_files']:
        fname = item['file'].replace(str(Path.cwd()), '').replace('\\', '/').lstrip('/')
        f.write(f"| `{fname}` | {item['critical_issues']} |\n")
    f.write('\n')
    f.write('## 详细数据\n\n')
    f.write('- 原始 Backend 扫描结果: docs/superpowers/plans/python-issues.json\n')
    f.write('- 原始 Frontend 扫描结果: docs/superpowers/plans/ts-issues.json\n')

print(f'Issue list written to {out_path}')
print(f"Combined: {merged['combined']['total_issues']} issues, {merged['combined']['critical']} critical")
