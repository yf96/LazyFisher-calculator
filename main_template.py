import tkinter as tk
from tkinter import ttk, font
import json, math

# ========== CONSTANTS ==========
FONT_SIZE = 13  # 统一字体大小
COLORS = {
    'bg': '#f4f6f9',
    'card': '#ffffff',
    'accent': '#2d6aa0',
    'accent2': '#1e3a5f',
    'text': '#1a2332',
    'text2': '#5f6b7a',
    'text3': '#8895a6',
    'border': '#e1e5eb',
    'thead': '#eef2f7',
    'warn': '#c62828',
    'hover': '#f7f9fc',
}

# ========== EMBEDDED DATA ==========
# Generated from 数据库/渔场数据库.json and 数据库/tackle.json

REGIONS = __REGIONS_PLACEHOLDER__
HOOKS = __HOOKS_PLACEHOLDER__
LURES = __LURES_PLACEHOLDER__
BAITS = __BAITS_PLACEHOLDER__

# ========== FORMULAS ==========
import math

def gauss(x, mu, sigma):
    if sigma == 0:
        return 1.0 if x == mu else 0.0
    return math.exp(-(x - mu) ** 2 / sigma ** 2)

def hook_match(mouth, size, rod_type):
    gh = max((20 - size) / 2, 0)
    if rod_type == 'lure':
        target = 1.1
    elif rod_type == 'iso':
        target = 1.05
    else:
        target = 0.9
    raw = math.exp(-(gh - target * mouth) ** 2 / 4)
    return min(1.0, raw * 0.75)

def lure_match(size, mouth):
    r = size / mouth
    if r >= 1:
        return min(1.0, math.exp(-2.5 * (r - 1)))
    return min(1.0, max(r, 0.35))

def line_depth(d, fish_layer, rod_type):
    dd = d * 100
    if fish_layer == 'surface':
        lo, hi = 0, round(dd * 0.2)
    elif fish_layer == 'mid':
        lo, hi = round(dd * 0.2), round(dd * 0.6)
    else:
        lo, hi = round(dd * 0.6), dd
    if rod_type in ('bottom', 'lure'):
        return None
    return (lo, hi)

LURE_ACTIONS = {
    'topwater': ('浅层匀速', '1.70m/s'),
    'spoon': ('中层匀速', '1.28m/s'),
    'crank': ('中层匀速', '1.16m/s'),
    'jig': ('底层跳动', '0.64m/s'),
    'minnow': ('中层抽动', '1.38m/s'),
    'softbait': ('底层跳动', '0.64m/s'),
}

def get_lure_action(lure_type, fish_layer):
    if lure_type not in LURE_ACTIONS:
        return ('-', '-', True)
    act, spd = LURE_ACTIONS[lure_type]
    ok = not (
        (lure_type == 'topwater' and fish_layer != 'surface') or
        (lure_type in ('jig', 'softbait') and fish_layer != 'deep')
    )
    return (act, spd, ok)

def select_best_bait(bait_type, mouth, lvl):
    best, bs = None, -1
    for b in BAITS:
        if b['t'] != bait_type or b['lv'] > lvl:
            continue
        sc = math.exp(-(b['s'] - mouth) ** 2 / 6.25)
        if sc > bs:
            bs = sc
            best = b
    if best:
        return (best['n'], min(bs, 1.0))
    # fallback to first matching bait
    for b in BAITS:
        if b['t'] == bait_type and b['lv'] <= lvl:
            return (b['n'], 0)
    return (bait_type, 0)

ROD_CN = {'lure': '路亚', 'bottom': '底钓', 'iso': '矶竿', 'match': '赛竿'}
ROD_REV = {'路亚': 'lure', '底钓': 'bottom', '矶竿': 'iso', '赛竿': 'match'}
TYPE_CN = {'船钓': '船钓', '岸钓': '岸钓', '自有船': '自有船'}
LAYER_CN = {'surface': '表层', 'mid': '中层', 'deep': '底层'}

