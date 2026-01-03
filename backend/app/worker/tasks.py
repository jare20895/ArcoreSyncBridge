from app.services.run_history import RunHistoryService

logger = get_task_logger(__name__)

@celery_app.task(bind=True)
def run_push_sync(self, sync_def_id: str):
    logger.info(f"Starting push sync for definition {sync_def_id}")
    
    db = SessionLocal()
    run = None
    try:
        sync_def = db.get(SyncDefinition, UUID(sync_def_id))
        if not sync_def:
            logger.error(f"Sync definition {sync_def_id} not found")
            return "Failed: Definition not found"
            
        logger.info(f"Syncing '{sync_def.name}' (Mode: {sync_def.sync_mode})")
        
        history_service = RunHistoryService(db)
        run = history_service.start_run(sync_def.id, "PUSH")
        
        pusher = Pusher(db)
        result = pusher.run_push(sync_def.id)
        
        logger.info(f"Push sync for {sync_def_id} completed successfully: {result}")
        history_service.end_run(run.id, "COMPLETED", items_processed=result.get("processed_count", 0))
        return f"Success: {result}"
        
    except Exception as e:
        logger.exception(f"Sync failed: {str(e)}")
        if run:
            history_service.end_run(run.id, "FAILED", error_message=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()

@celery_app.task(bind=True)
def run_ingress_sync(self, sync_def_id: str):
    logger.info(f"Starting ingress sync for definition {sync_def_id}")
    
    db = SessionLocal()
    run = None
    try:
        sync_def = db.get(SyncDefinition, UUID(sync_def_id))
        if not sync_def:
            logger.error(f"Sync definition {sync_def_id} not found")
            return "Failed: Definition not found"
        
        if sync_def.sync_mode != "TWO_WAY":
             logger.warning(f"Skipping ingress for '{sync_def.name}' (Mode: {sync_def.sync_mode})")
             return "Skipped: Not TWO_WAY"
            
        logger.info(f"Ingesting '{sync_def.name}'")
        
        history_service = RunHistoryService(db)
        run = history_service.start_run(sync_def.id, "INGRESS")
        
        syncer = Synchronizer(db)
        result = syncer.run_ingress(sync_def.id)
        
        logger.info(f"Ingress sync for {sync_def_id} completed successfully: {result}")
        history_service.end_run(run.id, "COMPLETED", items_processed=result.get("processed_count", 0))
        return f"Success: {result}"
        
    except Exception as e:
        logger.exception(f"Ingress failed: {str(e)}")
        if run:
            history_service.end_run(run.id, "FAILED", error_message=str(e))
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
