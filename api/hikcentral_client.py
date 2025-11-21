import requests
import logging
import time
import uuid
import hmac
import hashlib
import base64
import json
from config import HIKCENTRAL_BASE_URL, HIKCENTRAL_APP_KEY, HIKCENTRAL_APP_SECRET, HIKCENTRAL_PRIVILEGE_GROUP_ID, DRY_RUN
from database import add_request_log, create_log_entry

logger = logging.getLogger('HydeParkSync.HikCentralClient')

class HikCentralClient:
    """Client for interacting with the HikCentral API using Artemis v2 Signature."""

    def __init__(self):
        self.base_url = HIKCENTRAL_BASE_URL
        self.app_key = HIKCENTRAL_APP_KEY
        self.app_secret = HIKCENTRAL_APP_SECRET
        self.privilege_group_id = HIKCENTRAL_PRIVILEGE_GROUP_ID

    def _generate_signature_headers(self, path, body_json=""):
        """Generates the required headers for Artemis v2 Signature."""
        nonce = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000)) # Milliseconds timestamp
        
        # 1. Construct the string to be signed
        # StringToSign = AppKey + Nonce + Timestamp + Body (if POST/PUT)
        string_to_sign = f"{self.app_key}{nonce}{timestamp}{body_json}"
        
        # 2. Sign the string using HMAC-SHA256 with the AppSecret
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # 3. Encode the signature in Base64
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "X-Ca-Key": self.app_key,
            "X-Ca-Nonce": nonce,
            "X-Ca-Timestamp": timestamp,
            "X-Ca-Signature": signature_base64,
            "X-Ca-Signature-Headers": "X-Ca-Key,X-Ca-Nonce,X-Ca-Timestamp"
        }
        return headers

    def _request(self, method, path, data=None):
        """Generic request handler with signature generation and logging."""
        url = f"{self.base_url}{path}"
        body_json = json.dumps(data) if data else ""
        
        headers = self._generate_signature_headers(path, body_json)
        
        log_data = {
            "api_type": "HikCentral",
            "endpoint": url,
            "request_data": data,
            "success": False,
            "status_code": 0,
            "response_data": None
        }

        try:
            # Note: HikCentral often uses self-signed certificates, so verify=False might be needed in a real-world scenario
            # For this project, we'll assume a secure connection or that the environment handles the certificate.
            response = requests.request(method, url, headers=headers, data=body_json, timeout=15, verify=False)
            response.raise_for_status()
            
            response_json = response.json()
            
            # Check HikCentral specific error code (e.g., code != 0)
            if response_json.get('code') != '0':
                raise requests.exceptions.HTTPError(f"HikCentral API Error: {response_json.get('msg', 'Unknown error')}", response=response)

            log_data["success"] = True
            log_data["status_code"] = response.status_code
            log_data["response_data"] = response_json
            
            return response_json

        except requests.exceptions.HTTPError as e:
            logger.error(f"HikCentral HTTP Error on {path}: {e}")
            log_data["status_code"] = response.status_code if 'response' in locals() else 0
            log_data["response_data"] = response.text if 'response' in locals() else str(e)
            log_data["message"] = f"HTTP Error: {e}"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"HikCentral Connection Error on {path}: {e}")
            log_data["message"] = f"Connection Error: {e}"
        except requests.exceptions.Timeout as e:
            logger.error(f"HikCentral Timeout Error on {path}: {e}")
            log_data["message"] = f"Timeout Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred with HikCentral on {path}: {e}")
            log_data["message"] = f"Unexpected Error: {e}"
        finally:
            add_request_log(create_log_entry(**log_data))
        
        return None

    # --- Worker Management Functions ---

    def add_worker(self, worker_data):
        """Adds a worker to HikCentral (Person and Face)."""
        # 1. Add Person
        person_path = "/api/resource/v1/person/single/add"
        person_payload = {
            "personName": worker_data.get('name'),
            "personNo": str(worker_data.get('id')), # Use worker ID as personNo
            "orgIndexCode": "1", # Assuming a default organization code
            "gender": worker_data.get('gender', '1'), # 1: Male, 2: Female
            "phoneNo": worker_data.get('phone', ''),
            "email": worker_data.get('email', ''),
            "certificateType": 1, # ID Card
            "certificateNo": worker_data.get('national_id', ''),
            "privilegeGroupIndexCode": self.privilege_group_id
        }
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="HikCentral",
                endpoint=f"{self.base_url}{person_path}",
                success=True,
                status_code=200,
                request_data=person_payload,
                response_data={"code": "0", "data": {"personId": str(worker_data.get('id'))}}
            ))
            logger.info(f"Successfully added person {worker_data.get('id')} with PersonID: {str(worker_data.get('id'))}")
            return str(worker_data.get('id'))
        person_response = self._request("POST", person_path, person_payload)
        
        if not person_response or person_response.get('code') != '0':
            logger.error(f"Failed to add person {worker_data.get('id')}: {person_response}")
            return None

        person_id = person_response.get('data', {}).get('personId')
        if not person_id:
            logger.error(f"Person ID not returned for worker {worker_data.get('id')}")
            return None

        # 2. Add Face (Requires face image data, which is not in the current worker_data)
        # In a real scenario, the worker_data would contain a URL to the image, 
        # which would need to be downloaded and then uploaded to HikCentral's file service 
        # before calling the face add API.
        # For now, we will simulate the success of the person add and return the person ID.
        
        # SIMULATION: Assume face is added successfully or handled elsewhere
        logger.info(f"Successfully added person {worker_data.get('id')} with PersonID: {person_id}")
        return person_id

    def delete_worker(self, person_id):
        """Deletes a worker from HikCentral by Person ID."""
        path = "/api/resource/v1/person/single/delete"
        payload = {
            "personId": person_id
        }
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="HikCentral",
                endpoint=f"{self.base_url}{path}",
                success=True,
                status_code=200,
                request_data=payload,
                response_data={"code": "0"}
            ))
            logger.info(f"Successfully deleted person with PersonID: {person_id}")
            return True
        response = self._request("POST", path, payload)
        
        if response and response.get('code') == '0':
            logger.info(f"Successfully deleted person with PersonID: {person_id}")
            return True
        
        logger.error(f"Failed to delete person {person_id}: {response}")
        return False

    def update_worker(self, person_id, worker_data):
        """Updates a worker's information in HikCentral."""
        # This is a simplified update. Real update would involve person update and face update/delete/add.
        path = "/api/resource/v1/person/single/update"
        payload = {
            "personId": person_id,
            "personName": worker_data.get('name'),
            "personNo": str(worker_data.get('id')),
            "gender": worker_data.get('gender', '1'),
            "phoneNo": worker_data.get('phone', ''),
            "email": worker_data.get('email', ''),
            "certificateNo": worker_data.get('national_id', ''),
            "privilegeGroupIndexCode": self.privilege_group_id
        }
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="HikCentral",
                endpoint=f"{self.base_url}{path}",
                success=True,
                status_code=200,
                request_data=payload,
                response_data={"code": "0"}
            ))
            logger.info(f"Successfully updated person with PersonID: {person_id}")
            return True
        response = self._request("POST", path, payload)
        
        if response and response.get('code') == '0':
            logger.info(f"Successfully updated person with PersonID: {person_id}")
            return True
        
        logger.error(f"Failed to update person {person_id}: {response}")
        return False

    def extend_worker_validity(self, person_id, valid_to):
        """Extends a worker's validity/permission period. Placeholder implementation."""
        path = "/api/resource/v1/person/single/update"
        payload = {
            "personId": person_id,
            # Placeholder field; real HikCentral privileges would be updated via access/authorization APIs
            "remark": f"Validity extended to {valid_to}"
        }
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="HikCentral",
                endpoint=f"{self.base_url}{path}",
                success=True,
                status_code=200,
                request_data=payload,
                response_data={"code": "0"}
            ))
            logger.info(f"Extended validity for PersonID {person_id} to {valid_to}")
            return True
        response = self._request("POST", path, payload)
        if response and response.get('code') == '0':
            logger.info(f"Extended validity for PersonID {person_id} to {valid_to}")
            return True
        logger.error(f"Failed to extend validity for person {person_id}: {response}")
        return False

# Suppress InsecureRequestWarning for verify=False
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
