import requests
import logging
from config import SUPABASE_BASE_URL, SUPABASE_API_KEY, SUPABASE_EVENTS_ENDPOINT, SUPABASE_COMPLETE_ENDPOINT, SUPABASE_FAIL_ENDPOINT, DRY_RUN, SUPABASE_UPDATE_STATUS_ENDPOINT
from database import add_request_log, create_log_entry

logger = logging.getLogger('HydeParkSync.SupabaseClient')

class SupabaseClient:
    """Client for interacting with the Supabase Edge Function API."""

    def __init__(self):
        self.base_url = SUPABASE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

    def _request(self, method, endpoint, data=None):
        """Generic request handler with logging."""
        url = f"{self.base_url}{endpoint}"
        log_data = {
            "api_type": "Supabase",
            "endpoint": url,
            "request_data": data,
            "success": False,
            "status_code": 0,
            "response_data": None
        }

        try:
            response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
            response.raise_for_status()
            
            log_data["success"] = True
            log_data["status_code"] = response.status_code
            log_data["response_data"] = response.json()
            
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"Supabase HTTP Error on {endpoint}: {e}")
            log_data["status_code"] = response.status_code if 'response' in locals() else 0
            log_data["response_data"] = response.text if 'response' in locals() else str(e)
            log_data["message"] = f"HTTP Error: {e}"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Supabase Connection Error on {endpoint}: {e}")
            log_data["message"] = f"Connection Error: {e}"
        except requests.exceptions.Timeout as e:
            logger.error(f"Supabase Timeout Error on {endpoint}: {e}")
            log_data["message"] = f"Timeout Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred with Supabase on {endpoint}: {e}")
            log_data["message"] = f"Unexpected Error: {e}"
        finally:
            add_request_log(create_log_entry(**log_data))
        
        return None

    def get_pending_events(self):
        """Fetches pending events from Supabase."""
        logger.info("Fetching pending events from Supabase...")
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="Supabase",
                endpoint=f"{self.base_url}{SUPABASE_EVENTS_ENDPOINT}",
                success=True,
                status_code=200,
                request_data=None,
                response_data={"success": True, "events": []}
            ))
            return {"success": True, "events": []}
        resp = self._request("GET", SUPABASE_EVENTS_ENDPOINT)
        # Normalize to object with events array
        if isinstance(resp, list):
            return {"success": True, "events": resp}
        return resp

    def complete_event(self, event_id):
        """Marks an event as completed in Supabase."""
        endpoint = SUPABASE_COMPLETE_ENDPOINT.format(eventId=event_id)
        logger.info(f"Marking event {event_id} as complete.")
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="Supabase",
                endpoint=f"{self.base_url}{endpoint}",
                success=True,
                status_code=200,
                request_data=None,
                response_data={"status": "ok"}
            ))
            return {"status": "ok"}
        return self._request("POST", endpoint)

    def fail_event(self, event_id, reason="Processing failed"):
        """Marks an event as failed in Supabase."""
        endpoint = SUPABASE_FAIL_ENDPOINT.format(eventId=event_id)
        logger.warning(f"Marking event {event_id} as failed. Reason: {reason}")
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="Supabase",
                endpoint=f"{self.base_url}{endpoint}",
                success=True,
                status_code=200,
                request_data={"reason": reason},
                response_data={"status": "ok"}
            ))
            return {"status": "ok"}
        return self._request("POST", endpoint, data={"reason": reason})

    def update_worker_status(self, national_id_number, status, external_id=None, reason=""):
        """Updates worker status back on Supabase external system API."""
        endpoint = SUPABASE_UPDATE_STATUS_ENDPOINT
        payload = {
            "nationalIdNumber": national_id_number,
            "status": status,
            "externalId": external_id,
            "reason": reason,
        }
        logger.info(f"Updating worker status on Supabase: {national_id_number} -> {status}")
        if DRY_RUN:
            add_request_log(create_log_entry(
                api_type="Supabase",
                endpoint=f"{self.base_url}{endpoint}",
                success=True,
                status_code=200,
                request_data=payload,
                response_data={"success": True}
            ))
            return {"success": True}
        # Use API key header; same header works here
        return self._request("POST", endpoint, data=payload)

# Example usage (for testing, will be removed later)
if __name__ == '__main__':
    client = SupabaseClient()
    # Test fetching events (requires a running Supabase instance and valid key)
    # events = client.get_pending_events()
    # print(events)
    pass
