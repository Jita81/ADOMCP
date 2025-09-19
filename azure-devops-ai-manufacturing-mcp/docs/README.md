# Azure DevOps AI Manufacturing MCP

A comprehensive Azure DevOps MCP (Model Context Protocol) module that enables AI-driven software manufacturing processes with full integration into Azure DevOps boards and source control systems.

## 🎯 Overview

This module provides enterprise-grade Azure DevOps integration for AI manufacturing workflows, including:

- **Complete Project Analysis**: Comprehensive Azure DevOps project structure analysis with persistent configuration
- **Manufacturing Workflow Management**: Intelligent work item creation and workflow automation through Azure Boards
- **Multi-Platform Git Integration**: Seamless integration with Azure Repos, GitHub, and GitLab
- **High-Performance Caching**: Multi-tier caching system for optimal performance
- **Real-Time Monitoring**: Comprehensive performance and health monitoring with Azure DevOps Analytics

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd azure-devops-ai-manufacturing-mcp

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
import asyncio
from azure_devops_ai_manufacturing_mcp import create_manufacturing_mcp

async def main():
    # Configuration
    config = {
        'azure_devops_organization_url': 'https://dev.azure.com/your-org',
        'personal_access_token': 'your-pat-token',
        'default_project': 'AI-Manufacturing'
    }
    
    # Create and use the MCP
    async with create_manufacturing_mcp(config) as mcp:
        # Analyze project structure
        result = await mcp.analyze_project_structure('your-org', 'your-project')
        print(f"Analysis completed: {result.success}")
        
        # Create manufacturing work item
        from azure_devops_ai_manufacturing_mcp import ManufacturingWorkItem, ManufacturingMetadata
        
        work_item = ManufacturingWorkItem(
            organization='your-org',
            project='your-project',
            work_item_type='User Story',
            title='AI Generated Authentication Service',
            manufacturing_metadata=ManufacturingMetadata(
                manufacturing_id='ai_auth_001',
                ai_generator='gpt-4-code-specialist',
                confidence_score=0.94
            )
        )
        
        result = await mcp.create_manufacturing_work_item(work_item)
        print(f"Work item created: {result.data['work_item_id']}")

# Run the example
asyncio.run(main())
```

## 🏗️ Architecture

### Core Components

```
azure-devops-ai-manufacturing-mcp/
├── core.py                    # Main implementation
├── interface.py               # Interface contracts
├── types.py                   # Data type definitions
├── config_manager.py          # Configuration persistence
├── workflow_manager.py        # Azure Boards workflow automation
├── artifact_manager.py        # Git integration (Azure Repos/GitHub/GitLab)
├── cache_manager.py           # Multi-tier caching system
├── monitoring.py              # Performance and health monitoring
└── tests/                     # Comprehensive test suite
```

### Key Features

#### 1. Project Structure Analysis
- Comprehensive Azure DevOps project analysis
- Work item type and field configuration discovery
- Board and team configuration mapping
- Persistent configuration with versioning

#### 2. Manufacturing Work Item Management
- AI-optimized work item creation with custom metadata
- Automatic board transitions based on manufacturing phases
- Bulk operations for high-volume manufacturing
- Quality gate validation and enforcement

#### 3. Multi-Platform Git Integration
- **Azure Repos**: Native integration with Azure DevOps Git
- **GitHub**: Full GitHub API integration with work item linking
- **GitLab**: GitLab API integration for merge requests and commits
- Automatic artifact attachment and synchronization

#### 4. Workflow Automation
- Manufacturing phase mapping to Azure Boards states
- Intelligent transition validation and quality gates
- Custom board configuration support
- Automated progress tracking and reporting

## 📋 Configuration

### Basic Configuration

```python
config = {
    # Azure DevOps Configuration
    'azure_devops_organization_url': 'https://dev.azure.com/your-org',
    'personal_access_token': 'your-pat-token',
    'default_project': 'AI-Manufacturing',
    
    # Cache Configuration
    'redis_url': 'redis://localhost:6379',  # Optional
    'cache_ttl_seconds': 3600,
    'persistent_cache': True,
    
    # Git Integration
    'github_token': 'your-github-token',
    'gitlab_token': 'your-gitlab-token',
    'default_git_provider': 'azure_repos',
    
    # Manufacturing Phases
    'manufacturing_phases': {
        'analysis': 'New',
        'code_generation': 'Active', 
        'testing': 'Testing',
        'completion': 'Closed'
    }
}
```

### Production Configuration

```python
from azure_devops_ai_manufacturing_mcp import get_default_configuration

