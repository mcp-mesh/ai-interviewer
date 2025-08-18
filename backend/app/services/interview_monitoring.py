"""
Background interview monitoring service.
Handles expired session detection and finalization.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.redis_client import redis_client
from app.config import SESSION_PREFIX, INTERVIEW_TIMEOUT_SECONDS, LOCK_PREFIX, LOCK_TTL

logger = logging.getLogger(__name__)

class InterviewMonitoringService:
    """Handles background monitoring of interview sessions."""
    
    def __init__(self):
        self._timer_task: Optional[asyncio.Task] = None
    
    def is_session_expired(self, session_data: dict) -> bool:
        """Check if a session has expired based on start_time + duration."""
        try:
            start_time_str = session_data.get("start_time")
            duration = session_data.get("duration", INTERVIEW_TIMEOUT_SECONDS)  # fallback to old logic
            
            if not start_time_str:
                # Fallback to old logic for backward compatibility
                created_at_str = session_data.get("created_at")
                if not created_at_str:
                    return True
                start_time_str = created_at_str
                
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            elapsed_seconds = (now - start_time).total_seconds()
            
            return elapsed_seconds > duration
        except Exception as e:
            logger.error(f"Error checking session expiry: {e}")
            return True

    async def acquire_expire_lock(self, session_id: str) -> bool:
        """Acquire distributed lock for session expiry processing."""
        try:
            lock_key = f"{LOCK_PREFIX}{session_id}"
            return redis_client.set_with_nx_ex(lock_key, "locked", LOCK_TTL)
        except Exception as e:
            logger.error(f"Error acquiring expire lock for {session_id}: {e}")
            return False

    async def release_expire_lock(self, session_id: str) -> bool:
        """Release distributed lock for session expiry."""
        try:
            lock_key = f"{LOCK_PREFIX}{session_id}"
            return redis_client.delete(lock_key)
        except Exception as e:
            logger.error(f"Error releasing expire lock for {session_id}: {e}")
            return False

    async def finalize_all_pending_sessions(self) -> bool:
        """Finalize all pending sessions using batch API endpoint."""
        try:
            logger.info("Calling batch finalization API endpoint")
            
            from app.config import API_PORT
            import httpx
            
            # Call the batch finalize endpoint (no auth required)
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"http://localhost:{API_PORT}/api/interviews/finalize/batch")
                
                if response.status_code == 200:
                    result = response.json()
                    if result and result.get("success"):
                        finalized_count = result.get("finalized_count", 0)
                        total_processed = result.get("total_processed", 0)
                        logger.info(f"Batch finalization successful: {finalized_count}/{total_processed} sessions finalized")
                        return finalized_count > 0
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No response"
                        logger.error(f"Batch finalization failed: {error_msg}")
                        return False
                else:
                    logger.error(f"Batch API returned status {response.status_code}: {response.text}")
                    return False
                
        except Exception as e:
            logger.error(f"Error calling batch finalization API: {e}")
            return False

    def is_session_expired_by_expires_at(self, session_data: dict) -> bool:
        """Check if session expired based on expires_at timestamp."""
        try:
            expires_at = session_data.get("expires_at", 0)
            current_time = datetime.now().timestamp()
            return current_time >= expires_at
        except Exception as e:
            logger.error(f"Error checking session expiry by expires_at: {e}")
            return True

    async def monitor_expired_interviews(self):
        """Background task to finalize expired/ended interview sessions via batch API."""
        logger.info("Starting interview expiry monitor - using batch finalization API")
        
        while True:
            try:
                # Call the batch finalization API endpoint
                success = await self.finalize_all_pending_sessions()
                
                if success:
                    logger.debug("Batch finalization cycle completed successfully")
                else:
                    logger.debug("No sessions required finalization this cycle")
                    
            except Exception as e:
                logger.error(f"Error in interview monitor: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds

    async def start_monitor(self):
        """Start the background timer monitor task."""
        if self._timer_task is None or self._timer_task.done():
            logger.info("Starting background interview timer monitor")
            self._timer_task = asyncio.create_task(self.monitor_expired_interviews())
        else:
            logger.info("Background timer monitor already running")

    async def stop_monitor(self):
        """Stop the background timer monitor task."""
        if self._timer_task and not self._timer_task.done():
            logger.info("Shutting down timer monitor")
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass

# Global monitoring service instance
monitoring_service = InterviewMonitoringService()