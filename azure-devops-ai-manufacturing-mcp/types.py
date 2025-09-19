"""
Azure DevOps AI Manufacturing MCP - Data Types and Structures

This module defines all data types, enums, and structures used for Azure DevOps
AI manufacturing operations following the Standardized Modules Framework.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class ManufacturingPhase(Enum):
    """Manufacturing phases for Azure DevOps workflow"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    COMPLETION = "completion"


class AzureDevOpsWorkItemType(Enum):
    """Azure DevOps work item types"""
    EPIC = "Epic"
    FEATURE = "Feature"
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"
    TEST_CASE = "Test Case"
    ISSUE = "Issue"


class QualityGateStatus(Enum):
    """Quality gate statuses"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GitProvider(Enum):
    """Supported Git providers"""
    AZURE_REPOS = "azure_repos"
    GITHUB = "github"
    GITLAB = "gitlab"


@dataclass
class OperationResult:
    """Standard operation result structure"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AzureDevOpsProjectStructure:
    """Complete Azure DevOps project structure"""
    organization: str
    project: str
    project_id: str
    project_description: str
    process_template: str
    work_item_types: Dict[str, 'WorkItemTypeDefinition']
    custom_fields: Dict[str, 'FieldDefinition']
    area_paths: List['AreaPath']
    iteration_paths: List['IterationPath']
    teams: List['TeamConfiguration']
    boards: Dict[str, 'BoardConfiguration']
    repositories: List['RepositoryInfo']
    build_definitions: List['BuildDefinition']
    analyzed_at: datetime
    field_usage_patterns: Dict[str, int]


@dataclass
class ManufacturingWorkItem:
    """Manufacturing work item structure for Azure DevOps"""
    organization: str
    project: str
    work_item_type: AzureDevOpsWorkItemType
    title: str
    description: Optional[str] = None
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    assigned_to: Optional[str] = None
    state: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    manufacturing_metadata: Optional['ManufacturingMetadata'] = None
    quality_requirements: Optional['QualityRequirements'] = None
    artifact_links: Optional[List['ArtifactLink']] = None


@dataclass
class ManufacturingMetadata:
    """AI manufacturing metadata structure for Azure DevOps"""
    manufacturing_id: str
    ai_generator: str
    confidence_score: float
    complexity_score: Optional[int] = None
    estimated_duration_hours: Optional[int] = None
    current_phase: ManufacturingPhase = ManufacturingPhase.ANALYSIS
    progress_percentage: int = 0
    quality_metrics: Optional[Dict[str, Any]] = None
    manufacturing_history: Optional[List['ManufacturingEvent']] = None
    azure_devops_work_item_id: Optional[int] = None


@dataclass
class ManufacturingProgress:
    """Manufacturing progress update structure"""
    current_phase: ManufacturingPhase
    progress_percentage: int
    quality_metrics: Optional[Dict[str, Any]] = None
    phase_completion_time: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass
class ManufacturingEvent:
    """Manufacturing event for history tracking"""
    event_type: str
    phase: ManufacturingPhase
    timestamp: datetime
    description: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QualityRequirements:
    """Quality requirements for manufacturing"""
    code_coverage_threshold: Optional[float] = None
    security_scan_required: bool = False
    performance_test_required: bool = False
    manual_review_required: bool = False
    custom_quality_gates: Optional[List[str]] = None


@dataclass
class QualityGateResult:
    """Quality gate validation result"""
    gate_name: str
    status: QualityGateStatus
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DevelopmentArtifacts:
    """Development artifact structure for multi-platform Git support"""
    repository_url: str
    provider: GitProvider
    organization: Optional[str] = None  # Azure DevOps organization
    project: Optional[str] = None       # Azure DevOps project
    repository_id: Optional[str] = None # Azure Repos repository ID
    commits: Optional[List['CommitArtifact']] = None
    pull_requests: Optional[List['PullRequestArtifact']] = None
    build_artifacts: Optional[List['BuildArtifact']] = None
    deployment_artifacts: Optional[List['DeploymentArtifact']] = None


@dataclass
class CommitArtifact:
    """Commit artifact structure for multi-platform support"""
    commit_hash: str
    commit_message: str
    author: str
    author_email: str
    timestamp: datetime
    repository_url: str
    branch: str
    files_changed: List[str]
    additions: int
    deletions: int
    work_item_mentions: List[int]  # Work item IDs mentioned in commit


