# agent_sql.py
import os
import tkinter as tk
from tkinter import ttk
import pymssql
import numpy as np
import pandas as pd
from tkinter import messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

from ai_helper import (
    DB_CONFIG,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    analyze_and_query,
    explain_data,
)

# ============== 中文字体 ==============
try:
    mpl.font_manager.fontManager.addfont(r"C:\Windows\Fonts\STSONG.TTF")
    plt.rcParams['font.sans-serif'] = ['STSong', 'SimHei', 'Microsoft YaHei']
except Exception:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ============== 路径 ==============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "广告点击率预估.csv")
PREDICTION_TXT = os.path.join(BASE_DIR, "Prediction.txt")

# ============== 决策树模型 ==============
clf = None


def train_model():
    global clf
    try:
        data = pd.read_csv(CSV_PATH, encoding="utf-8")
        data.dropna(inplace=True)
        dc = data.copy(deep=True)
        dc.replace("Male", 1, inplace=True)
        dc.replace("Female", 2, inplace=True)
        X = np.array(dc.iloc[:, 8:12])
        Y = data["isClick"].to_list()
        X_train, X_test, y_train, y_test = train_test_split(
            X, Y, train_size=0.75, random_state=0)
        clf = DecisionTreeClassifier(criterion="gini", max_depth=3, random_state=0)
        clf.fit(X_train, y_train)
        print("[模型] 决策树训练完成")
    except Exception as e:
        print(f"[模型] 训练跳过：{e}")
        clf = None


class DatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 增强的 SQL Server 数据库管理系统")

        # ---- 自适应屏幕大小并居中 ----
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * 0.82)
        h = int(sh * 0.82)
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 20)     # 稍微上移，避开任务栏
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1000, 620)

        self.last_query = ""
        self.canvas = None

        self.conn = pymssql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

        self._build_layout()

    # ==================== 布局 ====================
    def _build_layout(self):
        # 左固定 380，右自适应
        self.root.grid_columnconfigure(0, weight=0, minsize=380)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        left = tk.Frame(self.root, bg="#f5f5f5", width=380)
        left.grid(row=0, column=0, sticky="ns", padx=(4, 2), pady=4)
        left.grid_propagate(False)

        right = tk.Frame(self.root)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)
        right.grid_columnconfigure(0, weight=1)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, p):
        F = ("Microsoft YaHei", 9)
        FB = ("Microsoft YaHei", 9, "bold")

        tk.Label(p, text="当前表名：", font=FB, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(8, 1))
        self.table_name_entry = tk.Entry(p, font=("Consolas", 9))
        self.table_name_entry.pack(fill=tk.X, padx=8, pady=1)

        row = tk.Frame(p, bg="#f5f5f5")
        row.pack(fill=tk.X, padx=8, pady=3)
        tk.Button(row, text="查询全部", command=self.search_data,
                  bg="#4a90e2", fg="white", font=F
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        tk.Button(row, text="条件查询", command=self.search_data_2,
                  bg="#4a90e2", fg="white", font=F
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        tk.Label(p, text="查询条件：", font=F, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(5, 1))
        self.search_data_entry = tk.Entry(p, font=("Consolas", 9))
        self.search_data_entry.pack(fill=tk.X, padx=8, pady=1)

        tk.Label(p, text="插入（含括号）：", font=F, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(5, 1))
        self.insert_data_entry = tk.Entry(p, font=("Consolas", 9))
        self.insert_data_entry.pack(fill=tk.X, padx=8, pady=1)
        tk.Button(p, text="插入", command=self.insert_data, font=F
                  ).pack(fill=tk.X, padx=8, pady=1)

        tk.Label(p, text="删除条件：", font=F, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(5, 1))
        self.delete_data_entry = tk.Entry(p, font=("Consolas", 9))
        self.delete_data_entry.pack(fill=tk.X, padx=8, pady=1)
        tk.Button(p, text="删除", command=self.delete_data, font=F
                  ).pack(fill=tk.X, padx=8, pady=1)

        tk.Label(p, text="更新 SQL：", font=F, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(5, 1))
        self.update_data_entry = tk.Entry(p, font=("Consolas", 9))
        self.update_data_entry.pack(fill=tk.X, padx=8, pady=1)
        tk.Button(p, text="更新", command=self.update_data, font=F
                  ).pack(fill=tk.X, padx=8, pady=1)

        tk.Label(p, text="快速可视化：", font=FB, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(8, 1))
        r1 = tk.Frame(p, bg="#f5f5f5")
        r1.pack(fill=tk.X, padx=8, pady=1)
        for name, cmd in [("gender", self.plot_gender),
                          ("age_level", self.plot_age_level),
                          ("user_depth", self.plot_user_depth)]:
            tk.Button(r1, text=name, command=cmd, font=F
                      ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        r2 = tk.Frame(p, bg="#f5f5f5")
        r2.pack(fill=tk.X, padx=8, pady=1)
        for name, cmd in [("var_1", self.plot_var_1),
                          ("isClick", self.plot_isClick),
                          ("点击率预测", self.pre_data)]:
            tk.Button(r2, text=name, command=cmd, font=F
                      ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        tk.Label(p, text="查询结果：", font=FB, bg="#f5f5f5").pack(
            anchor="w", padx=8, pady=(8, 1))

        rf = tk.Frame(p, bg="#f5f5f5")
        rf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(1, 6))

        self.result_text = tk.Text(rf, wrap=tk.NONE, font=("Consolas", 8))
        ysb = tk.Scrollbar(rf, orient="vertical", command=self.result_text.yview)
        xsb = tk.Scrollbar(rf, orient="horizontal", command=self.result_text.xview)
        self.result_text.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        rf.grid_rowconfigure(0, weight=1)
        rf.grid_columnconfigure(0, weight=1)

    def _build_right_panel(self, p):
        # ============ 画布区 ============
        plot_box = tk.LabelFrame(p, text=" 📊 可视化 ",
                                 font=("Microsoft YaHei", 9, "bold"),
                                 fg="#2c5aa0")
        plot_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))

        self.plot_frame = tk.Frame(plot_box, bg="white")
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # ============ 对话区 ============
        chat_box = tk.LabelFrame(p, text=" 💬 AI 对话 ",
                                 font=("Microsoft YaHei", 9, "bold"),
                                 fg="#2c5aa0")
        chat_box.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))

        # 输入行（底部）
        input_frame = tk.Frame(chat_box)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=(2, 4))

        tk.Label(input_frame, text="模型：",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        ttk.Combobox(input_frame, textvariable=self.model_var,
                     values=AVAILABLE_MODELS, width=18,
                     state="readonly").pack(side=tk.LEFT, padx=4)

        self.ai_entry = tk.Entry(input_frame, font=("Microsoft YaHei", 9))
        self.ai_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.ai_entry.bind("<Return>", lambda e: self.send_message())

        tk.Button(input_frame, text="发送", command=self.send_message,
                  bg="#4a90e2", fg="white",
                  font=("Microsoft YaHei", 9, "bold"), padx=14).pack(side=tk.LEFT)

        # 对话历史（height 从 10 缩到 6）
        cf = tk.Frame(chat_box)
        cf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=(4, 2))

        self.chat_text = tk.Text(cf, wrap=tk.WORD,
                                 font=("Microsoft YaHei", 9),
                                 bg="#fafafa", height=6)
        csb = tk.Scrollbar(cf, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=csb.set)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        csb.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_text.tag_configure("user", foreground="#0066cc",
                                     font=("Microsoft YaHei", 9, "bold"),
                                     spacing1=3, spacing3=3)
        self.chat_text.tag_configure("ai", foreground="#008844",
                                     font=("Microsoft YaHei", 9),
                                     spacing1=3, spacing3=3)
        self.chat_text.tag_configure("system", foreground="#888888",
                                     font=("Microsoft YaHei", 8, "italic"),
                                     spacing1=1, spacing3=1)
        self.chat_text.tag_configure("error", foreground="#cc0000",
                                     font=("Microsoft YaHei", 9),
                                     spacing1=3, spacing3=3)
        self.chat_text.configure(state="disabled")

        self.append_chat("👋 欢迎使用 AI 数据库助手！\n", "system")
        self.append_chat("可以跟我说：\n", "system")
        self.append_chat("  • 有哪些表？\n", "system")
        self.append_chat("  • 表 user_ad 有哪些列？\n", "system")
        self.append_chat("  • 统计每个性别数量，画柱状图\n", "system")
        self.append_chat("  • 画 id 随时间的折线图\n", "system")

    # ==================== 对话 ====================
    def append_chat(self, text, tag="ai"):
        self.chat_text.configure(state="normal")
        self.chat_text.insert(tk.END, text, tag)
        self.chat_text.see(tk.END)
        self.chat_text.configure(state="disabled")

    def send_message(self):
        q = self.ai_entry.get().strip()
        if not q:
            return

        self.append_chat(f"\n👤 你：{q}\n", "user")
        self.ai_entry.delete(0, tk.END)
        self.root.update_idletasks()

        model = self.model_var.get()
        table = self._table()

        try:
            result = analyze_and_query(q, table_name=table, model=model)
        except Exception as e:
            self.append_chat(f"❌ AI 调用失败：{e}\n", "error")
            return

        action = result.get("action", "chat").lower()
        thought = result.get("thought", "")
        sql = result.get("sql", "").strip()
        chart = result.get("chart", "none")
        answer = result.get("answer", "").strip()

        # 显示 AI 的判断
        if thought:
            self.append_chat(f"🤖 AI：{thought}\n", "ai")

        # ---------- action = chat：直接回答，不执行 SQL ----------
        if action == "chat" or not sql:
            if answer:
                self.append_chat(f"{answer}\n", "ai")
            elif thought:
                pass
            else:
                self.append_chat("（AI 没有返回内容）\n", "ai")
            return

        # ---------- action = query：只读，直接执行 ----------
        if action == "query":
            self.append_chat(f"📝 SQL：{sql}\n", "system")
            try:
                self.cursor.execute(sql)
                rows = self.cursor.fetchall()
            except Exception as e:
                self.append_chat(f"❌ 执行失败：{e}\n", "error")
                return

            if not rows:
                self.append_chat("✅ 查询完成，结果为空\n", "system")
                return

            self.append_chat(f"✅ 查询到 {len(rows)} 条结果\n", "system")
            self._set_text("\n".join(str(r) for r in rows[:200]))

            # 画图
            if chart and chart != "none":
                try:
                    self._draw_chart_from_rows(
                        rows, chart,
                        title=result.get("title", q),
                        xlabel=result.get("xlabel", ""),
                        ylabel=result.get("ylabel", ""),
                    )
                    self.append_chat(f"📊 已生成 {chart} 图表\n", "system")
                except Exception as e:
                    self.append_chat(f"⚠️ 绘图失败：{e}\n", "error")
            return

        # ---------- action = 写操作：弹出确认框 ----------
        if action in ("insert", "update", "delete", "ddl"):
            # 映射中文名
            action_cn = {
                "insert": "插入",
                "update": "修改",
                "delete": "删除",
                "ddl": "表结构变更",
            }.get(action, action)

            self.append_chat(f"⚠️ 检测到写操作（{action_cn}）：\n", "error")
            self.append_chat(f"📝 SQL：{sql}\n", "system")

            # 弹出确认框
            confirm = tk.messagebox.askyesno(
                f"确认{action_cn}？",
                f"AI 打算执行以下 SQL：\n\n{sql}\n\n"
                f"此操作会修改数据库，且无法撤销。是否继续？"
            )

            if not confirm:
                self.append_chat("🚫 已取消操作。\n", "error")
                return

            try:
                self.cursor.execute(sql)
                # 获取受影响行数
                affected = self.cursor.rowcount
                self.conn.commit()
                self.append_chat(f"✅ {action_cn}成功，影响 {affected} 行\n", "system")
            except Exception as e:
                self.append_chat(f"❌ 执行失败：{e}\n", "error")
            return

        # 未知 action
        self.append_chat(f"⚠️ 未知的操作类型：{action}\n", "error")

    def _draw_chart_from_rows(self, rows, chart_type, title="", xlabel="", ylabel=""):
        if not rows:
            return

        n_cols = len(rows[0])

        if n_cols == 1:
            values = [r[0] for r in rows]
            if all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in values):
                self._draw(values, None, "hist",
                           xlabel or "值", ylabel or "频率",
                           title or "数值分布")
            else:
                raise ValueError("单列非数值，不画图")

        elif n_cols == 2:
            labels = [str(r[0]) for r in rows]
            values = [float(v) if v is not None else 0 for v in
                      [r[1] for r in rows]]

            if chart_type == "pie":
                self._draw(labels, values, "pie", "", "", title or "占比")
            elif chart_type == "line":
                self._draw(labels, values, "line",
                           xlabel or "X", ylabel or "Y", title or "")
            else:
                self._draw(labels, values, "bar",
                           xlabel or "类别", ylabel or "数值", title or "")
        else:
            raise ValueError(f"结果有 {n_cols} 列，暂不支持自动画图")

    # ==================== 可视化核心 ====================
    def _draw(self, x, y, kind, xlabel, ylabel, title, color='skyblue'):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        fig = plt.Figure(figsize=(8, 3.6), dpi=100)   # ← 变小
        ax = fig.add_subplot(111)

        if kind == "bar":
            ax.bar(range(len(x)), y, color=color, edgecolor="black")
            ax.set_xticks(range(len(x)))
            ax.set_xticklabels(x, rotation=30, ha="right", fontsize=8)
        elif kind == "hist":
            ax.hist(x, bins=20, color=color, edgecolor="black")
        elif kind == "pie":
            ax.pie(y, labels=x, autopct="%1.1f%%", startangle=90,
                   textprops={"fontsize": 8})
        elif kind == "line":
            ax.plot(range(len(x)), y, color=color, marker="o", linewidth=2)
            ax.set_xticks(range(len(x)))
            ax.set_xticklabels(x, rotation=30, ha="right", fontsize=8)

        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, fontsize=10)
        if kind != "pie":
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=8)
        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _table(self):
        return self.table_name_entry.get().strip()

    # ==================== 快速可视化按钮 ====================
    def plot_gender(self):
        t = self._table()
        if not t:
            return
        try:
            self.cursor.execute(f"SELECT gender, COUNT(*) FROM [{t}] GROUP BY gender")
            rows = self.cursor.fetchall()
            self._draw([str(r[0]) for r in rows],
                       [float(r[1]) for r in rows],
                       "bar", "性别", "人数", "gender 分布")
        except Exception as e:
            print("plot_gender error:", e)

    def plot_age_level(self):
        t = self._table()
        if not t:
            return
        try:
            self.cursor.execute(
                f"SELECT age_level, COUNT(*) FROM [{t}] "
                f"GROUP BY age_level ORDER BY age_level")
            rows = self.cursor.fetchall()
            self._draw([str(r[0]) for r in rows], [r[1] for r in rows],
                       "bar", "年龄等级", "人数", "age_level 分布", color="#9ecae1")
        except Exception as e:
            print("plot_age_level error:", e)

    def plot_user_depth(self):
        t = self._table()
        if not t:
            return
        try:
            self.cursor.execute(
                f"SELECT user_depth, COUNT(*) FROM [{t}] "
                f"GROUP BY user_depth ORDER BY user_depth")
            rows = self.cursor.fetchall()
            self._draw([str(r[0]) for r in rows], [r[1] for r in rows],
                       "bar", "用户价值深度", "人数", "user_depth 分布", color="#a1d99b")
        except Exception as e:
            print("plot_user_depth error:", e)

    def plot_var_1(self):
        t = self._table()
        if not t:
            return
        try:
            self.cursor.execute(f"SELECT var_1 FROM [{t}]")
            data = [r[0] for r in self.cursor.fetchall()]
            self._draw(data, None, "hist", "匿名特征 var_1", "频率",
                       "var_1 分布", color="#fdd0a2")
        except Exception as e:
            print("plot_var_1 error:", e)

    def plot_isClick(self):
        t = self._table()
        if not t:
            return
        try:
            self.cursor.execute(
                f"SELECT isClick, COUNT(*) FROM [{t}] GROUP BY isClick")
            rows = self.cursor.fetchall()
            labels = ["未点击" if r[0] == 0 else "点击" for r in rows]
            counts = [r[1] for r in rows]
            self._draw(labels, counts, "pie", "", "", "isClick 分布")
        except Exception as e:
            print("plot_isClick error:", e)

    # ==================== CRUD ====================
    def search_data(self):
        t = self._table()
        if not t:
            self._set_text("请输入表名！")
            return
        try:
            self.cursor.execute(f"SELECT * FROM [{t}]")
            rows = self.cursor.fetchall()
            self._set_text("\n".join(str(r) for r in rows) or "(空)")
        except Exception as e:
            self._set_text(f"查询失败：{e}")

    def search_data_2(self):
        t = self._table()
        cond = self.search_data_entry.get().strip()
        if not (t and cond):
            self._set_text("请输入表名和查询条件！")
            return
        try:
            self.cursor.execute(f"SELECT * FROM [{t}] WHERE {cond}")
            rows = self.cursor.fetchall()
            self._set_text("\n".join(str(r) for r in rows) or "(无结果)")
        except Exception as e:
            self._set_text(f"查询失败：{e}")

    def insert_data(self):
        t = self._table()
        data = self.insert_data_entry.get().strip()
        if not (t and data):
            self._set_text("请输入表名和数据！")
            return
        try:
            self.cursor.execute(f"INSERT INTO [{t}] VALUES {data}")
            self.conn.commit()
            self._set_text("数据插入成功！")
        except Exception as e:
            self._set_text(f"插入失败：{e}")

    def delete_data(self):
        t = self._table()
        cond = self.delete_data_entry.get().strip()
        if not (t and cond):
            self._set_text("请输入表名和删除条件！")
            return
        try:
            self.cursor.execute(f"DELETE FROM [{t}] WHERE {cond}")
            self.conn.commit()
            self._set_text("数据删除成功！")
        except Exception as e:
            self._set_text(f"删除失败：{e}")

    def update_data(self):
        sql = self.update_data_entry.get().strip()
        if not sql:
            self._set_text("请输入完整 UPDATE 语句！")
            return
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            self._set_text("数据更新成功！")
        except Exception as e:
            self._set_text(f"更新失败：{e}")

    # ==================== 决策树预测 ====================
    def pre_data(self):
        if clf is None:
            self._set_text("模型未训练（检查 data/广告点击率预估.csv）")
            return
        try:
            raw = self.result_text.get("1.0", "end").strip().splitlines()
            if not raw:
                self._set_text("结果框里没有数据可预测！")
                return
            row = eval(raw[0])
            text_1 = list(row)
            id_ = text_1[0]
            text_1[8] = 2 if text_1[8] == 'Male' else 1
            arr = np.array(text_1, dtype=object)[8:12].reshape(1, -1)
            pred = clf.predict(arr)
            result = (f"预测结果 (id={id_})："
                      + ("会点击广告！" if pred[0] == 1 else "不会点击广告！"))
            self._set_text(result)
            with open(PREDICTION_TXT, "a", encoding="utf-8") as f:
                f.write(result + "\n")
        except Exception as e:
            self._set_text(f"预测失败：{e}")

    # ==================== 工具 ====================
    def _set_text(self, s):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, s)

    def __del__(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception:
            pass


# ==================== 入口 ====================
def launch():
    train_model()
    root = tk.Tk()
    DatabaseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch()