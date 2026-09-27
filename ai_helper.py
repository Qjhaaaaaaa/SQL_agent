# ai_helper.py
import os
import json
import pymssql
from dotenv import load_dotenv

# ============== 加载 .env ==============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
DEFAULT_MODEL     = os.getenv("DEFAULT_MODEL", "qwen-plus").strip()
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://ws-snoyjr5nr23z5zj7.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
).strip()

if DASHSCOPE_API_KEY:
    print(f"[配置] API Key 已加载（{DASHSCOPE_API_KEY[:8]}...）")
    print(f"[配置] Base URL: {DASHSCOPE_BASE_URL}")
else:
    print("[警告] 未找到 DASHSCOPE_API_KEY，请检查 .env")

print(f"[配置] 默认模型：{DEFAULT_MODEL}")

# ============== 使用 OpenAI 兼容模式 ==============
from openai import OpenAI

_client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
)

# ============== 数据库配置 ==============
DB_CONFIG = dict(
    server=os.getenv("DB_SERVER", "localhost").strip(),
    user=os.getenv("DB_USER", "").strip(),
    password=os.getenv("DB_PASSWORD", "").strip(),
    database=os.getenv("DB_NAME", "").strip(),
)

# ============== 支持的模型列表 ==============
AVAILABLE_MODELS = [
    "qwen3.8-max-0902",
    "qwen3-max",
    "qwen-max",
    "qwen-plus",
    "qwen-turbo",
    "qwen-long",
    "qwen-coder-plus",
    "deepseek-v3",
    "glm-4",
]

# ============== 自动读取数据库 schema ==============
_SCHEMA_CACHE = None

def get_schema():
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE:
        return _SCHEMA_CACHE
    try:
        conn = pymssql.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME
        """)
        tables = [r[0] for r in cur.fetchall()]
        lines = []
        for t in tables:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME=%s ORDER BY ORDINAL_POSITION
            """, (t,))
            cols = [f"{n} {d}" + (f"({l})" if l else "")
                    for n, d, l in cur.fetchall()]
            lines.append(f"表 {t}: " + ", ".join(cols))
        cur.close()
        conn.close()
        _SCHEMA_CACHE = "\n".join(lines)
    except Exception as e:
        _SCHEMA_CACHE = f"(读取schema失败: {e})"
    return _SCHEMA_CACHE


# ============== 通用调用（纯文本）==============
def ask_qwen(prompt, system=None, model=None, temperature=0.7):
    if not DASHSCOPE_API_KEY:
        return "错误：未配置 DASHSCOPE_API_KEY"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = _client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI调用异常：{e}"


# ============== 核心：分析用户需求，返回 action + SQL + 图表建议 ==============
def analyze_and_query(nl_text, table_name="", model=None):
    """
    让 AI 分析用户需求，返回 dict：
    {
        "action": "chat | query | insert | update | delete | ddl",
        "thought": "分析说明",
        "answer": "当 action=chat 时的直接回答内容",
        "sql": "SQL 语句，action!=chat 时必填",
        "chart": "bar | line | pie | hist | none",
        "title": "...",
        "xlabel": "...",
        "ylabel": "..."
    }
    """
    schema = get_schema()

    system = f"""你是一个 SQL Server 数据分析助手，可以直接和用户对话，也可以执行数据库操作。

═══════ 数据库结构 ═══════
{schema}
══════════════════════════

当前用户正在操作的表：{table_name or "(未指定)"}

用户会用自然语言描述需求。你必须**只返回 JSON**，不要任何解释文字、不要 markdown 代码块标记。

JSON 格式：
{{
    "action": "chat | query | insert | update | delete | ddl",
    "thought": "用一句中文简要说明你的判断",
    "answer": "当 action=chat 时，直接回答用户的内容；其他 action 时填空字符串",
    "sql": "要执行的 SQL 语句；action=chat 时填空字符串",
    "chart": "bar | line | pie | hist | none",
    "title": "图表标题",
    "xlabel": "X轴标签",
    "ylabel": "Y轴标签"
}}

═══════ action 选择规则 ═══════
- "chat"：用户只是问问题、聊天、或者信息已经在 schema 里能回答的
  · 例如："有哪些表？"、"表 xxx 有哪些列？"、"哪些列适合画图？"、"你能做什么？"
  · 这类问题不需要执行 SQL，直接看 schema 就能回答，answer 字段填你的回答
- "query"：需要从数据库 SELECT 数据（查明细、统计、聚合等）
- "insert"：用户要插入数据
- "update"：用户要修改数据
- "delete"：用户要删除数据
- "ddl"：用户要建表/改表结构/删表

═══════ 可视化建议规则（chart 字段）═══════
判断哪些列适合什么图，参考：
- 数值列（int/float/decimal）+ 想看分布 → "hist"
- 分类列（varchar 且不同值少）+ 想看数量对比 → "bar"
- 分类列 + 想看占比 → "pie"
- 时间列（datetime/date）+ 想看趋势 → "line"

chart 具体选择：
- 用户明确要求"柱状图/条形图" → "bar"
- 用户明确要求"饼图/占比" → "pie"
- 用户明确要求"折线图/趋势" → "line"
- 用户明确要求"分布图/直方图" → "hist"
- 用户没明确要求，但问题明显是统计类 → 主动选合适的
- 用户只是问信息、查明细、闲聊 → "none"

═══════ SQL 规则 ═══════
- 表名/字段名如果含中文或特殊字符，用 [] 包起来
- SELECT 查询加 TOP 100，避免返回过多数据
- 需要画图时，SQL 结果最好返回**两列**：第一列是标签（类别/时间），第二列是数值
- 问"有哪些表"时若用 chat 则不必生成 SQL；若选择 query 可用：SELECT name FROM sys.tables
- 问"某表有哪些列"时若用 chat 则不必生成 SQL；若选择 query 可用：SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='xxx'

只返回 JSON，不要任何其他字符。
"""

    raw = ask_qwen(nl_text, system=system, model=model)
    return _parse_json(raw)


def _parse_json(text):
    """从 AI 返回的文本里解析 JSON，容错处理"""
    default = {
        "action": "chat",
        "thought": "AI 返回格式异常",
        "answer": "",
        "sql": "",
        "chart": "none",
        "title": "",
        "xlabel": "",
        "ylabel": "",
    }
    if not text:
        return default

    text = text.strip()

    # 去掉 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    # 找到第一个 { 和最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except Exception:
        default["answer"] = f"AI 返回内容无法解析：\n{text[:500]}"
        return default


# ============== 保留兼容接口 ==============
def explain_data(content, model=None):
    return ask_qwen(
        f"请用通俗中文解释下面数据的内容：\n{content}",
        system="你是数据分析师，回答简洁。",
        model=model,
    )


def optimize_sql(sql, model=None):
    return ask_qwen(
        f"请分析以下 SQL 是否有性能问题，并给出优化建议：\n{sql}",
        system="你是 SQL Server 性能优化专家。",
        model=model,
    )