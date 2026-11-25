import duckdb

con = duckdb.connect("dbt/warehouse.duckdb")
con.execute("create schema if not exists raw")
files = {"restaurant": "restaurants", "users": "users", "food": "food", "menu": "menu",
         "orders": "orders", "order_items": "order_items", "reviews": "reviews"}
for f, t in files.items():
    con.execute(f"create or replace table raw.{t} as select * from read_csv_auto('data/bd/{f}.csv')")
    print(t, con.execute(f"select count(*) from raw.{t}").fetchone()[0])