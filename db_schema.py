# db_schema.py
import pymssql
from ai_helper import DB_CONFIG


def main():
    conn = pymssql.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 1. 列出所有表
    cur.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME
    """)
    tables = [r[0] for r in cur.fetchall()]
    print("=== 所有表 ===")
    for t in tables:
        print(" -", t)

    # 2. 逐表列出字段 + 样例数据
    for t in tables:
        print(f"\n=== 表 {t} 字段 ===")
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME=%s ORDER BY ORDINAL_POSITION
        """, (t,))
        for name, dtype, length, nullable in cur.fetchall():
            length = f"({length})" if length else ""
            print(f"  {name:<20} {dtype}{length:<10} NULL={nullable}")

        cur.execute(f"SELECT TOP 3 * FROM [{t}]")
        print("  样例：")
        for row in cur.fetchall():
            print("   ", row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()