# Get production-ready configuration template
config = get_default_configuration()

# Customize for your environment
config.update({
    'azure_devops_organization_url': 'https://dev.azure.com/mycompany',
    'personal_access_token': os.environ['AZURE_DEVOPS_PAT'],
    'redis_url': os.environ['REDIS_URL'],
    'config_encryption_key': os.environ['CONFIG_ENCRYPTION_KEY'],
    'enable_metrics': True,
    'metrics_backend': 'prometheus'
})
```

## 🔧 API Reference

### Core MCP Class

#### `AzureDevOpsAIManufacturingMCP`

The main class providing Azure DevOps AI manufacturing functionality.

```python
async def analyze_project_structure(organization: str, project: str) -> OperationResult
```
Analyzes Azure DevOps project structure with caching and persistence.

```python
async def create_manufacturing_work_item(work_item: ManufacturingWorkItem) -> OperationResult
```
Creates manufacturing-optimized work item with AI metadata.

```python
async def update_manufacturing_progress(work_item_id: int, progress: ManufacturingProgress) -> OperationResult
```
Updates manufacturing progress and transitions workflow states.

```python
async def attach_development_artifacts(work_item_id: int, artifacts: DevelopmentArtifacts) -> ArtifactResult
```
Attaches development artifacts from multiple Git platforms.

### Data Types

#### `ManufacturingWorkItem`
```python
@dataclass
class ManufacturingWorkItem:
    organization: str
    project: str
    work_item_type: AzureDevOpsWorkItemType
    title: str
    description: Optional[str] = None
    manufacturing_metadata: Optional[ManufacturingMetadata] = None
    # ... additional fields
```

#### `ManufacturingMetadata`
```python
@dataclass
class ManufacturingMetadata:
    manufacturing_id: str
    ai_generator: str
    confidence_score: float
    current_phase: ManufacturingPhase = ManufacturingPhase.ANALYSIS
    progress_percentage: int = 0
    # ... additional fields
```

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest azure-devops-ai-manufacturing-mcp/tests/ -v

# Run specific test file
pytest azure-devops-ai-manufacturing-mcp/tests/test_core.py -v

# Run with coverage
pytest --cov=azure-devops-ai-manufacturing-mcp tests/
```

### Test Categories

- **Unit Tests**: Core functionality and data processing
- **Integration Tests**: Azure DevOps API integration
- **Performance Tests**: Load testing and benchmarks
- **End-to-End Tests**: Complete manufacturing workflows

## 📊 Monitoring and Performance

### Performance Metrics

The module includes comprehensive monitoring capabilities:

```python
# Get performance statistics
async with create_manufacturing_mcp(config) as mcp:
    health = await mcp.get_health_status()
    print(f"System healthy: {health.healthy}")
    
    dashboard = await mcp.generate_manufacturing_dashboard('org', 'project')
    print(f"Active work items: {dashboard.active_work_items}")
```

### Performance Targets

- **Individual Operations**: <2 seconds response time
- **Bulk Operations**: 50+ work items per batch
- **Concurrent Operations**: 100+ simultaneous requests
- **Cache Hit Rate**: >80% for repeated operations
- **System Uptime**: 99.9% availability

## 🔒 Security

### Authentication

