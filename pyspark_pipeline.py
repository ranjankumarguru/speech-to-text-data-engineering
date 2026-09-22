from pyspark.sql import SparkSession
import sys
from pyspark.sql.functions import trim,regexp_replace,size, split, col
import uuid
from datetime import datetime
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    DoubleType,
    TimestampType	
)

def get_error_details(exception):
    return str(exception), type(exception).__name__


def handle_pipeline_failure(exception):
    error_message, error_type = get_error_details(exception)

def handle_unexpected_failure(exception):
    global error_message, error_type

    error_message, error_type = get_error_details(exception)

    print("\nPipeline Run Status: FAILED")
    print("Error Type:", error_type)
    print("Error Message:", error_message)

    failure_end_time = datetime.now()
    failure_duration_seconds = (
        failure_end_time - run_start_time
    ).total_seconds()

    failure_audit_record = {
        "run_id": run_id,
        "run_start_time": run_start_time,
        "run_end_time": failure_end_time,
        "run_duration_seconds": failure_duration_seconds,
        "run_status": "FAILED",
        "bronze_record_count": globals().get("bronze_record_count"),
        "silver_record_count": globals().get("silver_record_count"),
        "joined_record_count": globals().get("joined_record_count"),
        "final_record_count": globals().get("final_record_count"),
        "error_message": error_message,
        "error_type": error_type
    }

    print("\nFailed Pipeline Audit Record:")
    print(failure_audit_record)

    try:
        failure_audit_schema = StructType([
            StructField("run_id", StringType(), False),
            StructField("run_start_time", StringType(), False),
            StructField("run_end_time", StringType(), True),
            StructField("run_duration_seconds", DoubleType(), True),
            StructField("run_status", StringType(), False),
            StructField("bronze_record_count", LongType(), True),
            StructField("silver_record_count", LongType(), True),
            StructField("joined_record_count", LongType(), True),
            StructField("final_record_count", LongType(), True),
            StructField("error_message", StringType(), True),
            StructField("error_type", StringType(), True)
        ])

        failure_audit_df = spark.createDataFrame(
            [failure_audit_record],
            schema=failure_audit_schema
        )
        failure_audit_df.write \
            .format("jdbc") \
            .option(
                "url",
                "jdbc:sqlserver://localhost:1433;databaseName=SpeechToTextDB;integratedSecurity=true;encrypt=true;trustServerCertificate=true"
            ) \
            .option("dbtable", "pipeline_audit") \
            .option(
                "driver",
                "com.microsoft.sqlserver.jdbc.SQLServerDriver"
            ) \
            .mode("append") \
            .save()

        print("\nFailed pipeline audit record written successfully to SQL Server.")

    except Exception as audit_exception:
        print("\nWARNING: Failed to write failure audit record.")
        print("Audit Error Type:", type(audit_exception).__name__)
        print("Audit Error Message:", str(audit_exception))
error_message = None
error_type = None
sys.excepthook = lambda exc_type, exc_value, exc_traceback: handle_unexpected_failure(exc_value)

spark = (
    SparkSession.builder
    .appName("SpeechToTextDE")
    .getOrCreate()
)

print("Spark session created successfully.")

# ============================================================
# PIPELINE RUN TRACKING
# ============================================================

run_id = str(uuid.uuid4())
run_start_time = datetime.now()

print("\nPipeline Run ID:", run_id)
print("Pipeline Start Time:", run_start_time)

bronze_path = "output/got_s1e7_what_want.json"

bronze_schema = StructType([
    StructField("audio_id", StringType(), True),	
    StructField("audio_filename", StringType(), True),
    StructField("source", StringType(), True),
    StructField("file_type", StringType(), True),
    StructField("file_size_bytes", LongType(), True),
    StructField("batch_id", StringType(), True),
    StructField("ingestion_timestamp", StringType(), True),
    StructField("processing_timestamp", StringType(), True),
    StructField("model", StringType(), True),
    StructField("language", StringType(), True),
    StructField("status", StringType(), True),
    StructField("processing_duration_seconds", DoubleType(), True),
    StructField("transcription", StringType(), True),
    StructField("transcription_length", LongType(), True),
    StructField("word_count", LongType(), True),
    StructField("error", StringType(), True),
    StructField("error_type", StringType(), True),
    StructField("pipeline_version", StringType(), True)
])

