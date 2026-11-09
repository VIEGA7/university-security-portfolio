"""Partial reconstruction from lab 8 screenshots 10, 11, 14, 15.

CSV source and notebook did not survive. Pass your own file with the documented
columns. No historical row counts or conclusions are invented.
"""
import argparse


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file')
    args=parser.parse_args()
    from pyspark.sql import SparkSession, functions as F
    spark=SparkSession.builder.appName('portfolio-storage-lab8').master('local[*]').getOrCreate()
    try:
        df=spark.read.csv(args.csv_file,header=True,inferSchema=True,multiLine=True)
        required={'Traffic Type','Protocol','Packet Length'}
        if not required.issubset(df.columns):
            raise ValueError(f'Missing columns: {sorted(required-set(df.columns))}')
        df.printSchema()
        df.show(5,truncate=False)
        df.groupBy('Traffic Type').count().orderBy(F.desc('count')).show(truncate=False)
        df.groupBy('Protocol').agg(F.count('*').alias('count'),
            F.avg('Packet Length').alias('average_packet_length')).orderBy(F.desc('count')).show(truncate=False)
        print(f'Rows: {df.count()}')
    finally:
        spark.stop()
