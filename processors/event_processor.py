import logging
from api.supabase_client import SupabaseClient
from api.hikcentral_client import HikCentralClient
from database import load_workers, save_workers, add_or_update_worker, delete_worker
from utils.face_processor import process_face_image, delete_face_image, find_duplicate_by_face

logger = logging.getLogger('HydeParkSync.EventProcessor')

supabase_client = SupabaseClient()
hikcentral_client = HikCentralClient()

def handle_event(event):
    """
    Processes a single event fetched from Supabase.
    Event structure is expected to be:
    {
        "id": "event_uuid",
        "worker_id": 123,
        "action": "ADD" | "UPDATE" | "DELETE",
        "data": { ... worker data ... }
    }
    """
    event_id = event.get('id')
    worker_id = event.get('worker_id')
    action = event.get('action')
    worker_data = event.get('data', {})
    
    if not event_id or not worker_id or not action:
        logger.error(f"Invalid event structure received: {event}")
        supabase_client.fail_event(event_id, "Invalid event structure")
        return

    logger.info(f"Processing event {event_id} for worker {worker_id} with action: {action}")
    
    success = False
    error_reason = ""
    
    try:
        workers = load_workers()
        local_worker = workers.get(str(worker_id))
        
        if action == "ADD" or action == "UPDATE":
            # 1. Check for local worker data to determine if it's a new add or an update
            person_id = local_worker.get('hikcentral_person_id') if local_worker else None
            
            # 2. Process Face Image (Placeholder for Phase 6)
            # if not process_face_image(worker_data):
            #     error_reason = "Face image processing failed (e.g., no face detected or duplicate face found)"
            #     raise Exception(error_reason)

            # 3. Interact with HikCentral
            if person_id:
                # Update existing worker
                result = hikcentral_client.update_worker(person_id, worker_data)
                if result:
                    worker_data['hikcentral_person_id'] = person_id
                    success = True
            else:
                # Add new worker
                person_id = hikcentral_client.add_worker(worker_data)
                if person_id:
                    worker_data['hikcentral_person_id'] = person_id
                    success = True
            
            if success:
                # 4. Update local database
                add_or_update_worker(worker_data)
                logger.info(f"Successfully processed {action} for worker {worker_id}.")
            else:
                error_reason = "HikCentral API operation failed."
                raise Exception(error_reason)

        elif action == "DELETE":
            if local_worker and local_worker.get('hikcentral_person_id'):
                person_id = local_worker['hikcentral_person_id']
                # 1. Delete from HikCentral
                if hikcentral_client.delete_worker(person_id):
                    # 2. Delete from local database
                    delete_worker(worker_id)
                    success = True
                    logger.info(f"Successfully processed DELETE for worker {worker_id}.")
                else:
                    error_reason = "HikCentral API delete operation failed."
                    raise Exception(error_reason)
            else:
                # Worker not found locally, assume already deleted or ignore
                logger.warning(f"DELETE event for worker {worker_id} ignored. Worker not found locally.")
                success = True # Treat as success to complete the event

        else:
            error_reason = f"Unknown action type: {action}"
            raise ValueError(error_reason)

    except Exception as e:
        logger.error(f"Error processing event {event_id}: {e}")
        error_reason = str(e)
        success = False

    # 5. Report back to Supabase
    if success:
        supabase_client.complete_event(event_id)
    else:
        supabase_client.fail_event(event_id, error_reason)

def _normalize_worker_from_event(worker):
    return {
        "id": worker.get('id') or worker.get('nationalIdNumber'),
        "name": worker.get('fullName'),
        "national_id": worker.get('nationalIdNumber'),
        "face_image_url": worker.get('facePhoto'),
        "valid_from": worker.get('validFrom'),
        "valid_to": worker.get('validTo'),
        "status": worker.get('status'),
        "unit_number": worker.get('unitNumber'),
    }

def _workers_dict():
    try:
        return load_workers()
    except Exception:
        return {}

def _find_local_by_national_id(workers, national_id):
    if not national_id:
        return None, None
    for wid, w in workers.items():
        if str(w.get('national_id')) == str(national_id):
            return wid, w
    return None, None