bronze_df = (
    spark.read
    .schema(bronze_schema)
    .option("multiLine", True)
    .json(bronze_path)
)

bronze_df = bronze_df.withColumn(
    "audio_file",
    col("audio_filename")
)

# BRONZE DATA QUALITY CHECK - DUPLICATE AUDIO IDs

print("\nChecking Bronze Data for duplicate audio_id values...")

duplicate_bronze_df = (
    bronze_df
    .groupBy("audio_id")
    .count()
    .filter(col("count") > 1)
)

duplicate_bronze_count = duplicate_bronze_df.count()


print("Duplicate Bronze audio_id count:", duplicate_bronze_count)

if duplicate_bronze_count == 0:
    print("Bronze Data Quality Check: PASSED - No duplicate audio_id values found.")
else:
    print("Bronze Data Quality Check: FAILED - Duplicate audio_id values found.")
    duplicate_bronze_df.show(truncate=False)

bronze_record_count = bronze_df.count()

print("Bronze Record Count:", bronze_record_count)


print("Bronze JSON loaded successfully.")

bronze_df.printSchema()
bronze_df.show(truncate=False)

print("Bronze record count:", bronze_df.count())

bronze_df.select(
    "audio_file",
    "status",
    "transcription",
    "word_count",
    "processing_duration_seconds"
).show(truncate=False)
print("\nBronze data quality checks:")

bronze_df.select(
    "audio_file",
    "status",
    "transcription",
    "word_count",
    "processing_duration_seconds"
).show(truncate=False)

print("Null audio_file:", bronze_df.filter(bronze_df.audio_file.isNull()).count())
print("Null status:", bronze_df.filter(bronze_df.status.isNull()).count())
print("Null transcription:", bronze_df.filter(bronze_df.transcription.isNull()).count())
print("Zero word_count:", bronze_df.filter(bronze_df.word_count == 0).count())
print(
    "Non-success records:",
    bronze_df.filter(bronze_df.status != "success").count()
)

# ============================================================
# SILVER LAYER
# ============================================================

print("\nCreating Silver DataFrame...")

silver_df = bronze_df.filter(
    bronze_df.status == "success"
)

silver_df = silver_df.withColumn(
    "transcription_clean",
    regexp_replace(
        trim(silver_df.transcription),
        r"\s+",
        " "
    )
)

silver_df = silver_df.withColumn(
    "cleaned_word_count",
    size(split(silver_df.transcription_clean, " "))
)

silver_record_count = silver_df.count()
print("Silver record count:", silver_record_count)

silver_df.select(
    "audio_file",
    "word_count",
    "transcription_clean",
    "cleaned_word_count"
).show(truncate=False)

# ============================================================
# REFERENCE DATASET
# ============================================================

print("\nReading Reference Dataset from SQL Server via JDBC...")

sql_reference_df = (
    spark.read
    .format("jdbc")
    .option(
        "url",
        "jdbc:sqlserver://localhost:1433;databaseName=SpeechToTextDB;integratedSecurity=true;encrypt=true;trustServerCertificate=true"
    )
    .option("dbtable", "audio_reference")
    .option(
        "driver",
        "com.microsoft.sqlserver.jdbc.SQLServerDriver"
    )
    .load()
)

print("SQL Server reference record count:", sql_reference_df.count())

sql_reference_df.show(truncate=False)

reference_df = sql_reference_df.drop("created_at")

# REFERENCE DATA QUALITY CHECK - DUPLICATE AUDIO IDs

print("\nChecking Reference Dataset for duplicate audio_id values...")

duplicate_reference_df = (
    reference_df
    .groupBy("audio_id")
    .count()
    .filter(col("count") > 1)
)

duplicate_reference_count = duplicate_reference_df.count()

print("Duplicate reference audio_id count:", duplicate_reference_count)

if duplicate_reference_count == 0:
    print("Reference Data Quality Check: PASSED - No duplicate audio_id values found.")
else:
    print("Reference Data Quality Check: FAILED - Duplicate audio_id values found.")
    duplicate_reference_df.show(truncate=False)

# JOIN
print("\nJoining Silver Data with Reference Dataset...")

# ============================================================
# JOIN SILVER DATA WITH REFERENCE DATA
# ============================================================

print("\nJoining Silver Data with Reference Dataset...")

joined_df = (
    silver_df
    .join(
        reference_df.drop("audio_file"),
        on="audio_id",
        how="inner"
    )
)

joined_record_count = joined_df.count()
print("Joined record count:", joined_record_count)



# ============================================================
# TRANSCRIPTION MATCH CHECK
# ============================================================

print("\nChecking Transcription Match...")

from pyspark.sql.functions import col, when

joined_df = joined_df.withColumn(
    "transcription_match",
    when(
        col("transcription_clean") == col("expected_transcription"),
        "MATCH"
    ).otherwise("MISMATCH")
)

joined_df.select(
    "audio_file",
    "transcription_clean",
    "expected_transcription",
    "transcription_match"
).show(truncate=False)

# ============================================================
# RECONCILIATION SUMMARY
# ============================================================

print("\nCreating Reconciliation Summary...")

from pyspark.sql.functions import count, sum, when, col, round

reconciliation_summary = joined_df.agg(
    count("*").alias("total_records"),
    sum(
        when(col("transcription_match") == "MATCH", 1)
        .otherwise(0)
    ).alias("match_count"),
    sum(
        when(col("transcription_match") == "MISMATCH", 1)
        .otherwise(0)
    ).alias("mismatch_count")
)

reconciliation_summary = reconciliation_summary.withColumn(
    "match_percentage",
    round(
        col("match_count") / col("total_records") * 100,
        2
    )
)

reconciliation_summary.show()

# ============================================================
# TRANSCRIPTION WORD COUNT COMPARISON
# ============================================================

print("\nCalculating Transcription Word Count Difference...")

from pyspark.sql.functions import size, split, abs

joined_df = joined_df.withColumn(
    "expected_word_count",
    size(split(col("expected_transcription"), " "))
)

joined_df = joined_df.withColumn(
    "word_count_difference",
    abs(
        col("cleaned_word_count") - col("expected_word_count")
    )
)

joined_df.select(
    "audio_file",
    "cleaned_word_count",
    "expected_word_count",
    "word_count_difference",
    "transcription_match"
).show(truncate=False)

# ============================================================
# NORMALIZE TRANSCRIPTION TEXT FOR COMPARISON
# ============================================================

print("\nNormalizing Transcription Text for Comparison...")

from pyspark.sql.functions import lower, regexp_replace, trim

joined_df = joined_df.withColumn(
    "generated_normalized",
    trim(
        regexp_replace(
            lower(col("transcription_clean")),
            r"[^\w\s]",
            ""
        )
    )
)

joined_df = joined_df.withColumn(
    "expected_normalized",
    trim(
        regexp_replace(
            lower(col("expected_transcription")),
            r"[^\w\s]",
            ""
        )
    )
)

joined_df.select(
    "audio_file",
    "generated_normalized",
    "expected_normalized"
).show(truncate=False)

# ============================================================
# NORMALIZED COMPARISON AND RECORD-LEVEL QUALITY CHECK
# ============================================================

print("\nPerforming Normalized Comparison and Quality Checks...")

from pyspark.sql.functions import (
    size,
    split,
    abs,
    when
)

