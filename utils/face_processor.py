import logging
import os
import requests
import numpy as np
from config import FACE_IMAGES_DIR, FACE_RECOGNITION_THRESHOLD
from database import load_workers

logger = logging.getLogger('HydeParkSync.FaceProcessor')

# --- MOCK IMPLEMENTATION WARNING ---
# The actual face recognition libraries (dlib, face-recognition) are heavy and
# failed to compile in the current environment. This implementation uses MOCK
# functions for face detection and comparison.
# In a real deployment, these functions must be replaced with a robust
# implementation using the actual libraries.
# -----------------------------------

def _mock_get_face_encoding(image_path):
    """MOCK: Simulates getting a face encoding (a 128-dimension vector)."""
    logger.warning("MOCK: Generating a random face encoding for simulation.")
    # In a real scenario, this would use face_recognition.face_encodings(image)
    return np.random.rand(128)

def _mock_face_exists(image_path):
    """MOCK: Simulates face detection."""
    logger.warning("MOCK: Assuming face detection is successful.")
    # In a real scenario, this would use face_recognition.face_locations(image)
    return True

def download_image(url, worker_id):
    """Downloads the face image from the given URL."""
    if not url:
        logger.error(f"Worker {worker_id} has no face image URL.")
        return None
        
    image_path = os.path.join(FACE_IMAGES_DIR, f"{worker_id}.jpg")
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        with open(image_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded image for worker {worker_id} to {image_path}")
        return image_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download image from {url}: {e}")
        return None

def process_face_image(worker_data):
    """
    Handles face image processing: download, detection, and duplicate check.
    Returns True if the face is unique and processed, False otherwise.
    """
    worker_id = worker_data.get('id')
    image_url = worker_data.get('face_image_url')
    
    if not image_url:
        logger.warning(f"Worker {worker_id} has no face image URL. Skipping face processing.")
        return True # Allow processing if no face is required

    image_path = download_image(image_url, worker_id)
    if not image_path:
        return False

    if not _mock_face_exists(image_path):
        logger.error(f"No face detected in the image for worker {worker_id}.")
        os.remove(image_path)
        return False

    new_encoding = _mock_get_face_encoding(image_path)

    # Duplicate check using simple Euclidean distance on stored encodings
    workers = load_workers()
    for existing_worker_id, existing_worker in workers.items():
        existing_encoding = existing_worker.get('face_encoding')
        if existing_encoding is not None:
            try:
                existing_vec = np.array(existing_encoding)
                dist = float(np.linalg.norm(existing_vec - new_encoding))
                if dist < FACE_RECOGNITION_THRESHOLD:
                    logger.error(f"Duplicate face detected for worker {worker_id} (matches {existing_worker_id}). Distance={dist:.4f}")
                    os.remove(image_path)
                    return False
            except Exception as e:
                logger.warning(f"Failed face duplicate comparison for worker {worker_id}: {e}")

    # Save the new encoding (MOCK: saving as list)
    worker_data['face_encoding'] = new_encoding.tolist()
    return True

def delete_face_image(worker_id):
    """Deletes the face image file for a worker."""
    image_path = os.path.join(FACE_IMAGES_DIR, f"{worker_id}.jpg")
    if os.path.exists(image_path):
        os.remove(image_path)
        logger.info(f"Deleted face image for worker {worker_id}.")
        return True
    return False

def find_duplicate_by_face(image_url, worker_id):
    """Downloads face image and returns existing worker_id if duplicate face is found."""
    image_path = download_image(image_url, worker_id)
    if not image_path:
        return None
    try:
        new_encoding = _mock_get_face_encoding(image_path)
        workers = load_workers()
        for existing_worker_id, existing_worker in workers.items():
            existing_encoding = existing_worker.get('face_encoding')
            if existing_encoding is not None:
                try:
                    existing_vec = np.array(existing_encoding)
                    dist = float(np.linalg.norm(existing_vec - new_encoding))
                    if dist < FACE_RECOGNITION_THRESHOLD:
                        logger.info(f"Duplicate face match: input {worker_id} -> existing {existing_worker_id}")
                        return existing_worker_id
                except Exception:
                    continue
        return None
    finally:
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

def get_image_base64(image_url, worker_id):
    image_path = download_image(image_url, worker_id)
    if not image_path:
        return None
    try:
        with open(image_path, 'rb') as f:
            import base64
            return base64.b64encode(f.read()).decode('utf-8')
    finally:
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass
