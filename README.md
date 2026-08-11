# 🎣 LazyFisher 钓鱼计算器

基于 Python tkinter 的桌面端钓鱼计算工具，输入鱼名 + 竿型，一键输出推荐装备方案。

## 快速开始

### 环境要求
- Python 3.8+
- PyInstaller

### 构建

```bash
# 1. 生成内嵌数据
python build_data.py

# 2. 打包为单文件 exe
python -m PyInstaller "LazyFisher计算器.spec"
```

产物在 `dist/LazyFisher计算器.exe`，可直接分发，无需 Python 环境。

### 开发调试

```bash
# 先生成 main.py（含数据），再直接运行
python build_data.py && python main.py
```

修改 UI 逻辑请编辑 `main_template.py`，不要直接改 `main.py`（它由 build_data.py 自动生成）。

---

## 数据库结构

项目依赖两个 JSON 数据库，位于 `../数据库/`（与 calculator-app 同级目录）。

### 1. 渔场数据库 (`数据库/渔场数据库.json`)

顶层是一个 JSON 对象，key 为渔场英文 ID，value 为渔场对象。

```json
{
  "pond_village": {
    "n": "青溪镇·村边鱼塘",
    "lv": 1,
    "t": "岸钓",
    "w": "淡水",
    "d": 1.6,
    "sk": 1,
    "f": {
      "小鲫鱼": {
        "r": "common",
        "l": "mid",
        "m": 1.6,
        "b": "worm",
        "u": "spoon",
        "s": 1
      }
    }
  }
}
```

#### 渔场字段

| 字段 | 含义 | 类型 | 说明 |
|------|------|------|------|
| `n` | 中文名称 | string | 如 `"青溪镇·村边鱼塘"` |
| `lv` | 等级要求 | int | 玩家达到该等级才能进入 |
| `t` | 钓法类型 | string | `"岸钓"` 或 `"船钓"` |
| `w` | 水域类型 | string | `"淡水"` 或 `"海水"` |
| `d` | 水深 | float | 单位：米 |
| `sk` | 技能经验 | int | 目标技能经验需求 |
| `f` | 鱼种列表 | object | key=鱼名，value=鱼属性 |

#### 鱼种字段 (`f` 下每条鱼)

| 字段 | 含义 | 类型 | 可选值 |
|------|------|------|--------|
| `r` | 稀有度 | string | `common` `uncommon` `rare` `epic` `legendary` |
| `l` | 活动水层 | string | `surface`（表层）`mid`（中层）`deep`（底层） |
| `m` | 鱼嘴大小 | float | 单位 cm，决定钩号匹配 |
| `b` | 最佳真饵类型 | string | 见下方真饵类型枚举 |
| `u` | 最佳拟饵类型 | string | 见下方拟饵类型枚举 |
| `s` | 体型系数 | float | 默认 1.0，影响鱼体重 |

**真饵类型枚举**: `worm` `small_fish` `shrimp` `shellfish` `snail` `corn` `algae_paste` `grass` `insect` `paste` `crab` `grain`

**拟饵类型枚举**: `spoon` `topwater` `minnow` `crank` `jig` `softbait`

### 2. 装备数据库 (`数据库/tackle.json`)

```json
{
  "hooks": [...],
  "lures": [...],
  "baits": [...]
}
```

#### 鱼钩 (`hooks`)

| 字段 | 含义 | 类型 | 说明 |
|------|------|------|------|
| `id` | 唯一 ID | string | |
| `name` | 名称 | string | 格式 `英文名 · 中文名` |
| `hook_type` | 钩型 | string | `single` `double` `treble` |
| `size` | 钩号 | int | 号数越小钩越大 |
| `max_tension` | 最大拉力 | int | 单位 kg |
| `snag_factor` | 挂底系数 | float | 0~1 |
| `recognition` | 识别度 | float | 0~1，三本钩>双钩>单钩 |
| `base_price` | 基础价格 | int | |
| `durability` | 耐久度 | int | |
| `level_required` | 等级需求 | int | 可选 |

#### 拟饵 (`lures`)

| 字段 | 含义 | 类型 | 说明 |
|------|------|------|------|
| `id` | 唯一 ID | string | |
| `name` | 名称 | string | 格式 `英文名 · 中文名` |
| `lure_type` | 拟饵类型 | string | `jig` `spoon` `minnow` `crank` `softbait` `topwater` |
| `size` | 尺寸 | float | |
| `weight_g` | 重量 | float | 单位 g |
| `turbulence` | 扰流值 | float | 0~1 |
| `reflectivity` | 反光度 | float | 0~1 |
| `sound` | 声响值 | float | 0~1 |
| `base_price` | 基础价格 | int | |
| `level_required` | 等级需求 | int | 可选 |

#### 真饵 (`baits`)

| 字段 | 含义 | 类型 | 说明 |
|------|------|------|------|
| `id` | 唯一 ID | string | |
| `name` | 名称 | string | 商店显示原名 |
| `bait_type` | 饵类型 | string | 见上方真饵类型枚举 |
| `size` | 饵球大小 | float | |
| `naturalness` | 自然度 | float | 0~1 |
| `base_price` | 基础价格 | int | |
| `level_required` | 等级需求 | int | 可选 |

---

## 数据扩容指南

### 添加新渔场

在 `渔场数据库.json` 顶层新增一个 key：

```json
"my_new_pond": {
  "n": "新渔场中文名",
  "lv": 50,
  "t": "船钓",
  "w": "海水",
  "d": 30.0,
  "sk": 200,
  "f": {}
}
```

然后在 `f` 中填入该渔场出没的鱼种（参考上方鱼种字段格式）。

### 添加新鱼种

在目标渔场的 `f` 对象中新增一条：

```json
"f": {
  "新鱼种中文名": {
    "r": "rare",
    "l": "mid",
    "m": 5.2,
    "b": "shrimp",
    "u": "minnow",
    "s": 1.0
  }
}
```

### 添加新装备

在 `tackle.json` 对应的数组（`hooks` / `lures` / `baits`）中追加一条，格式同上表。

### 构建验证

```bash
python build_data.py && python main.py
```

搜索新加的鱼名，确认计算器能正确推荐装备。

---

## 自有船鱼种数据贡献

游戏中的**自有船远航**会解锁专属鱼种和渔场。如果你有相关数据，欢迎贡献：

1. Fork 本仓库
2. 在 `渔场数据库.json` 中添加远航渔场（`t` 设为 `"船钓"`）
3. 填入该航线出没的鱼种及其属性（嘴大小、水层、最佳饵类型等）
4. 提交 Pull Request

不确定的数值（如嘴大小 `m`、体型系数 `s`）可以估算或留默认值 `1.0`，后续由其他贡献者校准。

---

## 构建流程

```
数据库/渔场数据库.json ──┐
                        ├── build_data.py ──→ main.py ──→ pyinstaller ──→ dist/xxx.exe
数据库/tackle.json ─────┘
```

`build_data.py` 读取 JSON 源数据，精简为计算器需要的字段，注入 `main_template.py` 的占位符，输出 `main.py`。

---

## License

MIT
