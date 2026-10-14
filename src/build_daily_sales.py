import sys
from pyspark.sql import SparkSession
from transforms import daily_sales

schema = sys.argv[1]
spark = SparkSession.builder.getOrCreate()

orders = spark.createDataFrame(
    [("2026-10-13", 100.0), ("2026-10-13", 50.0), ("2026-10-14", 70.0), ("2026-10-14", -5.0)],
    "order_date STRING, amount DOUBLE")

daily_sales(orders).write.mode("overwrite").saveAsTable(f"workspace.{schema}.daily_sales")
print(f"Wrote workspace.{schema}.daily_sales")