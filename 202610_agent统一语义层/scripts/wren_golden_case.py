"""Run with the pinned Wren checkout's uv environment; synthetic CNY cents."""
import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
from wren import DataSource, WrenEngine, WrenError
from wren.config import WrenConfig


def main():
    with TemporaryDirectory() as directory:
        database = Path(directory) / "gold.duckdb"
        with duckdb.connect(str(database)) as connection:
            connection.execute("CREATE TABLE orders(id VARCHAR, tenant VARCHAR, amount BIGINT)")
            connection.execute("INSERT INTO orders VALUES ('O1','A',10000),('O2','A',20000),('O3','B',30000)")
            connection.execute("CREATE TABLE refunds(order_id VARCHAR, amount BIGINT)")
            connection.execute("INSERT INTO refunds VALUES ('O1',1000),('O1',2000),('O3',5000)")
            connection.execute("CREATE TABLE items(order_id VARCHAR, item_id VARCHAR)")
            connection.execute("INSERT INTO items VALUES ('O1','I1'),('O1','I2'),('O2','I3'),('O3','I4'),('O3','I5')")
        fields = {
            "orders": [("id", "varchar"), ("tenant", "varchar"), ("amount", "bigint")],
            "refunds": [("order_id", "varchar"), ("amount", "bigint")],
            "items": [("order_id", "varchar"), ("item_id", "varchar")],
        }
        manifest = {"catalog": "wren", "schema": "public", "models": [
            {"name": name, "tableReference": {"catalog": "gold", "schema": "main", "table": name},
             "columns": [{"name": column, "type": kind} for column, kind in columns]}
            for name, columns in fields.items()
        ]}
        encoded = base64.b64encode(json.dumps(manifest).encode()).decode()
        correct = """WITH r AS (
            SELECT order_id, SUM(amount) AS refunded FROM refunds GROUP BY order_id
        ) SELECT o.tenant, SUM(o.amount - COALESCE(r.refunded,0)) AS net
          FROM orders o LEFT JOIN r ON o.id=r.order_id GROUP BY o.tenant ORDER BY o.tenant"""
        naive = """SELECT o.tenant, SUM(o.amount - COALESCE(r.amount,0)) AS net
            FROM orders o LEFT JOIN refunds r ON o.id=r.order_id
            LEFT JOIN items i ON o.id=i.order_id GROUP BY o.tenant ORDER BY o.tenant"""
        with WrenEngine(encoded, DataSource.duckdb, {"url": directory, "format": "duckdb"},
                        config=WrenConfig(strict_mode=True), fallback=False) as engine:
            result = engine.query(correct).to_pylist()
            wrong_grain = engine.query(naive).to_pylist()
            assert result == [{"tenant": "A", "net": 27000}, {"tenant": "B", "net": 25000}], result
            assert wrong_grain == [{"tenant": "A", "net": 54000}, {"tenant": "B", "net": 50000}], wrong_grain
            blocked = False
            try:
                engine.dry_plan("SELECT * FROM undeclared_table")
            except WrenError:
                blocked = True
            assert blocked
            result = [{"tenant": row["tenant"], "net": int(row["net"])} for row in result]
            wrong_grain = [{"tenant": row["tenant"], "net": int(row["net"])} for row in wrong_grain]
            print(json.dumps({"correct": result, "naive_join": wrong_grain,
                              "unknown_table_blocked": blocked}, ensure_ascii=False))


if __name__ == "__main__":
    main()
