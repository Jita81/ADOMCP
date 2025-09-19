"""
Azure DevOps AI Manufacturing MCP - Interface Contracts

This module defines the complete interface contracts for Azure DevOps AI manufacturing
operations following the Standardized Modules Framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .types import (
    OperationResult, ManufacturingWorkItem, ManufacturingProgress, 
    ManufacturingPhase, DevelopmentArtifacts, AzureDevOpsProjectStructure,
    TransitionResult, ArtifactResult, QualityGateResult, HealthStatus, DashboardData
)


class AzureDevOpsAIManufacturingInterface(ABC):
    """
    Complete interface contract for Azure DevOps AI Manufacturing MCP module.
    
    This interface defines all operations required for AI-driven software manufacturing
    processes integrated with Azure DevOps, including project analysis, work item
    management, workflow automation, and artifact tracking.
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
    async def create_manufacturing_work_item(self, work_item: ManufacturingWorkItem) -> OperationResult:
        """
        Create manufacturing-optimized Azure DevOps work item with AI metadata.
        
        Args:
            work_item: ManufacturingWorkItem with all required fields
            
        Returns:
            OperationResult with created work item ID and details
        """
        pass
    
    @abstractmethod
    async def bulk_create_manufacturing_work_items(self, work_items: List[ManufacturingWorkItem]) -> OperationResult:
        """
        Create multiple manufacturing work items in batch for performance.
        
        Args:
            work_items: List of ManufacturingWorkItem objects
            
        Returns:
            OperationResult with batch creation results
        """
        pass
    
    @abstractmethod
    async def update_manufacturing_progress(self, work_item_id: int, progress_data: ManufacturingProgress) -> OperationResult:
        """
        Update manufacturing progress and automatically transition work item states.
        
        Args:
            work_item_id: Azure DevOps work item ID
            progress_data: ManufacturingProgress with current phase and metrics
            
        Returns:
            OperationResult with update confirmation
        """
        pass
    
    @abstractmethod
    async def transition_manufacturing_workflow(self, work_item_id: int, target_phase: ManufacturingPhase) -> TransitionResult:
        """
        Transition work item through Azure Boards workflow based on manufacturing phase.
        
        Args:
            work_item_id: Azure DevOps work item ID
            target_phase: Target ManufacturingPhase
            
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
    
    # Quality and Validation Operations
    @abstractmethod
    async def validate_quality_gates(self, work_item_id: int, target_phase: ManufacturingPhase) -> QualityGateResult:
        """
        Validate quality gates before manufacturing phase transition.
        
        Args:
            work_item_id: Azure DevOps work item ID
            target_phase: Target ManufacturingPhase for validation
            
        Returns:
            QualityGateResult with validation status
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
    async def generate_manufacturing_dashboard(self, organization: str, project: str) -> DashboardData:
        """
        Generate real-time manufacturing dashboard data.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            
        Returns:
            DashboardData with manufacturing metrics and insights
        """
        pass
    
    # Batch Operations for Performance
    @abstractmethod
    async def bulk_update_manufacturing_progress(self, updates: Dict[int, ManufacturingProgress]) -> OperationResult:
        """
        Update manufacturing progress for multiple work items in batch.
        
        Args:
            updates: Dictionary mapping work item IDs to ManufacturingProgress
            
        Returns:
            OperationResult with batch update results
        """
        pass
    
    @abstractmethod
    async def bulk_transition_workflows(self, transitions: Dict[int, ManufacturingPhase]) -> List[TransitionResult]:
        """
        Transition multiple work items through manufacturing workflows in batch.
        
        Args:
            transitions: Dictionary mapping work item IDs to target ManufacturingPhase
            
        Returns:
            List of TransitionResult for each transition
        """
        pass


class ConfigurationManagerInterface(ABC):
    """Interface for Azure DevOps configuration persistence"""
    
    @abstractmethod
    async def store_project_configuration(self, organization: str, project: str, 
                                        configuration: AzureDevOpsProjectStructure) -> bool:
        """Store Azure DevOps project configuration with versioning"""
        pass
    
    @abstractmethod
    async def get_project_configuration(self, organization: str, project: str, 
                                      version: Optional[str] = None) -> Optional[AzureDevOpsProjectStructure]:
        """Retrieve Azure DevOps project configuration with optional versioning"""
        pass
    
    @abstractmethod
    async def schedule_configuration_validation(self, organization: str, project: str, schedule: str) -> bool:
        """Schedule daily configuration validation job"""
        pass


class WorkflowManagerInterface(ABC):
    """Interface for Azure Boards workflow automation"""
    
    @abstractmethod
    async def execute_phase_transition(self, devops_client: Any, organization: str, project: str,
                                     work_item_id: int, target_phase: ManufacturingPhase, 
                                     context: Dict[str, Any]) -> TransitionResult:
        """Execute manufacturing phase transition in Azure Boards"""
        pass
    
    @abstractmethod
    async def validate_quality_gates(self, work_item_id: int, target_phase: ManufacturingPhase) -> QualityGateResult:
        """Validate quality gates before phase transition"""
        pass
    
    @abstractmethod
    async def get_board_configuration(self, organization: str, project: str, team: str) -> Dict[str, Any]:
        """Retrieve Azure Boards configuration"""
        pass


class ArtifactManagerInterface(ABC):
    """Interface for multi-platform Git integration"""
    
    @abstractmethod
    async def attach_commit_artifacts(self, organization: str, project: str, work_item_id: int, 
                                    repository_url: str, commit_hashes: List[str]) -> ArtifactResult:
        """Attach commit artifacts to Azure DevOps work items"""
        pass
    
    @abstractmethod
    async def attach_pull_request_artifacts(self, organization: str, project: str, 
                                          work_item_id: int, pr_url: str) -> ArtifactResult:
        """Attach pull/merge request artifacts"""
        pass
    
    @abstractmethod
    async def monitor_repository_activity(self, repository_url: str, 
                                        work_item_patterns: List[str]) -> None:
        """Monitor repository for manufacturing-related activity"""
        pass


class CacheManagerInterface(ABC):
    """Interface for high-performance caching"""
    
    @abstractmethod
    async def get_project_structure(self, organization: str, project: str) -> Optional[AzureDevOpsProjectStructure]:
        """Multi-tier cache lookup for Azure DevOps project structure"""
        pass
    
    @abstractmethod
    async def cache_work_item_types(self, organization: str, project: str, work_item_types: List[Dict[str, Any]]) -> bool:
        """Cache work item type definitions with field schemas"""
        pass
    
    @abstractmethod
    async def warm_cache_for_manufacturing(self, organizations: List[str], projects: List[str]) -> bool:
        """Pre-warm cache for manufacturing operations"""
        pass
    
    @abstractmethod
    async def invalidate_cache(self, cache_key: str) -> bool:
        """Invalidate specific cache entry"""
        pass