# ------------------------------------------------------------
# 1. Compare normalized transcriptions
# ------------------------------------------------------------

joined_df = joined_df.withColumn(
    "normalized_match",
    when(
        col("generated_normalized") == col("expected_normalized"),
        "MATCH"
    ).otherwise("MISMATCH")
)


# ------------------------------------------------------------
# 2. Calculate normalized word counts
# ------------------------------------------------------------

joined_df = joined_df.withColumn(
    "generated_normalized_word_count",
    size(
        split(
            col("generated_normalized"),
            " "
        )
    )
)

joined_df = joined_df.withColumn(
    "expected_normalized_word_count",
    size(
        split(
            col("expected_normalized"),
            " "
        )
    )
)


# ------------------------------------------------------------
# 3. Calculate normalized word-count difference
# ------------------------------------------------------------

joined_df = joined_df.withColumn(
    "normalized_word_count_difference",
    abs(
        col("generated_normalized_word_count")
        - col("expected_normalized_word_count")
    )
)


# ------------------------------------------------------------
# 4. Create record-level quality classification
# ------------------------------------------------------------

joined_df = joined_df.withColumn(
    "quality_status",
    when(
        col("normalized_match") == "MATCH",
        "PASS"
    ).otherwise("REVIEW")
)


# ------------------------------------------------------------
# 5. Inspect the complete validation output
# ------------------------------------------------------------

joined_df.select(
    "audio_file",
    "transcription_match",
    "normalized_match",
    "cleaned_word_count",
    "expected_word_count",
    "word_count_difference",
    "generated_normalized_word_count",
    "expected_normalized_word_count",
    "normalized_word_count_difference",
    "quality_status"
).show(truncate=False)

# ============================================================
# CREATE QUALITY REASON
# ============================================================

print("\nCreating Record-Level Quality Reason...")

joined_df = joined_df.withColumn(
    "quality_reason",
    when(
        col("normalized_match") == "MATCH",
        "TRANSCRIPTION_MATCH"
    ).when(
        col("normalized_word_count_difference") > 0,
        "WORD_COUNT_DIFFERENCE"
    ).otherwise(
        "TRANSCRIPTION_REVIEW"
    )
)


# ------------------------------------------------------------
# Inspect quality classification
# ------------------------------------------------------------

joined_df.select(
    "audio_file",
    "transcription_match",
    "normalized_match",
    "generated_normalized_word_count",
    "expected_normalized_word_count",
    "normalized_word_count_difference",
    "quality_status",
    "quality_reason"
).show(truncate=False)

# ============================================================
# GOLD QUALITY SUMMARY
# ============================================================

print("\nGenerating Gold Quality Summary...")

from pyspark.sql.functions import count, sum, round

# ------------------------------------------------------------
# 1. Overall quality summary
# ------------------------------------------------------------

quality_summary = joined_df.agg(
    count("*").alias("total_records"),

    sum(
        when(
            col("quality_status") == "PASS",
            1
        ).otherwise(0)
    ).alias("pass_count"),

    sum(
        when(
            col("quality_status") == "REVIEW",
            1
        ).otherwise(0)
    ).alias("review_count")
)

quality_summary = quality_summary.withColumn(
    "pass_percentage",
    round(
        col("pass_count") / col("total_records") * 100,
        2
    )
)

quality_summary = quality_summary.withColumn(
    "review_percentage",
    round(
        col("review_count") / col("total_records") * 100,
        2
    )
)

print("\nOverall Quality Summary:")
quality_summary.show()


# ------------------------------------------------------------
# 2. Quality reason breakdown
# ------------------------------------------------------------

quality_reason_summary = (
    joined_df
    .groupBy("quality_reason")
    .agg(
        count("*").alias("record_count")
    )
    .orderBy("quality_reason")
)

print("\nQuality Reason Breakdown:")
quality_reason_summary.show(truncate=False)

