import os
import sys
import json
import subprocess
import logging
import hashlib
from datetime import datetime

import onnx_asr


# --------------------------------------------------
# Step 1: Configure logging
# --------------------------------------------------

log_dir = "logs"

os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, "pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
#------------------------------------------------------
# converting different sterio audio to mono audio
#------------------------------------------------------

def normalize_audio_to_mono(input_file):
    """
    Convert the input audio to a temporary mono WAV file
    suitable for Whisper/onnx_asr processing.

    The original input file is never modified.
    """

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_file = os.path.join(
        "data",
        f"{base_name}_normalized.wav"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-ac", "1",
        "-ar", "16000",
        temp_file
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return temp_file
# --------------------------------------------------
# Generate stable SHA-256 audio ID
# --------------------------------------------------

def generate_audio_id(input_file):
    """
    Generate a stable SHA-256 ID from the original audio file content.

    The original audio file is hashed before any normalization.
    """

    sha256 = hashlib.sha256()

    with open(input_file, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()

# --------------------------------------------------
# Step 2: Validate command-line argument
# --------------------------------------------------

input_path = "data/incoming"

supported_extensions = [
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a"
]


# --------------------------------------------------
# Step 3: Identify input as file or directory
# --------------------------------------------------

if os.path.isfile(input_path):

    file_extension = os.path.splitext(input_path)[1].lower()

    if file_extension not in supported_extensions:

        print(
            f"Error: Unsupported audio format: {file_extension}"
        )

        print(
            f"Supported formats: {', '.join(supported_extensions)}"
        )

        logger.error(
            f"Unsupported audio format: {file_extension}"
        )

        sys.exit(1)

    audio_files = [input_path]


elif os.path.isdir(input_path):

    audio_files = []

    for filename in os.listdir(input_path):

        file_path = os.path.join(
            input_path,
            filename
        )

        if os.path.isfile(file_path):

            file_extension = os.path.splitext(
                filename
            )[1].lower()

            if file_extension in supported_extensions:

                audio_files.append(file_path)

    if not audio_files:

        print(
            f"Error: No supported audio files found in: {input_path}"
        )

        print(
            f"Supported formats: {', '.join(supported_extensions)}"
        )

        logger.error(
            f"No supported audio files found in: {input_path}"
        )

        sys.exit(1)


else:

    print(
        f"Error: Input path not found: {input_path}"
    )

    logger.error(
        f"Input path not found: {input_path}"
    )

    sys.exit(1)


# --------------------------------------------------
# Step 4: Display discovered files
# --------------------------------------------------

print(
    f"Found {len(audio_files)} audio file(s):"
)

logger.info(
    f"Found {len(audio_files)} audio file(s)"
)

for audio_file in audio_files:

    print(f" - {audio_file}")

    logger.info(
        f"Discovered audio file: {audio_file}"
    )


# --------------------------------------------------
# Step 5: Prepare output directory
# --------------------------------------------------

output_dir = "output"
processed_dir = "data/processed"
failed_dir = "data/failed"

os.makedirs(
    output_dir,
    exist_ok=True
)

os.makedirs(
    processed_dir,
    exist_ok=True
)

os.makedirs(
    failed_dir,
    exist_ok=True
)


# --------------------------------------------------
# Step 6: Initialize processing counters
# --------------------------------------------------

success_count = 0
failure_count = 0
skipped_count = 0

batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

pipeline_version = "1.0"
source = "local_audio"

audit_records = []


# Load existing audit history if available

audit_file = os.path.join(
    output_dir,
    "processing_audit.json"
)

if os.path.isfile(audit_file):

    try:

        with open(
            audit_file,
            "r",
            encoding="utf-8"
        ) as file:

            audit_records = json.load(file)

    except (json.JSONDecodeError, OSError) as error:

        logger.warning(
            f"Could not load existing audit history: {error}"
        )


logger.info(
    "Batch processing started"
)


# --------------------------------------------------
# Step 7: Process each audio file
# --------------------------------------------------

for audio_file in audio_files:

    print(
        f"\nProcessing: {audio_file}"
    )

    # Generate stable ID from ORIGINAL audio file
    audio_id = generate_audio_id(audio_file)

    logger.info(
        f"Generated audio_id for {audio_file}: {audio_id}"
    )

    logger.info(
        f"Processing file: {audio_file}"
    )

    # ----------------------------------------------
    # Bronze metadata - file information
    # ----------------------------------------------

    ingestion_timestamp = datetime.now().isoformat()

    file_size_bytes = os.path.getsize(audio_file)

    file_type = os.path.splitext(
        os.path.basename(audio_file)
    )[1].lower().replace(".", "")

    processing_start_time = datetime.now()

    processed_at = ingestion_timestamp


    # ----------------------------------------------
    # Create base filename
    # ----------------------------------------------

    base_name = os.path.splitext(
        os.path.basename(audio_file)
    )[0]

    json_file = os.path.join(
        output_dir,
        f"{base_name}.json"
    )


    # ----------------------------------------------
    # Step 15: Idempotency check
    # ----------------------------------------------

    if os.path.isfile(json_file):

        try:

            with open(
                json_file,
                "r",
                encoding="utf-8"
            ) as file:

                existing_output = json.load(file)


            if (
    		existing_output.get("status") == "success"
    		and existing_output.get("audio_id")
		):

                skipped_count += 1

                print(
                    "Status: SKIPPED (already processed)"
                )

                logger.info(
                    f"Skipped already processed file: {audio_file}"
                )

                audit_records.append({
                    "audio_file": os.path.basename(audio_file),
                    "status": "skipped",
                    "batch_id": batch_id,
                    "processed_at": processed_at,
                    "reason": "Already successfully processed"
                })

                continue


        except (json.JSONDecodeError, OSError) as error:

            logger.warning(
                f"Could not validate existing output for "
                f"{audio_file}: {error}"
            )


    try:

        # ------------------------------------------
        # Transcribe audio
        # ------------------------------------------

        print("Transcribing...")

        # Load model only when actual processing is needed.
        # Model is loaded once and reused for files that
        # are not skipped.

        if "model" not in locals():

            print("Loading Whisper Base model...")

            logger.info(
                "Loading Whisper Base model"
            )

            model = onnx_asr.load_model(
                "whisper-base",
                providers=["CPUExecutionProvider"]
            )

            print("Model loaded successfully.")

            logger.info(
                "Whisper Base model loaded successfully"
            )


        temp_audio_file = None

        try:
            # Normalize audio for Whisper
            temp_audio_file = normalize_audio_to_mono(audio_file)

            # Transcribe normalized audio
            result = model.recognize(
                temp_audio_file,
                language="en"
            )

        finally:
            # Always remove temporary normalized audio
            if temp_audio_file and os.path.exists(temp_audio_file):
                os.remove(temp_audio_file)
        processing_timestamp = datetime.now().isoformat()

        processing_duration_seconds = round(
            (
                datetime.fromisoformat(processing_timestamp)
                - processing_start_time
            ).total_seconds(),
            2
        )


        # ------------------------------------------
        # Step 13: Data Quality Validation
        # ------------------------------------------

        if not result or not result.strip():

            failure_count += 1

            print("Status: FAILED")

            print(
                "Error: Transcription is empty."
            )

            logger.error(
                f"Data quality validation failed for {audio_file}: "
                "empty transcription"
            )

            # --------------------------------------
            # Create Bronze JSON for failed record
            # --------------------------------------

            output_data = {
                "audio_id": audio_id,
		"audio_file": os.path.basename(audio_file),
                "source": source,
                "file_type": file_type,
                "file_size_bytes": file_size_bytes,
                "batch_id": batch_id,
                "ingestion_timestamp": ingestion_timestamp,
                "processing_timestamp": processing_timestamp,
                "model": "whisper-base",
                "language": "en",
                "status": "failed",
                "processing_duration_seconds": processing_duration_seconds,
                "transcription": None,
                "transcription_length": 0,
                "word_count": 0,
                "error": "Transcription is empty.",
                "error_type": "EmptyTranscription",
                "pipeline_version": pipeline_version
            }

            with open(
                json_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    output_data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )


            audit_records.append({
                "audio_id": audio_id,
		"audio_file": os.path.basename(audio_file),
                "status": "failed",
                "processed_at": processed_at,
                "batch_id": batch_id,
                "error": "Transcription is empty."
            })


            # ------------------------------------------
            # Move failed audio file
            # ------------------------------------------

            failed_file = os.path.join(
                failed_dir,
                os.path.basename(audio_file)
            )

            os.rename(
                audio_file,
                failed_file
            )

            logger.info(
                f"Moved failed audio file to: {failed_file}"
            )


            continue


        # ------------------------------------------
        # Bronze transcription metrics
        # ------------------------------------------

        transcription_length = len(result)

        word_count = len(result.split())


        # ------------------------------------------
        # Save TXT output
        # ------------------------------------------

        output_file = os.path.join(
            output_dir,
            f"{base_name}.txt"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(result)


        # ------------------------------------------
        # Save Bronze JSON output
        # ------------------------------------------

        output_data = {
	    "audio_id": audio_id,	
            "audio_filename": os.path.basename(audio_file),
            "source": source,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "batch_id": batch_id,
            "ingestion_timestamp": ingestion_timestamp,
            "processing_timestamp": processing_timestamp,
            "model": "whisper-base",
            "language": "en",
            "status": "success",
            "processing_duration_seconds": processing_duration_seconds,
            "transcription": result,
            "transcription_length": transcription_length,
            "word_count": word_count,
            "error": None,
            "error_type": None,
            "pipeline_version": pipeline_version
        }

        with open(
            json_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        # ------------------------------------------
        # Move successfully processed audio file
        # ------------------------------------------

        processed_file = os.path.join(
            processed_dir,
            os.path.basename(audio_file)
        )

        os.rename(
            audio_file,
            processed_file
        )

        logger.info(
            f"Moved processed audio file to: {processed_file}"
        )


        # ------------------------------------------
        # Success handling
        # ------------------------------------------

        success_count += 1

        print("Status: SUCCESS")

        print("Transcription:")
        print(result)

        print(
            f"Saved transcription to: {output_file}"
        )

        print(
            f"Saved structured output to: {json_file}"
        )

        logger.info(
            f"Successfully processed: {audio_file}"
        )

        logger.info(
            f"Saved TXT output: {output_file}"
        )

        logger.info(
            f"Saved JSON output: {json_file}"
        )


        # ------------------------------------------
        # Add successful audit record
        # ------------------------------------------

        audit_records.append({
            "audio_file": os.path.basename(audio_file),
            "status": "success",
            "batch_id": batch_id,
            "processed_at": processed_at,
            "transcription": result
        })


    except Exception as error:

        failure_count += 1

        processing_timestamp = datetime.now().isoformat()

        processing_duration_seconds = round(
            (
                datetime.fromisoformat(processing_timestamp)
                - processing_start_time
            ).total_seconds(),
            2
        )

        print("Status: FAILED")

        print(
            f"Error processing {audio_file}: {error}"
        )

        logger.error(
            f"Error processing {audio_file}: {error}"
        )


        # ------------------------------------------
        # Create Bronze JSON for processing failure
        # ------------------------------------------

        output_data = {
            "audio_file": os.path.basename(audio_file),
            "source": source,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "batch_id": batch_id,
            "ingestion_timestamp": ingestion_timestamp,
            "processing_timestamp": processing_timestamp,
            "model": "whisper-base",
            "language": "en",
            "status": "failed",
            "processing_duration_seconds": processing_duration_seconds,
            "transcription": None,
            "transcription_length": 0,
            "word_count": 0,
            "error": str(error),
            "error_type": type(error).__name__,
            "pipeline_version": pipeline_version
        }

        with open(
            json_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output_data,
                file,
                indent=4,
                ensure_ascii=False
            )


        audit_records.append({
            "audio_file": os.path.basename(audio_file),
            "status": "failed",
            "processed_at": processed_at,
            "batch_id": batch_id,
            "error": str(error),
            "error_type": type(error).__name__
        })


        # ------------------------------------------
        # Move failed audio file
        # ------------------------------------------

        failed_file = os.path.join(
            failed_dir,
            os.path.basename(audio_file)
        )

        os.rename(
            audio_file,
            failed_file
        )

        logger.info(
            f"Moved failed audio file to: {failed_file}"
        )

        continue


# --------------------------------------------------
# Step 8: Save batch processing audit record
# --------------------------------------------------

audit_file = os.path.join(
    output_dir,
    "processing_audit.json"
)

with open(
    audit_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        audit_records,
        file,
        indent=4,
        ensure_ascii=False
    )


logger.info(
    f"Saved processing audit record: {audit_file}"
)


# --------------------------------------------------
# Step 9: Batch processing summary
# --------------------------------------------------

print(
    "\n========== BATCH SUMMARY =========="
)

print(
    f"Total files     : {len(audio_files)}"
)

print(
    f"Successful      : {success_count}"
)

print(
    f"Failed          : {failure_count}"
)

print(
    f"Skipped         : {skipped_count}"
)

print(
    "===================================="
)

print(
    f"Audit record saved to: {audit_file}"
)

print(
    "Batch processing completed."
)


logger.info(
    "========== BATCH SUMMARY =========="
)

logger.info(
    f"Total files: {len(audio_files)}"
)

logger.info(
    f"Successful: {success_count}"
)

logger.info(
    f"Failed: {failure_count}"
)

logger.info(
    f"Skipped: {skipped_count}"
)

logger.info(
    "Batch processing completed"
)