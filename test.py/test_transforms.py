import sys; sys.path.append("src")
from pyspark.sql import SparkSession
from transforms import daily_sales

def test_daily_sales_drops_negative_and_sums():
    spark = SparkSession.builder.master("local[1]").getOrCreate()
    df = spark.createDataFrame(
        [("d1", 100.0), ("d1", 50.0), ("d1", -5.0)], "order_date STRING, amount DOUBLE")
    row = daily_sales(df).collect()[0]
    assert row.revenue == 150.0
    assert row.orders == 2