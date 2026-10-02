# 屏蔽词收集 + 分类正则生成器

把「屏蔽哪些词」和「当时为什么屏蔽」一起记下来，再按分类一键生成正则。

## 直接运行

直接跑 `blocklist.py`（不带参数）就按文件顶部的配置生成正则：

```bat
python blocklist.py
```

配置全在 [blocklist.py](./blocklist.py) 顶部，想换目标改这几个常量就行：

```python
FLAVOR = "bilibili"   # bilibili / generic / java / pcre / js
COPY   = True         # 生成后自动复制到剪贴板
OUTPUT = ""           # 非空则同时写入文件，如 "rules.txt"
RECORD_ONLY = {"互动刷屏"}  # 只记录、不参与生成的分类
DATA   = ...          # 数据文件位置
```

当前配置是哔哩哔哩写法，输出：

```
/(致敬|舒服|热乎|反弹|便宜|划算|上岸|健康|英文|高能|愿|吉|值|考|顺|幕|翻|抽|我|三)/
```

## 命令行

需要临时换个目标、不动配置时，用 `gen` 的开关覆盖：

```bat
python blocklist.py                  :: 按配置生成
python blocklist.py gen -f generic   :: 临时按 TG / 通用写法生成
python blocklist.py add 引流 "加微信" -t "到处引流"
python blocklist.py add 弹幕 致敬     :: 不写 -t 就不会追问，适合批量
python blocklist.py list             :: 一行一条列出全部记录
python blocklist.py cats             :: 各分类词数
python blocklist.py rm 引流 "加微信"
python blocklist.py thought 引流 "加微信" "换个说法"
```

`add` 把分类和词都写全时不会追问想法（想法留空）；只写一半、或完全不写参数，才会接着问「分类 → 屏蔽词 → 想法」。

`gen` 的开关：

| 开关 | 作用 |
| --- | --- |
| `-f/--flavor` | 临时覆盖配置里的 `FLAVOR` |
| `-o rules.txt` | 临时覆盖配置里的 `OUTPUT`，结果写入文件（UTF-8） |
| `--copy` | 配置里 `COPY = False` 时用它临时复制一次 |
| `gen 分类A 分类B` | 只生成指定分类（指名仅记录分类也会输出，见下） |

## 生成规则

* 分类自己起名，**每个分类各生成一条**合并正则，输出一行一条，可直接整段粘走（`RECORD_ONLY` 里的分类不生成，见下）。
* 词内正则特殊字符自动转义；同分类多个词合并成 `(词1|词2)`，**长词排前面**，免得短词先把长词的一部分吃掉。

| flavor | 输出 | 用在哪 |
| --- | --- | --- |
| `generic` / `java` / `pcre` | `(?i)(点击链接|加微信)` | Python、PCRE、Java/Kotlin（安卓第三方 TG 客户端） |
| `js` | `(点击链接|加微信)` | JS 不支持行内 `(?i)`，忽略大小写用调用方的 `i` 标志 |
| `bilibili` | `/(点击链接|加微信)/` | 哔哩哔哩站内「弹幕 / 评论屏蔽词」，必须斜杠包裹，一行一条 |

站内屏蔽词没有「忽略大小写」开关，英文词要大小写都拦就两种各加一条。

## 仅记录分类

有些规则只在特定语境成立（比如「报时间 + 喊人互动」的刷屏），塞进通用正则会误伤。把这类词放进 `RECORD_ONLY` 指定的分类，就只攒着、不参与生成：

* `gen`（含直接运行）默认跳过它们，被跳过的分类名打到 stderr 提示一句，stdout 里干干净净；
* `cats` / `list` 给它们标上「（仅记录）」，方便回头看；
* `add` 到这些分类时会提示「仅记录，不参与生成」；
* 想临时看一眼，显式写 `python blocklist.py gen 互动刷屏`：此时**原样输出，不转义、不合并**，所以往里放整条现成正则也不会被改坏。

再加一个仅记录分类，在 `RECORD_ONLY` 里加上名字即可（分类名照常起）：

```python
RECORD_ONLY = {"互动刷屏", "另一个分类"}
```

## 数据文件

存在 `data/blocked_words.json`（可在配置里用 `DATA` 改路径），纯文本可直接手工编辑：

```json
{
  "引流": [
    { "word": "加微信", "thought": "到处引流", "added_at": "2026-10-03T02:16:48" }
  ]
}
```

## 环境要求

Python 3.8+，只用标准库。
