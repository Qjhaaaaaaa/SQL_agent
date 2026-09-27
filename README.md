# AI 增强的 SQL Server 数据库管理系统

基于 tkinter + pymssql + 通义千问（DashScope）的数据库智能助手，支持 CRUD 操作、数据可视化、自然语言转 SQL、SQL 优化、数据解读，以及广告点击率预测。

## ✨ 功能特性

- 📊 **数据库 CRUD**：增删改查、条件查询、一键查询全部
- 📈 **数据可视化**：柱状图、饼图、直方图，图形嵌入界面中央
- 🤖 **AI 助手**：
  - 自然语言 → SQL（自动执行并返回结果）
  - AI 解释查询结果的数据分布
  - AI 优化 SQL 性能
- 🎯 **决策树预测**：预测用户是否会点击广告
- 🔄 **多模型支持**：可切换 Qwen / DeepSeek / GLM / Kimi 等多种大模型
- 🔐 **安全配置**：所有密钥保存在 `.env`，不上传 GitHub

## 🖼️ 界面截图

> 截图待补充（把运行后的界面截图放到 `docs/screenshot.png`，然后这里写
> `![界面](docs/screenshot.png)`）

## 📋 环境要求

- Python 3.10+
- SQL Server 已启动，数据库可连接
- 阿里云百炼 API Key（[申请地址](https://bailian.console.aliyun.com/)）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/SQL_agent.git
cd SQL_agent
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

用编辑器打开 `.env`，填入你自己的信息：

```ini
DASHSCOPE_API_KEY=sk-你的真实Key
DEFAULT_MODEL=qwen3.8-max-0902

DB_SERVER=你的SQLServer地址
DB_USER=你的用户名
DB_PASSWORD=你的密码
DB_NAME=你的数据库名
```

> ⚠️ `.env` 已被 `.gitignore` 屏蔽，不会被提交到 GitHub。

### 5. 运行程序

```bash
python run.py
```

## 📁 项目结构

```
SQL_agent/
├── .env                  # 本地配置（不上传）
├── .env.example          # 配置模板
├── .gitignore            # Git 忽略规则
├── requirements.txt      # Python 依赖
├── README.md             # 说明文档
├── run.py                # 统一入口
├── agent_sql.py          # 主程序（界面 + 数据库 + AI）
├── ai_helper.py          # AI 封装（schema 自动读取、模型调用）
├── db_schema.py          # 数据库结构探查工具
└── data/
    └── 广告点击率预估.csv  # 决策树训练数据
```

## 🛠️ 技术栈

| 技术 | 用途 |
|---|---|
| Python 3.10 | 开发语言 |
| tkinter | 图形界面 |
| pymssql | SQL Server 连接 |
| matplotlib | 数据可视化 |
| scikit-learn | 决策树模型 |
| dashscope / openai | 通义千问 API |
| python-dotenv | 读取 .env 配置 |

## 📖 使用说明

### 数据库操作

1. 顶部输入表名 → 点「查询全部」查看所有数据
2. 输入「查询条件」（如 `id = 2334`）→ 点「条件查询」
3. 插入 / 删除 / 更新，对应各自输入框和按钮

### AI 助手

1. 在下拉框选择模型（默认 `qwen3.8-max-0902`）
2. 在「自然语言」框输入需求，例如：
   - `查询表结构`
   - `统计每个性别的用户数量`
   - `找出点击广告最多的年龄段`
3. 点「① 生成SQL并执行+自动画图」→ AI 自动生成 SQL 并执行
4. 如果结果是两列（类别 + 数量），**会自动画出柱状图并显示在界面中央**
5. 点「② 解释查询结果」→ AI 用中文解读数据
6. 点「③ 优化SQL」→ AI 对最近一次 SQL 给出优化建议

### 可视化

- 顶部填好表名，点 `gender` / `age_level` / `user_depth` / `var_1` / `isClick` 按钮
- 图表会显示在界面中央的白色区域

## 🔐 安全说明

- 所有敏感信息（API Key、数据库密码）都保存在本地 `.env`，**不上传 GitHub**
- 如果 key 曾经泄露，请立即到阿里云控制台**吊销并重新生成**
- 仓库中只保留 `.env.example` 作为配置模板

## 📄 License

MIT License

## 🙏 致谢

- 阿里云[百炼平台](https://bailian.console.aliyun.com/)
- 通义千问模型