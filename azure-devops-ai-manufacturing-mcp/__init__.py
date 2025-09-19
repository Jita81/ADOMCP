"""
Azure DevOps Multi-Platform MCP - Public Interface Exports

This module exports the public interface for the Azure DevOps Multi-Platform MCP
following the Standardized Modules Framework pattern.
"""

from .core import AzureDevOpsMultiPlatformMCP
from .interface import (
    AzureDevOpsMultiPlatformInterface,
    ConfigurationManagerInterface,
    WorkflowManagerInterface,
    ArtifactManagerInterface,
    CacheManagerInterface
)
from .types import (
    # Core data structures
    OperationResult,
    AzureDevOpsProjectStructure,
    WorkItemData,
    WorkItemUpdate,
    DevelopmentArtifacts,

    # Enums
    AzureDevOpsWorkItemType,
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

    # Monitoring types
    HealthStatus,
    DashboardData,

    # Constants
    DEFAULT_STATE_MAPPING
)
from .config_manager import ConfigurationManager
from .workflow_manager import WorkflowManager
from .artifact_manager import ArtifactManager, AzureReposClient, GitHubClient, GitLabClient
from .cache_manager import CacheManager
from .monitoring import AzureDevOpsMultiPlatformMonitor

# Version information
__version__ = "1.0.0"
__author__ = "Azure DevOps Multi-Platform Team"
__description__ = "Comprehensive MCP module for Azure DevOps, GitHub, and GitLab integration"

# Public API exports
__all__ = [
    # Main implementation class
    "AzureDevOpsMultiPlatformMCP",

    # Interface contracts
    "AzureDevOpsMultiPlatformInterface",
    "ConfigurationManagerInterface",
    "WorkflowManagerInterface",
    "ArtifactManagerInterface",
    "CacheManagerInterface",

    # Supporting manager classes
    "ConfigurationManager",
    "WorkflowManager",
    "ArtifactManager",
    "CacheManager",
    "AzureDevOpsMultiPlatformMonitor",

    # Git client classes
    "AzureReposClient",
    "GitHubClient",
    "GitLabClient",

    # Core data structures
    "OperationResult",
    "AzureDevOpsProjectStructure",
    "WorkItemData",
    "WorkItemUpdate",
    "DevelopmentArtifacts",

    # Enums
    "AzureDevOpsWorkItemType",
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

    # Monitoring types
    "HealthStatus",
    "DashboardData",

    # Constants
    "DEFAULT_STATE_MAPPING",

    # Module metadata
    "__version__",
    "__author__",
    "__description__"
]

# Module-level convenience functions
def create_multiplatform_mcp(config: dict) -> AzureDevOpsMultiPlatformMCP:
    """
    Convenience function to create a configured Azure DevOps Multi-Platform MCP instance

    Args:
        config: Configuration dictionary with Azure DevOps, GitHub, and GitLab settings

    Returns:
        Configured AzureDevOpsMultiPlatformMCP instance

    Example:
        >>> config = {
        ...     'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        ...     'azure_devops_pat': 'your-azure-devops-token',
        ...     'github_token': 'your-github-token',
        ...     'gitlab_token': 'your-gitlab-token',
        ...     'default_project': 'MyProject'
        ... }
        >>> mcp = create_multiplatform_mcp(config)
        >>> async with mcp:
        ...     result = await mcp.analyze_project_structure('myorg', 'MyProject')
    """
    return AzureDevOpsMultiPlatformMCP(config)


def get_default_configuration() -> dict:
    """
    Get default configuration template for Azure DevOps Multi-Platform MCP

    Returns:
        Dictionary with default configuration values and placeholders

    Example:
        >>> default_config = get_default_configuration()
        >>> default_config['azure_devops_pat'] = 'your-actual-token'
        >>> mcp = create_multiplatform_mcp(default_config)
    """
    return {
        # Azure DevOps Configuration
        'azure_devops_organization_url': 'https://dev.azure.com/your-organization',
        'azure_devops_pat': '${AZURE_DEVOPS_PAT}',  # Set from environment
        'default_project': 'YourProject',
        'rate_limit_rps': 20,
        'burst_capacity': 200,

        # Multi-Platform Configuration
        'github_token': '${GITHUB_TOKEN}',
        'gitlab_token': '${GITLAB_TOKEN}',

        # Database Configuration
        'config_storage': 'sqlite',
        'config_db_url': 'azure_devops_config.db',
        'config_encryption_key': '${CONFIG_ENCRYPTION_KEY}',

        # Cache Configuration
        'redis_url': None,  # Optional Redis URL
        'cache_ttl_seconds': 3600,
        'persistent_cache': True,

        # State Mapping Configuration
        'state_mapping': DEFAULT_STATE_MAPPING.copy(),

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
Azure DevOps Multi-Platform MCP v{__version__}

This module provides comprehensive integration with Azure DevOps, GitHub, and GitLab
for unified development workflow management. It includes project analysis, work item
management, cross-platform synchronization, and multi-platform Git integration.

Key Features:
- Complete Azure DevOps project structure analysis
- Flexible work item creation and management with custom field support
- Cross-platform synchronization between Azure DevOps, GitHub, and GitLab
- Multi-platform Git integration (Azure Repos, GitHub, GitLab)
- High-performance caching and configuration persistence
- Comprehensive monitoring and analytics

Quick Start:
    >>> from azure_devops_multiplatform_mcp import create_multiplatform_mcp
    >>>
    >>> config = {{
    ...     'azure_devops_organization_url': 'https://dev.azure.com/myorg',
    ...     'azure_devops_pat': 'your-azure-devops-token',
    ...     'github_token': 'your-github-token',
    ...     'gitlab_token': 'your-gitlab-token'
    ... }}
    >>>
    >>> async with create_multiplatform_mcp(config) as mcp:
    ...     result = await mcp.analyze_project_structure('myorg', 'myproject')
    ...     print(f"Analysis completed: {{result.success}}")

For more information, see the documentation in the docs/ directory.
"""