def handle_worker_created(event_id, worker):
    success = False
    reason = ""
    workers = _workers_dict()
    new_w = _normalize_worker_from_event(worker)
    nid = new_w.get('national_id')

    existing_id, existing_w = _find_local_by_national_id(workers, nid)
    if not existing_w and new_w.get('face_image_url'):
        dup_id = find_duplicate_by_face(new_w['face_image_url'], new_w.get('id'))
        if dup_id:
            existing_id = dup_id
            existing_w = workers.get(str(dup_id))

    try:
        if not existing_w:
            person_id = hikcentral_client.add_worker(new_w)
            if person_id:
                new_w['hikcentral_person_id'] = person_id
                process_face_image(new_w)
                add_or_update_worker(new_w)
                success = True
            else:
                reason = "Failed to add worker to HikCentral"
        else:
            status = existing_w.get('status')
            if status == 'blocked':
                supabase_client.update_worker_status(nid, 'blocked', existing_w.get('hikcentral_person_id'), reason="Worker is blocked locally")
                success = True
            else:
                core_same = (
                    existing_w.get('name') == new_w.get('name') and
                    str(existing_w.get('national_id')) == str(new_w.get('national_id'))
                )
                valid_to = new_w.get('valid_to')
                person_id = existing_w.get('hikcentral_person_id')
                if core_same and valid_to and person_id:
                    if hikcentral_client.extend_worker_validity(person_id, valid_to):
                        existing_w['valid_to'] = valid_to
                        add_or_update_worker(existing_w)
                        success = True
                    else:
                        reason = "Failed to extend validity in HikCentral"
                else:
                    if person_id and hikcentral_client.update_worker(person_id, new_w):
                        if new_w.get('face_image_url'):
                            process_face_image(new_w)
                        new_w['hikcentral_person_id'] = person_id
                        add_or_update_worker(new_w)
                        success = True
                    else:
                        reason = "Failed to update worker in HikCentral"
    except Exception as e:
        reason = str(e)
        success = False

    if success:
        supabase_client.complete_event(event_id)
    else:
        supabase_client.fail_event(event_id, reason)

def poll_and_process_events():
    """
    The main polling function to be run by APScheduler.
    Fetches events and processes them sequentially.
    """
    logger.info("--- Starting Polling Cycle ---")
    
    events_response = supabase_client.get_pending_events()
    if isinstance(events_response, dict) and 'events' in events_response:
        events = events_response.get('events') or []
        logger.info(f"Received {len(events)} pending events.")
        for event in events:
            etype = event.get('type')
            if etype == 'worker.created':
                for w in event.get('workers') or []:
                    handle_worker_created(event.get('id'), w)
            elif etype == 'worker.deleted':
                for w in event.get('workers') or []:
                    wid, existing_w = _find_local_by_national_id(_workers_dict(), w.get('nationalIdNumber'))
                    if existing_w and existing_w.get('hikcentral_person_id'):
                        if hikcentral_client.delete_worker(existing_w['hikcentral_person_id']):
                            delete_worker(existing_w.get('id') or wid)
                            supabase_client.complete_event(event.get('id'))
                        else:
                            supabase_client.fail_event(event.get('id'), "Failed to delete worker in HikCentral")
                    else:
                        supabase_client.complete_event(event.get('id'))
            else:
                logger.warning(f"Unhandled event type: {etype}")
                supabase_client.complete_event(event.get('id'))
    elif events_response is not None:
        logger.error(f"Failed to fetch events from Supabase. Response: {events_response}")
        
    logger.info("--- Polling Cycle Finished ---")

# Example worker data structure (for reference)
# worker_data = {
#     "id": 123,
#     "name": "John Doe",
#     "national_id": "12345678901234",
#     "gender": "1",
#     "phone": "01000000000",
#     "email": "john@example.com",
#     "face_image_url": "http://example.com/face.jpg",
#     "hikcentral_person_id": "optional_hikcentral_id"
# }
