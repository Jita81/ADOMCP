"""
Azure DevOps AI Manufacturing MCP - Public Interface Exports

This module exports the public interface for the Azure DevOps AI Manufacturing MCP
following the Standardized Modules Framework pattern.
"""

from .core import AzureDevOpsAIManufacturingMCP
from .interface import (
    AzureDevOpsAIManufacturingInterface,
    ConfigurationManagerInterface,
    WorkflowManagerInterface,
    ArtifactManagerInterface,
    CacheManagerInterface
)
from .types import (
    # Core data structures
    OperationResult,
    AzureDevOpsProjectStructure,
    ManufacturingWorkItem,
    ManufacturingMetadata,
    ManufacturingProgress,
    DevelopmentArtifacts,
    
    # Enums
    ManufacturingPhase,
    AzureDevOpsWorkItemType,
    QualityGateStatus,
    GitProvider,
    
    # Artifact types
    CommitArtifact,
    PullRequestArtifact,
    BuildArtifact,
    DeploymentArtifact,
    ArtifactLink,
    
    # Configuration types
    WorkItemTypeDefinition,
    FieldDefinition,
    BoardConfiguration,
    TeamConfiguration,
    RepositoryInfo,
    
    # Result types
    TransitionResult,
    ArtifactResult,
    QualityGateResult,
    
    # Monitoring types
    HealthStatus,
    DashboardData,
    
    # Constants
    DEFAULT_PHASES
)
from .config_manager import ConfigurationManager
from .workflow_manager import WorkflowManager
from .artifact_manager import ArtifactManager, AzureReposClient, GitHubClient, GitLabClient
from .cache_manager import CacheManager
from .monitoring import AzureDevOpsManufacturingMonitor

# Version information
__version__ = "1.0.0"
__author__ = "Azure DevOps AI Manufacturing Team"
__description__ = "Comprehensive Azure DevOps MCP module for AI-driven software manufacturing processes"

# Public API exports
__all__ = [
    # Main implementation class
    "AzureDevOpsAIManufacturingMCP",
    
    # Interface contracts
    "AzureDevOpsAIManufacturingInterface",
    "ConfigurationManagerInterface", 
    "WorkflowManagerInterface",
    "ArtifactManagerInterface",
    "CacheManagerInterface",
    
    # Supporting manager classes
    "ConfigurationManager",
    "WorkflowManager", 
    "ArtifactManager",
    "CacheManager",
    "AzureDevOpsManufacturingMonitor",
    
    # Git client classes
    "AzureReposClient",
    "GitHubClient", 
    "GitLabClient",
    
    # Core data structures
    "OperationResult",
    "AzureDevOpsProjectStructure",
    "ManufacturingWorkItem",
    "ManufacturingMetadata",
    "ManufacturingProgress", 
    "DevelopmentArtifacts",
    
    # Enums
    "ManufacturingPhase",
    "AzureDevOpsWorkItemType",
    "QualityGateStatus",
    "GitProvider",
    
    # Artifact types
    "CommitArtifact",
    "PullRequestArtifact",
    "BuildArtifact",
    "DeploymentArtifact", 
    "ArtifactLink",
    
    # Configuration types
    "WorkItemTypeDefinition",
    "FieldDefinition",
    "BoardConfiguration",
    "TeamConfiguration",
    "RepositoryInfo",
    
    # Result types
    "TransitionResult",
    "ArtifactResult",
    "QualityGateResult",
    
    # Monitoring types
    "HealthStatus",
    "DashboardData",
    
    # Constants
    "DEFAULT_PHASES",
    
    # Module metadata
    "__version__",
    "__author__",
    "__description__"
]