# ============================================================
# DUPLICATE DETECTION AND DEDUPLICATION
# ============================================================

print("\nChecking for Duplicate Audio Records...")

# ------------------------------------------------------------
# 1. Check total record count before deduplication
# ------------------------------------------------------------

before_dedup_count = joined_df.count()

print("Records before deduplication:", before_dedup_count)


# ------------------------------------------------------------
# 2. Identify duplicate audio files
# ------------------------------------------------------------

duplicate_records = (
    joined_df
    .groupBy("audio_id")
    .count()
    .filter(col("count") > 1)
    .orderBy("audio_id")
)

print("\nDuplicate Audio Files:")
duplicate_records.show(truncate=False)


# ------------------------------------------------------------
# 3. Remove duplicate records
# ------------------------------------------------------------

deduplicated_df = joined_df.dropDuplicates(
    ["audio_id"]
)


# ------------------------------------------------------------
# 4. Count records after deduplication
# ------------------------------------------------------------

after_dedup_count = deduplicated_df.count()

print(
    "\nRecords after deduplication:",
    after_dedup_count
)


# ------------------------------------------------------------
# 5. Calculate number of removed duplicates
# ------------------------------------------------------------

duplicates_removed = (
    before_dedup_count - after_dedup_count
)

print(
    "Duplicate records removed:",
    duplicates_removed
)


# ------------------------------------------------------------
# 6. Inspect deduplicated data
# ------------------------------------------------------------

print("\nDeduplicated Records:")

deduplicated_df.select(
    "audio_file",
    "batch_id",
    "transcription_match",
    "normalized_match",
    "quality_status",
    "quality_reason"
).show(truncate=False)


# ============================================================
# GOLD LAYER - FINAL BUSINESS OUTPUT
# ============================================================

print("\nCreating Gold Dataset...")

gold_df = joined_df.select(
    "audio_id",
    "audio_file",
    "transcription_clean",
    "expected_transcription",
    "transcription_match",
    "cleaned_word_count",
    "expected_word_count",
    "word_count_difference",
    "generated_normalized",
    "expected_normalized",
    "normalized_match",
    "generated_normalized_word_count",
    "expected_normalized_word_count",
    "normalized_word_count_difference",
    "quality_status",
    "quality_reason"
)

gold_df.show(truncate=False)

gold_record_count = gold_df.count()

print("Gold Record Count:", gold_record_count)

final_record_count = gold_record_count

print("Final Record Count:", final_record_count)
# ============================================================
# PIPELINE RUN COMPLETION
# ============================================================

run_end_time = datetime.now()
run_duration_seconds = (run_end_time - run_start_time).total_seconds()

print("\nPipeline End Time:", run_end_time)
print("Pipeline Duration (seconds):", run_duration_seconds)

run_status = "SUCCESS" if error_message is None else "FAILED"

print("Pipeline Run Status:", run_status)



audit_record = {
    "run_id": run_id,
    "run_start_time": run_start_time,
    "run_end_time": run_end_time,
    "run_duration_seconds": run_duration_seconds,
    "run_status": run_status,
    "bronze_record_count": bronze_record_count,
    "silver_record_count": silver_record_count,
    "joined_record_count": joined_record_count,
    "final_record_count": final_record_count
}

print("\nPipeline Audit Record:")
print(audit_record)

audit_df = spark.createDataFrame([audit_record])

print("\nAudit DataFrame:")
audit_df.show(truncate=False)

audit_df.write \
    .format("jdbc") \
    .option(
        "url",
        "jdbc:sqlserver://localhost:1433;databaseName=SpeechToTextDB;integratedSecurity=true;encrypt=true;trustServerCertificate=true"
    ) \
    .option("dbtable", "pipeline_audit") \
    .option(
        "driver",
        "com.microsoft.sqlserver.jdbc.SQLServerDriver"
    ) \
    .mode("append") \
    .save()

print("\nPipeline audit record written successfully to SQL Server.")