- Uses Azure DevOps Personal Access Tokens (PAT)
- Supports encrypted configuration storage
- Secure token management for multi-platform Git integration

### Data Protection

- Configuration encryption at rest
- Secure API communication with HTTPS
- Sensitive data masking in logs

## 🚀 Production Deployment

### Prerequisites

1. **Azure DevOps Organization** with appropriate permissions
2. **Personal Access Token** with work item and repository access
3. **Database** (SQLite, PostgreSQL) for configuration persistence
4. **Redis** (optional) for distributed caching

### Deployment Steps

1. **Configure Environment Variables**
   ```bash
   export AZURE_DEVOPS_PAT="your-pat-token"
   export CONFIG_ENCRYPTION_KEY="your-encryption-key"
   export REDIS_URL="redis://localhost:6379"
   ```

2. **Initialize Database**
   ```python
   from azure_devops_ai_manufacturing_mcp import ConfigurationManager
   
   config_manager = ConfigurationManager('postgresql', 'your-db-url')
   # Database tables will be created automatically
   ```

3. **Deploy Application**
   ```python
   # Production application example
   import asyncio
   from azure_devops_ai_manufacturing_mcp import create_manufacturing_mcp, get_default_configuration
   
   async def production_app():
       config = get_default_configuration()
       # Update with production settings
       
       async with create_manufacturing_mcp(config) as mcp:
           # Your manufacturing logic here
           pass
   
   if __name__ == '__main__':
       asyncio.run(production_app())
   ```

## 📚 Examples

### Complete Manufacturing Workflow

```python
async def manufacturing_workflow_example():
    config = get_default_configuration()
    config['personal_access_token'] = 'your-token'
    
    async with create_manufacturing_mcp(config) as mcp:
        # 1. Analyze project
        analysis = await mcp.analyze_project_structure('myorg', 'myproject')
        
        # 2. Create work items
        work_items = []
        for i in range(5):
            work_item = ManufacturingWorkItem(
                organization='myorg',
                project='myproject',
                work_item_type=AzureDevOpsWorkItemType.USER_STORY,
                title=f'AI Generated Feature {i+1}',
                manufacturing_metadata=ManufacturingMetadata(
                    manufacturing_id=f'ai_feature_{i+1:03d}',
                    ai_generator='gpt-4-turbo',
                    confidence_score=0.9 + (i * 0.01)
                )
            )
            work_items.append(work_item)
        
        # 3. Bulk create
        bulk_result = await mcp.bulk_create_manufacturing_work_items(work_items)
        print(f"Created {len(work_items)} work items")
        
        # 4. Progress through phases
        for work_item_data in bulk_result.data['results']:
            work_item_id = work_item_data['work_item_id']
            
            # Simulate progression through phases
            phases = [
                ManufacturingPhase.CODE_GENERATION,
                ManufacturingPhase.TESTING,
                ManufacturingPhase.COMPLETION
            ]
            
            for phase in phases:
                progress = ManufacturingProgress(
                    current_phase=phase,
                    progress_percentage=int((phases.index(phase) + 1) / len(phases) * 100)
                )
                
                await mcp.update_manufacturing_progress(work_item_id, progress)
                
                # Attach artifacts when appropriate
                if phase == ManufacturingPhase.CODE_GENERATION:
                    artifacts = DevelopmentArtifacts(
                        repository_url='https://github.com/myorg/myrepo',
                        provider=GitProvider.GITHUB,
                        commits=[
                            CommitArtifact(
                                commit_hash='abc123',
                                commit_message=f'AI: Implement feature #{work_item_id}',
                                author='AI Manufacturing Bot',
                                # ... other commit details
                            )
                        ]
                    )
                    
                    await mcp.attach_development_artifacts(work_item_id, artifacts)

# Run the example
asyncio.run(manufacturing_workflow_example())
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for details on:

- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- **Documentation**: Check this README and inline code documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Compatibility**: Python 3.8+, Azure DevOps Services, Azure DevOps Server 2019+
