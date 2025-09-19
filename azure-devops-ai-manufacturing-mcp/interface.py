"""
Azure DevOps Multi-Platform MCP - Interface Contracts

This module defines the complete interface contracts for Azure DevOps, GitHub, and GitLab
integration operations following the Standardized Modules Framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .types import (
    OperationResult, WorkItemData, WorkItemUpdate, DevelopmentArtifacts,
    AzureDevOpsProjectStructure, TransitionResult, ArtifactResult, HealthStatus, DashboardData
)


class AzureDevOpsMultiPlatformInterface(ABC):
    """
    Complete interface contract for Azure DevOps Multi-Platform MCP module.

    This interface defines all operations required for multi-platform development
    workflows integrated with Azure DevOps, GitHub, and GitLab, including work item
    management, cross-platform synchronization, and artifact tracking.
    """
    
    # Core Project Analysis Operations
    @abstractmethod
    async def analyze_project_structure(self, organization: str, project: str) -> OperationResult:
        """
        Analyze Azure DevOps project structure including work item types, fields,
        process templates, and board configurations.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            
        Returns:
            OperationResult with AzureDevOpsProjectStructure data
        """
        pass
    
    @abstractmethod
    async def schedule_daily_configuration_validation(self, organization: str, project: str) -> OperationResult:
        """
        Schedule daily automated configuration validation for Azure DevOps project.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            
        Returns:
            OperationResult confirming scheduled validation
        """
        pass
    
    # Work Item Management Operations
    @abstractmethod
    async def create_work_item(self, work_item_data: WorkItemData) -> OperationResult:
        """
        Create work item with flexible field mapping for multi-platform support.

        Args:
            work_item_data: WorkItemData with all required fields

        Returns:
            OperationResult with created work item ID and details
        """
        pass

    @abstractmethod
    async def bulk_create_work_items(self, work_items: List[WorkItemData]) -> OperationResult:
        """
        Create multiple work items in batch for performance.

        Args:
            work_items: List of WorkItemData objects

        Returns:
            OperationResult with batch creation results
        """
        pass

    @abstractmethod
    async def update_work_item(self, work_item_update: WorkItemUpdate) -> OperationResult:
        """
        Update work item fields and optionally transition state.

        Args:
            work_item_update: WorkItemUpdate with field updates and optional state transition

        Returns:
            OperationResult with update confirmation
        """
        pass

    @abstractmethod
    async def transition_work_item_state(self, work_item_id: int, target_state: str) -> TransitionResult:
        """
        Transition work item to a new state in the workflow.

        Args:
            work_item_id: Work item ID
            target_state: Target state name

        Returns:
            TransitionResult with transition details
        """
        pass
    
    # Development Artifact Operations
    @abstractmethod
    async def attach_development_artifacts(self, work_item_id: int, artifacts: DevelopmentArtifacts) -> ArtifactResult:
        """
        Attach development artifacts from Azure Repos, GitHub, or GitLab to work item.
        
        Args:
            work_item_id: Azure DevOps work item ID
            artifacts: DevelopmentArtifacts with commit, PR, and build information
            
        Returns:
            ArtifactResult with attachment details
        """
        pass
    
    @abstractmethod
    async def sync_repository_activity(self, repository_url: str, work_item_id: int) -> OperationResult:
        """
        Synchronize repository activity with Azure DevOps work item.
        
        Args:
            repository_url: Git repository URL
            work_item_id: Azure DevOps work item ID
            
        Returns:
            OperationResult with sync status
        """
        pass
    
    # Cross-Platform Operations
    @abstractmethod
    async def sync_github_issues(self, owner: str, repo: str, work_item_id: Optional[int] = None) -> OperationResult:
        """
        Synchronize GitHub issues with Azure DevOps work items.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            work_item_id: Optional Azure DevOps work item ID for linking

        Returns:
            OperationResult with sync status
        """
        pass

    @abstractmethod
    async def sync_gitlab_issues(self, project_id: str, work_item_id: Optional[int] = None) -> OperationResult:
        """
        Synchronize GitLab issues with Azure DevOps work items.

        Args:
            project_id: GitLab project ID
            work_item_id: Optional Azure DevOps work item ID for linking

        Returns:
            OperationResult with sync status
        """
        pass
    
    # Configuration Management Operations
    @abstractmethod
    async def get_project_configuration(self, organization: str, project: str) -> Optional[AzureDevOpsProjectStructure]:
        """
        Retrieve cached Azure DevOps project configuration.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            
        Returns:
            AzureDevOpsProjectStructure if cached, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_project_configuration(self, organization: str, project: str, 
                                         configuration: AzureDevOpsProjectStructure) -> OperationResult:
        """
        Update cached Azure DevOps project configuration.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            configuration: Updated AzureDevOpsProjectStructure
            
        Returns:
            OperationResult with update status
        """
        pass
    
    # Monitoring and Health Operations
    @abstractmethod
    async def get_health_status(self) -> HealthStatus:
        """
        Get comprehensive health status of the manufacturing system.
        
        Returns:
            HealthStatus with system health information
        """
        pass
    
    @abstractmethod
    async def generate_dashboard_data(self, organization: str, project: str) -> DashboardData:
        """
        Generate real-time dashboard data for multi-platform workflows.

        Args:
            organization: Organization name
            project: Project name

        Returns:
            DashboardData with metrics and insights
        """
        pass

    # Batch Operations for Performance
    @abstractmethod
    async def bulk_update_work_items(self, updates: List[WorkItemUpdate]) -> OperationResult:
        """
        Update multiple work items in batch for performance.

        Args:
            updates: List of WorkItemUpdate objects

        Returns:
            OperationResult with batch update results
        """
        pass

    @abstractmethod
    async def bulk_transition_work_items(self, transitions: Dict[int, str]) -> List[TransitionResult]:
        """
        Transition multiple work items to new states in batch.

        Args:
            transitions: Dictionary mapping work item IDs to target states

        Returns:
            List of TransitionResult for each transition
        """
        pass