@dataclass
class PullRequestArtifact:
    """Pull/merge request artifact structure"""
    pr_url: str
    pr_id: int
    title: str
    description: str
    status: str  # 'active', 'completed', 'abandoned' (Azure DevOps) or 'open', 'merged', 'closed'
    author: str
    reviewers: List[str]
    created_date: datetime
    completed_date: Optional[datetime] = None
    source_branch: str
    target_branch: str
    work_item_links: List[int]  # Linked work item IDs


@dataclass
class BuildArtifact:
    """Build artifact structure"""
    build_id: str
    build_number: str
    status: str
    result: str
    started_date: datetime
    finished_date: Optional[datetime] = None
    repository_url: str
    source_branch: str
    commit_hash: str
    build_url: str


@dataclass
class DeploymentArtifact:
    """Deployment artifact structure"""
    deployment_id: str
    environment: str
    status: str
    started_date: datetime
    completed_date: Optional[datetime] = None
    deployment_url: str
    release_version: str


@dataclass
class ArtifactLink:
    """Artifact link structure for Azure DevOps work items"""
    link_type: str  # 'commit', 'pull_request', 'build', 'deployment'
    url: str
    title: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkItemTypeDefinition:
    """Azure DevOps work item type definition"""
    name: str
    reference_name: str
    description: str
    icon: str
    color: str
    is_disabled: bool
    states: List['WorkItemState']
    fields: Dict[str, 'FieldDefinition']


@dataclass
class WorkItemState:
    """Azure DevOps work item state"""
    name: str
    category: str
    color: str


@dataclass
class FieldDefinition:
    """Azure DevOps field definition"""
    reference_name: str
    name: str
    type: str  # String, Integer, DateTime, Boolean, etc.
    usage: str  # WorkItem, WorkItemLink, Tree, etc.
    read_only: bool
    can_sort_by: bool
    is_queryable: bool
    is_identity: bool
    is_picklist: bool
    allowed_values: Optional[List[str]] = None


@dataclass
class AreaPath:
    """Azure DevOps area path"""
    id: int
    name: str
    path: str
    has_children: bool


@dataclass
class IterationPath:
    """Azure DevOps iteration path"""
    id: int
    name: str
    path: str
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None


@dataclass
class TeamConfiguration:
    """Azure DevOps team configuration"""
    id: str
    name: str
    description: str
    default_team: bool


@dataclass
class BoardConfiguration:
    """Azure DevOps board configuration"""
    board_id: str
    name: str
    columns: List['BoardColumn']
    rows: List['BoardRow']
    card_fields: List[str]
    card_styles: Dict[str, Any]


@dataclass
class BoardColumn:
    """Azure DevOps board column"""
    id: str
    name: str
    item_limit: Optional[int]
    state_mappings: List[str]  # Work item states mapped to this column
    column_type: str  # incoming, inProgress, outgoing


@dataclass
class BoardRow:
    """Azure DevOps board row (swimlane)"""
    id: str
    name: str


@dataclass
class RepositoryInfo:
    """Azure DevOps repository information"""
    id: str
    name: str
    url: str
    default_branch: str
    size: int


@dataclass
class BuildDefinition:
    """Azure DevOps build definition"""
    id: int
    name: str
    path: str
    type: str
    repository: RepositoryInfo


@dataclass
class TransitionResult:
    """Workflow transition result"""
    success: bool
    from_phase: ManufacturingPhase
    to_phase: ManufacturingPhase
    work_item_id: int
    board_column_updated: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ArtifactResult:
    """Artifact attachment result"""
    success: bool
    artifact_count: int
    attached_artifacts: List[ArtifactLink]
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HealthStatus:
    """System health status"""
    healthy: bool
    azure_devops_api_status: str
    cache_status: str
    database_status: str
    last_check: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None


@dataclass
class DashboardData:
    """Manufacturing dashboard data"""
    organization: str
    project: str
    manufacturing_velocity: Dict[str, float]
    active_work_items: int
    completed_work_items: int
    quality_metrics: Dict[str, Any]
    bottlenecks: List[str]
    team_performance: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)


# Default manufacturing phase mapping for Azure DevOps board states
DEFAULT_PHASES = {
    'analysis': 'New',
    'planning': 'Approved',
    'code_generation': 'Active',
    'code_review': 'Resolved',
    'testing': 'Testing',
    'integration': 'Build',
    'deployment': 'Deploy',
    'completion': 'Closed'
}
