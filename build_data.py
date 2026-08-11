import os, json, sys

app_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(app_dir, '数据库')

# Read region DB
with open(os.path.join(db_dir, '渔场数据库.json'), 'r', encoding='utf-8-sig') as f:
    regions = json.load(f)

# Read tackle
with open(os.path.join(db_dir, '装备数据库.json'), 'r', encoding='utf-8-sig') as f:
    tackle = json.load(f)

# recognition（识别度）为 0~1 值，缩放到 0~100 供公式使用
# single 平均 ≈0.32, double ≈0.37, treble ≈0.60（与帮助文档 §4.8 三本钩>双钩>单钩 一致）
def _hook_vis(h):
    recog = h.get('recognition')
    if recog is not None:
        return round(recog * 100, 1)
    # 极少数钩子可能缺失 recognition，按钩型给默认
    return {'treble': 60, 'double': 37, 'single': 32}.get(h.get('hook_type', 'single'), 32)
hooks = [{'n':h['name'],'s':h.get('size'),'t':h.get('hook_type','single'),'v':_hook_vis(h),'lv':h.get('level_required',1)} for h in tackle.get('hooks',[])]
lures = [{'n':l['name'],'s':l.get('size'),'t':l.get('lure_type'),'lv':l.get('level_required',1)} for l in tackle.get('lures',[])]
baits = [{'n':b['name'],'s':b.get('size',0),'t':b['bait_type'],'lv':b.get('level_required',1)} for b in tackle.get('baits',[])]

# Read template
with open(os.path.join(app_dir, 'main_template.py'), 'r', encoding='utf-8') as f:
    py = f.read()

# Replace placeholders
py = py.replace('__REGIONS_PLACEHOLDER__', json.dumps(regions, ensure_ascii=False))
py = py.replace('__HOOKS_PLACEHOLDER__', json.dumps(hooks, ensure_ascii=False))
py = py.replace('__LURES_PLACEHOLDER__', json.dumps(lures, ensure_ascii=False))
py = py.replace('__BAITS_PLACEHOLDER__', json.dumps(baits, ensure_ascii=False))

out_path = os.path.join(app_dir, 'main.py')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(py)

print(f'Wrote {out_path} ({len(py)} bytes)')
print(f'Regions: {len(regions)}, Hooks: {len(hooks)}, Lures: {len(lures)}, Baits: {len(baits)}')