class ConfigurationManagerInterface(ABC):
    """Interface for multi-platform configuration persistence"""

    @abstractmethod
    async def store_project_configuration(self, organization: str, project: str,
                                        configuration: AzureDevOpsProjectStructure) -> bool:
        """Store project configuration with versioning"""
        pass

    @abstractmethod
    async def get_project_configuration(self, organization: str, project: str,
                                      version: Optional[str] = None) -> Optional[AzureDevOpsProjectStructure]:
        """Retrieve project configuration with optional versioning"""
        pass

    @abstractmethod
    async def schedule_configuration_validation(self, organization: str, project: str, schedule: str) -> bool:
        """Schedule configuration validation job"""
        pass


class WorkflowManagerInterface(ABC):
    """Interface for workflow automation"""

    @abstractmethod
    async def execute_state_transition(self, organization: str, project: str,
                                     work_item_id: int, target_state: str,
                                     context: Dict[str, Any]) -> TransitionResult:
        """Execute state transition in workflow"""
        pass

    @abstractmethod
    async def get_board_configuration(self, organization: str, project: str, team: str) -> Dict[str, Any]:
        """Retrieve board configuration"""
        pass


class ArtifactManagerInterface(ABC):
    """Interface for multi-platform Git integration"""

    @abstractmethod
    async def attach_commit_artifacts(self, organization: str, project: str, work_item_id: int,
                                    repository_url: str, commit_hashes: List[str]) -> ArtifactResult:
        """Attach commit artifacts to work items"""
        pass

    @abstractmethod
    async def attach_pull_request_artifacts(self, organization: str, project: str,
                                          work_item_id: int, pr_url: str) -> ArtifactResult:
        """Attach pull/merge request artifacts"""
        pass

    @abstractmethod
    async def sync_repository_activity(self, repository_url: str,
                                     work_item_patterns: List[str]) -> None:
        """Monitor repository for development activity"""
        pass


class CacheManagerInterface(ABC):
    """Interface for high-performance caching"""

    @abstractmethod
    async def get_project_structure(self, organization: str, project: str) -> Optional[AzureDevOpsProjectStructure]:
        """Multi-tier cache lookup for project structure"""
        pass

    @abstractmethod
    async def cache_work_item_types(self, organization: str, project: str, work_item_types: List[Dict[str, Any]]) -> bool:
        """Cache work item type definitions with field schemas"""
        pass

    @abstractmethod
    async def warm_cache(self, organizations: List[str], projects: List[str]) -> bool:
        """Pre-warm cache for operations"""
        pass

    @abstractmethod
    async def invalidate_cache(self, cache_key: str) -> bool:
        """Invalidate specific cache entry"""
        pass
