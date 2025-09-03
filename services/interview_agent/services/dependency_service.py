"""
Dependency Service - Cross-Agent Communication Management

Handles MCP Mesh dependency injection and provides clean interfaces
for communicating with other agents in the system.
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from mesh.types import McpMeshAgent

logger = logging.getLogger(__name__)

class DependencyService:
    """
    Manages cross-agent dependencies and provides clean interfaces for MCP Mesh communication.
    """
    
    def __init__(self):
        """Initialize dependency service."""
        self.logger = logging.getLogger(__name__)
        self._dependencies = {}
    
    def register_dependencies(self, dependencies: Dict[str, McpMeshAgent]) -> None:
        """
        Register MCP Mesh dependencies for use in interview operations.
        
        Args:
            dependencies: Dictionary mapping capability names to injected functions
        """
        self._dependencies = dependencies
        capability_names = list(dependencies.keys())
        self.logger.info(f"Registered {len(capability_names)} dependencies: {capability_names}")
    
    async def get_user_applications(
        self,
        user_email: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user applications from application agent.
        
        Args:
            user_email: User's email address
            status_filter: Optional status filter
            
        Returns:
            List of user applications
            
        Raises:
            Exception: Application agent communication failed
        """
        try:
            user_applications_get = self._dependencies.get("user_applications_get")
            if not user_applications_get:
                raise Exception("user_applications_get dependency not available")
            
            result = await user_applications_get(user_email=user_email)
            
            # Extract applications from the response format
            if isinstance(result, dict) and result.get("success") and "applications" in result:
                applications = result["applications"]
            else:
                applications = result if isinstance(result, list) else []
            
            # Filter by status if requested
            if status_filter and isinstance(applications, list):
                applications = [app for app in applications if app.get("status") == status_filter]
            
            self.logger.info(f"Retrieved {len(applications)} applications for {user_email}")
            return applications
            
        except Exception as e:
            self.logger.error(f"Failed to get user applications for {user_email}: {e}")
            raise Exception(f"Application agent communication failed: {str(e)}")
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details from job agent.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job details dictionary
            
        Raises:
            Exception: Job agent communication failed
        """
        try:
            job_details_get = self._dependencies.get("job_details_get")
            if not job_details_get:
                raise Exception("job_details_get dependency not available")
            
            result = await job_details_get(job_id=job_id)
            
            if not isinstance(result, dict):
                raise Exception(f"Invalid job details format for {job_id}")
            
            self.logger.info(f"Retrieved job details for {job_id}: {result.get('title', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get job details for {job_id}: {e}")
            raise Exception(f"Job agent communication failed: {str(e)}")
    
    async def update_application_status(
        self,
        application_id: str,
        new_status: str
    ) -> bool:
        """
        Update application status via application agent.
        
        Args:
            application_id: Application identifier
            new_status: New status value
            
        Returns:
            bool: Success status
            
        Raises:
            Exception: Application agent communication failed
        """
        try:
            application_status_update = self._dependencies.get("application_status_update")
            if not application_status_update:
                raise Exception("application_status_update dependency not available")
            
            result = await application_status_update(
                application_id=application_id,
                new_status=new_status
            )
            
            success = isinstance(result, dict) and result.get("success", False)
            
            if success:
                self.logger.info(f"Updated application {application_id} status to {new_status}")
            else:
                self.logger.warning(f"Failed to update application {application_id} status")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update application status {application_id}: {e}")
            raise Exception(f"Application agent communication failed: {str(e)}")
    
    async def get_application_details(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed application information.
        
        Args:
            application_id: Application identifier
            
        Returns:
            Application details dictionary
            
        Raises:
            Exception: Application retrieval failed
        """
        try:
            # First try to get from application agent if available
            get_application = self._dependencies.get("get_application")
            if get_application:
                result = await get_application(application_id=application_id)
                if isinstance(result, dict):
                    self.logger.info(f"Retrieved application details for {application_id}")
                    return result
            
            # Fallback: Could implement alternative lookup methods here
            raise Exception(f"Application {application_id} not found")
            
        except Exception as e:
            self.logger.error(f"Failed to get application details {application_id}: {e}")
            raise Exception(f"Application retrieval failed: {str(e)}")
    
    async def validate_dependencies(self) -> Dict[str, bool]:
        """
        Validate all registered dependencies are available and callable.
        
        Returns:
            Dictionary mapping capability names to availability status
        """
        validation_results = {}
        
        required_capabilities = [
            "user_applications_get",
            "job_details_get", 
            "application_status_update"
        ]
        
        for capability in required_capabilities:
            is_available = capability in self._dependencies
            is_callable = callable(self._dependencies.get(capability))
            
            validation_results[capability] = is_available and is_callable
            
            status = "✓" if validation_results[capability] else "✗"
            self.logger.info(f"Dependency validation {capability}: {status}")
        
        # Check optional dependencies
        optional_capabilities = ["get_application"]
        for capability in optional_capabilities:
            if capability in self._dependencies:
                validation_results[capability] = callable(self._dependencies[capability])
                status = "✓" if validation_results[capability] else "✗"
                self.logger.info(f"Optional dependency {capability}: {status}")
        
        return validation_results
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """
        Get summary of registered dependencies.
        
        Returns:
            Summary dictionary with dependency information
        """
        registered_count = len(self._dependencies)
        capability_names = list(self._dependencies.keys())
        
        summary = {
            "total_registered": registered_count,
            "capabilities": capability_names,
            "status": "ready" if registered_count > 0 else "no_dependencies"
        }
        
        return summary
    
    async def test_cross_agent_communication(self) -> Dict[str, Any]:
        """
        Test communication with all registered agents.
        
        Returns:
            Test results dictionary
        """
        test_results = {
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": {}
        }
        
        try:
            # Test application agent for user applications
            if "user_applications_get" in self._dependencies:
                test_results["tests_run"] += 1
                try:
                    # Test with a non-existent user to avoid side effects
                    await self.get_user_applications("test@nonexistent.com")
                    test_results["tests_passed"] += 1
                    test_results["details"]["application_agent_user_apps"] = "✓ Available"
                except Exception as e:
                    test_results["tests_failed"] += 1
                    test_results["details"]["application_agent_user_apps"] = f"✗ Error: {str(e)}"
            
            # Test job agent
            if "job_details_get" in self._dependencies:
                test_results["tests_run"] += 1
                try:
                    # Test with a non-existent job to avoid side effects
                    await self.get_job_details("test-job-id")
                    test_results["tests_passed"] += 1
                    test_results["details"]["job_agent"] = "✓ Available"
                except Exception as e:
                    test_results["tests_failed"] += 1
                    test_results["details"]["job_agent"] = f"✗ Error: {str(e)}"
            
            # Test application agent
            if "application_status_update" in self._dependencies:
                test_results["tests_run"] += 1
                try:
                    # Test with invalid parameters to check connectivity
                    await self.update_application_status("test-app-id", "TEST_STATUS")
                    test_results["tests_passed"] += 1
                    test_results["details"]["application_agent"] = "✓ Available"
                except Exception as e:
                    test_results["tests_failed"] += 1
                    test_results["details"]["application_agent"] = f"✗ Error: {str(e)}"
            
            self.logger.info(f"Cross-agent communication test completed: {test_results['tests_passed']}/{test_results['tests_run']} passed")
            
        except Exception as e:
            self.logger.error(f"Cross-agent communication test failed: {e}")
            test_results["details"]["general_error"] = str(e)
        
        return test_results

# Global dependency service instance
dependency_service = DependencyService()