# ========== GUI ==========
class CalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("LazyFisher 钓鱼计算器")
        root.geometry("800x800")
        root.resizable(False, False)
        root.configure(bg=COLORS['bg'])

        # Top bar
        bar = tk.Frame(root, bg=COLORS['card'], height=42)
        bar.pack(fill='x', padx=0, pady=(0,1))
        bar.pack_propagate(False)

        tk.Label(bar, text="🐟", font=('', 12), bg=COLORS['card']).pack(side='left', padx=(12,3))
        self.fish_var = tk.StringVar()
        self.fish_entry = tk.Entry(bar, textvariable=self.fish_var, font=('Microsoft YaHei', FONT_SIZE),
                                    width=16, relief='solid', bd=1, bg='white')
        self.fish_entry.pack(side='left', padx=3, pady=5)
        self.fish_var.trace('w', lambda *a: self.on_input())

        tk.Label(bar, text="🎣", font=('', FONT_SIZE), bg=COLORS['card'], fg=COLORS['text2']).pack(side='left', padx=(12,3))
        self.rod_var = tk.StringVar(value='路亚')
        rod_cb = ttk.Combobox(bar, textvariable=self.rod_var, values=['路亚','底钓','矶竿','赛竿'],
                               state='readonly', width=6, font=('Microsoft YaHei', FONT_SIZE))
        rod_cb.pack(side='left', padx=3)
        rod_cb.bind('<<ComboboxSelected>>', lambda e: self.on_input())

        tk.Label(bar, text="⭐", font=('', FONT_SIZE), bg=COLORS['card'], fg=COLORS['text2']).pack(side='left', padx=(12,3))
        self.lvl_var = tk.StringVar(value='200')
        lvl_entry = tk.Entry(bar, textvariable=self.lvl_var, font=('Microsoft YaHei', FONT_SIZE),
                              width=5, relief='solid', bd=1, justify='center')
        lvl_entry.pack(side='left', padx=3)
        self.lvl_var.trace('w', lambda *a: self.on_input())

        # Results area
        self.canvas = tk.Canvas(root, bg=COLORS['bg'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # 滚动条已删除，用户使用滚轮滚动

        self.res_frame = tk.Frame(self.canvas, bg=COLORS['bg'])
        self.canvas.create_window((0,0), window=self.res_frame, anchor='nw', tags='res')

        self.res_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)

        self.match_list = None
        self.show_empty()

    def on_canvas_resize(self, event):
        self.canvas.itemconfig('res', width=event.width)

    def on_mousewheel(self, event):
        bbox = self.canvas.bbox('all')
        if not bbox:
            return
        _, _, _, content_bottom = bbox
        if content_bottom <= self.canvas.winfo_height():
            return  # 内容不溢出，不滚动
        self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

    def _make_entry(self, parent, text, fg, bg):
        """创建只读 Entry，点击自动全选并复制到剪贴板"""
        var = tk.StringVar(value=text)
        e = tk.Entry(parent, textvariable=var, font=('Microsoft YaHei', FONT_SIZE),
                     fg=fg, bg=bg, relief='flat', readonlybackground=bg,
                     state='readonly', width=0, justify='center')
        def on_click(event):
            e.select_range(0, 'end')
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._show_toast('已复制')
        e.bind('<Button-1>', on_click)
        return e

    def _show_toast(self, text):
        """屏幕正中显示半秒提示"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.configure(bg=COLORS['accent2'])
        tk.Label(toast, text=text, font=('Microsoft YaHei', FONT_SIZE),
                 bg=COLORS['accent2'], fg='#ffffff', padx=24, pady=10).pack()
        toast.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - toast.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - toast.winfo_height()) // 2
        toast.geometry(f'+{x}+{y}')
        self.root.after(500, toast.destroy)

    def get_rod(self):
        return ROD_REV.get(self.rod_var.get(), 'lure')

    def get_lvl(self):
        v = self.lvl_var.get().strip()
        if not v: return 200
        try: return max(1, min(int(v), 200))
        except: return 1

    def show_empty(self):
        for w in self.res_frame.winfo_children():
            w.destroy()
        tk.Label(self.res_frame, text="🐟", font=('', 24), bg=COLORS['bg'], fg=COLORS['text2']).pack(pady=(60,8))
        tk.Label(self.res_frame, text="输入鱼名开始查询", font=('Microsoft YaHei', FONT_SIZE),
                 bg=COLORS['bg'], fg=COLORS['text2']).pack()

    def on_input(self):
        q = self.fish_var.get().strip()
        self.hide_match_list()
        if not q:
            self.show_empty()
            return
        fish_names = sorted(set(
            fn for reg in REGIONS.values()
            for fn in reg['f'] if q in fn or fn in q
        ))
        if not fish_names:
            self.show_empty()
            return
        if len(fish_names) > 1 and q not in fish_names:
            self.show_match_list(fish_names)
        self.show_results(fish_names)

    def show_match_list(self, names):
        self.hide_match_list()
        self.match_list = tk.Toplevel(self.root)
        self.match_list.title("")
        self.match_list.attributes("-topmost", True)
        self.match_list.overrideredirect(True)
        self.match_list.configure(bg=COLORS['border'])

        # 左上角对齐输入框左下角，宽度跟随输入框
        x = self.fish_entry.winfo_rootx()
        y = self.fish_entry.winfo_rooty() + self.fish_entry.winfo_height()
        w = self.fish_entry.winfo_width()
        item_count = min(len(names), 12)
        self.match_list.geometry(f"{w}x{item_count * 32 + 2}+{x}+{y}")
        # 跟随主窗口移动
        self._move_id = self.root.bind('<Configure>', self._on_root_move, add='+')

        # 全局点击监听：点击 match_list 外部 → 关闭；内部 → 不关
        self._ml = self.match_list  # 保存引用供闭包使用
        def on_global_click(event):
            ml = self._ml
            if ml is None:
                return
            wgt = event.widget
            while wgt is not None:
                if wgt is ml:
                    return  # 在 match_list 内部，不关闭
                try:
                    wgt = wgt.master
                except Exception:
                    break
            # 点击了外部 → 关闭
            self.hide_match_list()
        self._bind_all_id = self.root.bind_all('<Button-1>', on_global_click, add='+')

        inner = tk.Frame(self.match_list, bg=COLORS['card'])
        inner.pack(fill='both', expand=True, padx=3, pady=3)
        lb = tk.Listbox(inner, font=('Microsoft YaHei', FONT_SIZE), bg=COLORS['card'],
                         selectbackground='#e0e8f0', relief='flat', bd=0, highlightthickness=0,
                         activestyle='none')
        lb.pack(fill='both', expand=True)
        for n in names[:12]:
            lb.insert('end', n)
        lb.bind('<<ListboxSelect>>', lambda e: self.select_from_list(lb, names))

    def _update_match_pos(self):
        if self.match_list:
            x = self.fish_entry.winfo_rootx()
            y = self.fish_entry.winfo_rooty() + self.fish_entry.winfo_height()
            self.match_list.geometry(f"+{x}+{y}")

    def _on_root_move(self, event):
        self._update_match_pos()

    def select_from_list(self, lb, names):
        sel = lb.curselection()
        if sel:
            self.hide_match_list()
            self.fish_var.set(names[sel[0]])
            self.on_input()

    def hide_match_list(self):
        # 解绑全局点击
        if hasattr(self, '_bind_all_id') and self._bind_all_id:
            self.root.unbind_all(self._bind_all_id)
            self._bind_all_id = None
        if hasattr(self, '_move_id') and self._move_id:
            self.root.unbind('<Configure>', self._move_id)
            self._move_id = None
        self._ml = None
        if self.match_list:
            self.match_list.destroy()
            self.match_list = None

    def show_results(self, fish_names):
        rod = self.get_rod()
        lvl = self.get_lvl()
        for w in self.res_frame.winfo_children():
            w.destroy()

        all_r = []
        for fn in fish_names:
            rfs = [(reg, reg["f"][fn]) for rid, reg in REGIONS.items() if fn in reg["f"]]
            if rfs:
                all_r.append((fn, rfs))

        if not all_r:
            self.show_empty()
            return

        total = sum(len(r[1]) for r in all_r)
        summary = f"{len(fish_names)}条鱼 · {total}渔场 · {ROD_CN[rod]} · Lv≤{lvl}"
        tk.Label(self.res_frame, text=summary, font=('Microsoft YaHei', FONT_SIZE),
                 bg=COLORS['bg'], fg=COLORS['text2'], anchor='w').pack(fill='x', padx=10, pady=(8,4))

        # 固定列宽 & 间距（grid 布局）
        COL_W = [180, 170, 160, 170]
        COL_HDR = ['渔场', '拟饵' if rod == 'lure' else '真饵', '鱼钩', '装备参数']
        COL_GAP = 40

        mk = self._make_entry  # 快捷引用

        for fn, regions in all_r:
            if len(all_r) > 1:
                tk.Label(self.res_frame, text=fn, font=('Microsoft YaHei', FONT_SIZE, 'bold'),
                         bg=COLORS['bg'], fg=COLORS['accent'], anchor='w').pack(fill='x', padx=10, pady=(10,4))

            card = tk.Frame(self.res_frame, bg=COLORS['bg'])
            card.pack(fill='x', padx=8, pady=1)
            for i, w in enumerate(COL_W):
                card.grid_columnconfigure(i, minsize=w, weight=1)

            # Header row 0
            hdr = tk.Frame(card, bg=COLORS['thead'])
            hdr.grid(row=0, column=0, columnspan=4, sticky='ew')
            for i, w in enumerate(COL_W):
                hdr.grid_columnconfigure(i, minsize=w, weight=1)
            for i, label in enumerate(COL_HDR):
                gap = (0, COL_GAP) if i < 3 else (0, 0)
                tk.Label(hdr, text=label, font=('Microsoft YaHei', FONT_SIZE, 'bold'),
                         bg=COLORS['thead'], fg='#384860', anchor='center')\
                  .grid(row=0, column=i, sticky='ew', padx=gap, pady=2)

            # Data rows — 每列统一 3 行 Entry
            row_idx = 1
            for reg, fish in regions:
                bg = COLORS['bg']
                gap = (0, COL_GAP)
                tg = COLORS['text']   # 黑色
                t3 = COLORS['text3']  # 灰色
                t2 = COLORS['text2']  # 中灰
                wr = COLORS['warn']   # 红色

                # === Col1: 渔场 (3行) ===
                c1 = tk.Frame(card, bg=bg)
                c1.grid(row=row_idx, column=0, sticky='nsew', padx=gap, pady=3)
                mk(c1, reg['n'], tg, bg).pack(fill='x')
                mk(c1, f"Lv.{reg['lv']} · {TYPE_CN.get(reg['t'], reg['t'])}", t3, bg).pack(fill='x')
                # Row3: 自有船显示出现率，其余留空
                if reg.get('t') == '自有船' and fish.get('ar') is not None:
                    mk(c1, f"出现率 {fish['ar']}%", t3, bg).pack(fill='x')
                else:
                    mk(c1, '', t3, bg).pack(fill='x')

                # === Col2: 饵 (3行) ===
                c2 = tk.Frame(card, bg=bg)
                c2.grid(row=row_idx, column=1, sticky='nsew', padx=gap, pady=3)
                if rod == 'lure':
                    bl, bls = None, -1
                    for l in LURES:
                        if not l.get('s') or l.get('lv',1) > lvl: continue
                        sc = lure_match(l['s'], fish['m'])
                        if l['t'] == fish.get('u',''): sc *= 1.3
                        if sc > bls: bls, bl = sc, l
                    if bl:
                        parts = bl['n'].split(' · ', 1)
                        mk(c2, parts[0], tg, bg).pack(fill='x')
                        mk(c2, parts[1] if len(parts)>1 else '', tg, bg).pack(fill='x')
                        mk(c2, f"匹配 {min(bls*100,100):.0f}% · Lv.{bl['lv']}", t3, bg).pack(fill='x')
                    else:
                        mk(c2, '—', t2, bg).pack(fill='x')
                        mk(c2, '', tg, bg).pack(fill='x')
                        mk(c2, '', t3, bg).pack(fill='x')
                else:
                    bn, bs = select_best_bait(fish['b'], fish['m'], lvl)
                    # 真饵：找中文名
                    parts = bn.split(' · ', 1)
                    cn_name = parts[1] if len(parts)>1 else bn
                    # 找等级
                    b_lv = None
                    for b in BAITS:
                        if b['n'] == bn:
                            b_lv = b['lv'] if b.get('lv') else None
                            break
                    b_lv_str = f" · Lv.{b_lv}" if b_lv else ""
                    mk(c2, '', tg, bg).pack(fill='x')
                    mk(c2, cn_name, tg, bg).pack(fill='x')
                    mk(c2, f"匹配 {bs*100:.0f}%{b_lv_str}", t3, bg).pack(fill='x')

                # === Col3: 鱼钩 (3行) ===
                c3 = tk.Frame(card, bg=bg)
                c3.grid(row=row_idx, column=2, sticky='nsew', padx=gap, pady=3)
                bh, bhs = None, -1
                for h in HOOKS:
                    if h.get('s') is None or h.get('lv',1) > lvl: continue
                    sc = hook_match(fish['m'], h['s'], rod)
                    if h.get('t') == 'treble': sc *= 1.15
                    elif h.get('t') == 'double': sc *= 1.08
                    sc *= (100 - (h.get('v',50)) * 0.15) / 100
                    if sc > bhs: bhs, bh = sc, h
                if bh:
                    parts = bh['n'].split(' · ', 1)
                    h_lv = bh.get('lv') if bh.get('lv') else ''
                    mk(c3, parts[0], tg, bg).pack(fill='x')
                    mk(c3, parts[1] if len(parts)>1 else '', tg, bg).pack(fill='x')
                    mk(c3, f"匹配 {min(bhs*100,100):.0f}% · Lv.{h_lv}", t3, bg).pack(fill='x')
                else:
                    mk(c3, '—', t2, bg).pack(fill='x')
                    mk(c3, '', tg, bg).pack(fill='x')
                    mk(c3, '', t3, bg).pack(fill='x')

                # === Col4: 装备参数 (3行) ===
                c4 = tk.Frame(card, bg=bg)
                c4.grid(row=row_idx, column=3, sticky='nsew', pady=3)
                ld = line_depth(reg['d'], fish['l'], rod)
                if rod == 'lure' and bl:
                    act, spd, ok = get_lure_action(bl['t'], fish['l'])
                    speed_num = spd.replace('m/s', '') if spd else ''
                    mk(c4, act, tg if ok else wr, bg).pack(fill='x')
                    mk(c4, speed_num, tg, bg).pack(fill='x')
                    mk(c4, '⚠ 水层不匹配' if not ok else '', wr, bg).pack(fill='x')
                elif rod in ('iso','match') and ld:
                    mk(c4, '线深', tg, bg).pack(fill='x')
                    mk(c4, str(ld[0]+1), tg, bg).pack(fill='x')
                    mk(c4, str(ld[1]-100), tg, bg).pack(fill='x')
                else:
                    mk(c4, '—', t2, bg).pack(fill='x')
                    mk(c4, '—', t2, bg).pack(fill='x')
                    mk(c4, '—', t2, bg).pack(fill='x')

                row_idx += 1

        # 刷新 canvas 滚动区域，防止滚轮出现空白
        self.res_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

def main():
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
