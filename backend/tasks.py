import os
import asyncio
from datetime import datetime, timezone
import logging
import tempfile
import shutil
import subprocess
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import zipfile

from celery_app import celery
from s3_utils import s3_client, S3_BUCKET_NAME, S3_REGION

# --- Task-specific setup ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# --- Helper function ---
def find_meshroom_output(output_dir: Path) -> Path:
    """Finds the main textured mesh file from Meshroom's output."""
    for item in (output_dir / "texturedMesh").glob("texturedMesh.*"):
        if item.suffix.lower() in ['.obj', '.fbx']:
            logging.info(f"Found Meshroom output model: {item}")
            return item
    raise FileNotFoundError(f"Could not find texturedMesh output in {output_dir}")

# --- The core async logic for the job ---
async def _process_photogrammetry_job_async(job_id: str, menu_item_id: str):
    """The actual async logic for processing, wrapped by the Celery task."""
    logging.info(f"Starting processing for job_id: {job_id}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        raw_zip_s3_key = f"raw-uploads/{job_id}.zip"
        local_zip_path = temp_path / f"{job_id}.zip"
        image_dir = temp_path / "images"
        output_dir = temp_path / "meshroom_output"
        image_dir.mkdir()
        output_dir.mkdir()

        try:
            # 1. Update job status to PROCESSING
            await db.photogrammetry_jobs.update_one(
                {"id": job_id}, {"$set": {"status": "PROCESSING"}}
            )
            logging.info(f"Job {job_id} status updated to PROCESSING.")

            # 2. Download the zip file from S3
            if not s3_client or not S3_BUCKET_NAME:
                raise Exception("S3 client is not configured on the worker. Check environment variables.")

            logging.info(f"Downloading {raw_zip_s3_key} from S3 to {local_zip_path}")
            s3_client.download_file(S3_BUCKET_NAME, raw_zip_s3_key, str(local_zip_path))

            # 3. Unzip the file and validate image count
            logging.info(f"Unzipping {local_zip_path} to {image_dir}")
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(image_dir)

            image_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(image_extensions)]
            if len(image_files) < 5:
                raise Exception(f"Insufficient images. Found {len(image_files)}, requires at least 5.")

            # 4. Execute the Meshroom CLI command
            meshroom_cmd = ["meshroom_batch", "--input", str(image_dir), "--output", str(output_dir)]
            logging.info(f"Running Meshroom command: {' '.join(meshroom_cmd)}")
            subprocess.run(meshroom_cmd, capture_output=True, text=True, check=True, timeout=1800)
            logging.info(f"Meshroom processing completed successfully for job {job_id}.")

            # 5. Find the output .obj file
            obj_path = find_meshroom_output(output_dir)
            optimized_glb_path = obj_path.with_suffix(".glb")

            # 6. Convert and optimize the model to GLB using gltf-pipeline
            gltf_cmd = [
                "gltf-pipeline", "-i", str(obj_path), "-o", str(optimized_glb_path),
                "--draco.compressionLevel=10"
            ]
            logging.info(f"Running gltf-pipeline command: {' '.join(gltf_cmd)}")
            subprocess.run(gltf_cmd, capture_output=True, text=True, check=True, timeout=300)
            logging.info(f"gltf-pipeline conversion completed successfully for job {job_id}.")

            # 7. Upload the final .glb model to S3
            final_model_s3_key = f"processed-models/{menu_item_id}.glb"
            logging.info(f"Uploading optimized model {optimized_glb_path} to S3 at {final_model_s3_key}")
            s3_client.upload_file(str(optimized_glb_path), S3_BUCKET_NAME, final_model_s3_key, ExtraArgs={'ContentType': 'model/gltf-binary'})
            final_model_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{final_model_s3_key}"

            # 8. Update menu item with the final model URL
            await db.menu_items.update_one(
                {"id": menu_item_id}, {"$set": {"model_url": final_model_url}}
            )
            logging.info(f"Menu item {menu_item_id} updated with model URL: {final_model_url}")

            # 9. Update job status to COMPLETED
            await db.photogrammetry_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "COMPLETED", "completed_at": datetime.now(timezone.utc).isoformat()}}
            )
            logging.info(f"Job {job_id} status updated to COMPLETED.")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            error_message = f"Processing command failed. Stderr: {e.stderr or 'N/A'}"
            logging.error(error_message)
            await db.photogrammetry_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "FAILED", "error_message": error_message, "completed_at": datetime.now(timezone.utc).isoformat()}}
            )
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            logging.error(f"Error processing job {job_id}: {error_message}", exc_info=True)
            await db.photogrammetry_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "FAILED", "error_message": error_message, "completed_at": datetime.now(timezone.utc).isoformat()}}
            )
        finally:
            logging.info(f"Finished processing for job_id: {job_id}. Temporary files cleaned up.")

# --- Celery Task Definition ---
@celery.task(name="process_photogrammetry_job")
def process_photogrammetry_job(job_id: str, menu_item_id: str):
    """Celery task to process a photogrammetry job. Wraps the async logic."""
    asyncio.run(_process_photogrammetry_job_async(job_id, menu_item_id))