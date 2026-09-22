from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("SQLServerConnectionTest")
    .config(
        "spark.jars",
        r"C:\sqljdbc\sqljdbc_13.6\enu\jars\mssql-jdbc-13.6.0.jre11.jar"
    )
    .getOrCreate()
)

print("Spark session created successfully.")

jdbc_url = (
    "jdbc:sqlserver://localhost:1433;"
    "databaseName=SpeechToTextDB;"
    "integratedSecurity=true;"
    "encrypt=false;"
    "trustServerCertificate=true;"
)

connection_properties = {
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

reference_df = spark.read.jdbc(
    url=jdbc_url,
    table="audio_reference",
    properties=connection_properties
)

print("SQL Server connection successful.")

reference_df.show(truncate=False)

print("Record count:", reference_df.count())

spark.stop()