# Module-level convenience functions
def create_manufacturing_mcp(config: dict) -> AzureDevOpsAIManufacturingMCP:
    """
    Convenience function to create a configured Azure DevOps AI Manufacturing MCP instance
    
    Args:
        config: Configuration dictionary with Azure DevOps settings
        
    Returns:
        Configured AzureDevOpsAIManufacturingMCP instance
        
    Example:
        >>> config = {
        ...     'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        ...     'personal_access_token': 'your-pat-token',
        ...     'default_project': 'MyProject'
        ... }
        >>> mcp = create_manufacturing_mcp(config)
        >>> async with mcp:
        ...     result = await mcp.analyze_project_structure('myorg', 'MyProject')
    """
    return AzureDevOpsAIManufacturingMCP(config)


def get_default_configuration() -> dict:
    """
    Get default configuration template for Azure DevOps AI Manufacturing MCP
    
    Returns:
        Dictionary with default configuration values and placeholders
        
    Example:
        >>> default_config = get_default_configuration()
        >>> default_config['personal_access_token'] = 'your-actual-token'
        >>> mcp = create_manufacturing_mcp(default_config)
    """
    return {
        # Azure DevOps Configuration
        'azure_devops_organization_url': 'https://dev.azure.com/your-organization',
        'personal_access_token': '${AZURE_DEVOPS_PAT}',  # Set from environment
        'default_project': 'AI-Manufacturing',
        'rate_limit_rps': 20,
        'burst_capacity': 200,
        
        # Database Configuration  
        'config_storage': 'sqlite',
        'config_db_url': 'azure_devops_config.db',
        'config_encryption_key': '${CONFIG_ENCRYPTION_KEY}',
        
        # Cache Configuration
        'redis_url': None,  # Optional Redis URL
        'cache_ttl_seconds': 3600,
        'persistent_cache': True,
        
        # Git Integration
        'azure_repos_token': None,  # Usually same as main PAT
        'github_token': '${GITHUB_TOKEN}',
        'gitlab_token': '${GITLAB_TOKEN}',
        'default_git_provider': 'azure_repos',
        
        # Manufacturing Configuration
        'manufacturing_phases': DEFAULT_PHASES.copy(),
        
        # Quality Gates Configuration
        'quality_gates': {
            'code_coverage_threshold': 80,
            'security_scan_required': True,
            'performance_test_required': True,
            'azure_pipelines_integration': True
        },
        
        # Monitoring Configuration
        'enable_metrics': True,
        'metrics_backend': 'prometheus',
        'health_check_interval': 30,
        'log_level': 'INFO'
    }


# Module initialization
def _validate_dependencies():
    """Validate that required dependencies are available"""
    missing_deps = []
    
    # Check for optional dependencies
    try:
        import aiohttp
    except ImportError:
        missing_deps.append('aiohttp')
    
    try:
        import aiosqlite
    except ImportError:
        missing_deps.append('aiosqlite')
    
    if missing_deps:
        import warnings
        warnings.warn(
            f"Some optional dependencies are missing: {', '.join(missing_deps)}. "
            "Some features may not be available.",
            ImportWarning
        )

# Validate dependencies on import
_validate_dependencies()

# Module docstring for help()
__doc__ = f"""
Azure DevOps AI Manufacturing MCP v{__version__}

This module provides comprehensive Azure DevOps integration for AI-driven software 
manufacturing processes. It includes project analysis, work item management, 
workflow automation, and multi-platform Git integration.

Key Features:
- Complete Azure DevOps project structure analysis
- Manufacturing-optimized work item creation and management  
- Intelligent workflow automation with Azure Boards
- Multi-platform Git integration (Azure Repos, GitHub, GitLab)
- High-performance caching and configuration persistence
- Comprehensive monitoring and analytics

Quick Start:
    >>> from azure_devops_ai_manufacturing_mcp import create_manufacturing_mcp
    >>> 
    >>> config = {{
    ...     'azure_devops_organization_url': 'https://dev.azure.com/myorg',
    ...     'personal_access_token': 'your-pat-token'
    ... }}
    >>> 
    >>> async with create_manufacturing_mcp(config) as mcp:
    ...     result = await mcp.analyze_project_structure('myorg', 'myproject')
    ...     print(f"Analysis completed: {{result.success}}")

For more information, see the documentation in the docs/ directory.
"""
