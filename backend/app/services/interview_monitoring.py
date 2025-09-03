"""
Background interview monitoring service.
Handles periodic finalization of completed interviews by calling the interview agent.
"""

import asyncio
import logging
from typing import Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class InterviewMonitoringService:
    """Handles background monitoring and finalization of interview sessions."""
    
    def __init__(self):
        self._monitor_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def finalize_all_pending_interviews(self) -> bool:
        """Finalize all pending interviews by calling the batch API endpoint."""
        try:
            logger.info("Calling batch finalization API endpoint")
            
            # Call the internal batch finalization endpoint
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post("http://localhost:8080/api/interviews/finalize/batch")
                
                if response.status_code != 200:
                    logger.error(f"Batch API returned status {response.status_code}: {response.text}")
                    return False
                
                result = response.json()
            
            if result and result.get("success"):
                processed_count = result.get("processed_count", 0)
                total_found = result.get("total_found", 0)
                lock_status = result.get("lock_status", "unknown")
                
                if processed_count > 0:
                    logger.info(f"Batch finalization successful: {processed_count}/{total_found} interviews finalized")
                    return True
                else:
                    if lock_status == "held_by_another_instance":
                        logger.debug("Finalization skipped - another instance is processing")
                    else:
                        logger.debug(f"No interviews required finalization - {result.get('message', 'No message')}")
                    return False
            else:
                error_msg = result.get("error", "Unknown error") if result else "No response from interview agent"
                logger.error(f"Interview agent finalization failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error calling interview agent finalization: {e}")
            return False
    
    async def monitor_interview_finalization(self):
        """Background task to periodically finalize completed interviews."""
        logger.info("Starting interview finalization monitor - calling interview agent every 30 seconds")
        
        while self._is_running:
            try:
                # Call the interview agent to finalize pending interviews
                success = await self.finalize_all_pending_interviews()
                
                if success:
                    logger.debug("Interview finalization cycle completed successfully")
                else:
                    logger.debug("No finalization needed this cycle")
                    
            except Exception as e:
                logger.error(f"Error in interview finalization monitor: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def start_monitor(self):
        """Start the background interview finalization monitor."""
        if self._monitor_task is None or self._monitor_task.done():
            logger.info("Starting background interview finalization monitor")
            self._is_running = True
            self._monitor_task = asyncio.create_task(self.monitor_interview_finalization())
        else:
            logger.info("Interview finalization monitor already running")
    
    async def stop_monitor(self):
        """Stop the background interview finalization monitor."""
        if self._monitor_task and not self._monitor_task.done():
            logger.info("Shutting down interview finalization monitor")
            self._is_running = False
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            finally:
                self._monitor_task = None

# Global monitoring service instance
monitoring_service = InterviewMonitoringService()