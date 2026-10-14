from pyspark.sql import DataFrame, functions as F

def daily_sales(orders: DataFrame) -> DataFrame:
    return (orders
            .filter(F.col("amount") > 0)
            .groupBy("order_date")
            .agg(F.sum("amount").alias("revenue"),
                 F.count("*").alias("orders")))