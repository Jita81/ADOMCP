# Azure DevOps AI Manufacturing MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Azure DevOps](https://img.shields.io/badge/Azure%20DevOps-Compatible-blue.svg)](https://dev.azure.com/)

A comprehensive Model Context Protocol (MCP) module that integrates AI-powered manufacturing workflows with Azure DevOps, providing automated work item management, quality gates, and development artifact tracking.

## 🚀 Features

### 🏭 AI Manufacturing Workflow
- **Automated Lifecycle Management**: Complete work item progression from Analysis to Deployment
- **AI-Powered Code Generation**: Intelligent code creation and review processes
- **Quality Gate Integration**: Automated testing and validation at each phase
- **Custom Process Support**: Adapts to your Azure DevOps process templates and custom states

### 📊 Advanced Work Item Management
- **Smart Work Item Creation**: AI-generated work items with manufacturing metadata
- **Progress Tracking**: Real-time progress monitoring with detailed metrics
- **Custom Field Support**: Full integration with custom fields (e.g., tokens, cost tracking)
- **State Transition Automation**: Intelligent workflow progression based on quality gates

### 🔗 Development Integration
- **Multi-Platform Git Support**: Azure Repos, GitHub, and GitLab integration
- **Artifact Attachment**: Automatic linking of commits, pull requests, and releases
- **Repository Activity Sync**: Real-time synchronization of development activities
- **Code Quality Metrics**: Integrated code analysis and quality scoring

### ⚡ Performance & Scalability
- **High-Performance Caching**: Multi-tier caching with Redis support
- **Rate Limiting**: Intelligent API rate limiting and burst capacity management
- **Asynchronous Operations**: Non-blocking operations for maximum throughput
- **Configuration Management**: Secure, versioned configuration with encryption

### 📈 Monitoring & Analytics
- **Performance Metrics**: Comprehensive monitoring of manufacturing processes
- **Azure DevOps Analytics**: Deep integration with Azure DevOps reporting
- **Quality Insights**: Manufacturing quality trends and improvement recommendations
- **Cost Tracking**: AI token usage and cost management (with custom fields)

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Azure DevOps organization with appropriate permissions
- Personal Access Token (PAT) with work item and repository access
- Optional: Redis for caching (recommended for production)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Jita81/ADOMCP.git
cd ADOMCP

# Install dependencies
pip install -r azure-devops-ai-manufacturing-mcp/requirements.txt
```

### Production Installation

```bash
# Create virtual environment
python -m venv mcp_env
source mcp_env/bin/activate  # On Windows: mcp_env\Scripts\activate

# Install the module
cd azure-devops-ai-manufacturing-mcp
pip install -e .
```

## ⚙️ Configuration

### Basic Configuration

```python
config = {
    'azure_devops_organization_url': 'https://dev.azure.com/YourOrg',
    'personal_access_token': 'your_pat_token_here',
    'default_project': 'YourProject',
    'rate_limit_rps': 10,
    'burst_capacity': 100,
    'enable_metrics': True
}
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from azure_devops_ai_manufacturing_mcp import AzureDevOpsAIManufacturingMCP
from azure_devops_ai_manufacturing_mcp.types import ManufacturingWorkItem, ManufacturingMetadata

async def main():
    config = {
        'azure_devops_organization_url': 'https://dev.azure.com/YourOrg',
        'personal_access_token': 'your_pat_here',
        'default_project': 'YourProject'
    }
    
    mcp = AzureDevOpsAIManufacturingMCP(config)
    
    async with mcp:
        # Create a manufacturing work item
        work_item = ManufacturingWorkItem(
            organization="YourOrg",
            project="YourProject",
            work_item_type="User Story",
            title="AI-Generated Authentication Service",
            description="Automated authentication service with OAuth integration",
            manufacturing_metadata=ManufacturingMetadata(
                manufacturing_id="auth_service_001",
                ai_generator="gpt-4",
                confidence_score=95.0,
                complexity_score=7
            )
        )
        
        # Create the work item
        result = await mcp.create_manufacturing_work_item(work_item)
        
        if result.success:
            print(f"Created work item: {result.data['id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 Manufacturing Workflow

The module supports a complete AI manufacturing lifecycle:

```
📋 Analysis (New)
    ↓ Requirements gathering and AI model selection

🎯 Planning (Active) 
    ↓ Technical design and architecture planning

⚙️ Code Generation (Active)
    ↓ AI-driven code implementation

🔍 Code Review (Resolved)
    ↓ Peer review and quality validation

🧪 Testing (Test) *
    ↓ Comprehensive testing and validation

🚀 Deployment (Closed)
    ↓ Production deployment and monitoring
```

*Custom states are automatically detected and integrated

## 🔧 API Reference

### Core Classes

#### `AzureDevOpsAIManufacturingMCP`

Main interface for the manufacturing MCP module.

```python
class AzureDevOpsAIManufacturingMCP:
    async def create_manufacturing_work_item(self, work_item: ManufacturingWorkItem) -> OperationResult
    async def update_manufacturing_progress(self, work_item_id: int, progress_data: ManufacturingProgress) -> OperationResult
    async def transition_manufacturing_workflow(self, work_item_id: int, target_phase: str) -> OperationResult
    async def attach_development_artifacts(self, work_item_id: int, artifacts: DevelopmentArtifacts) -> OperationResult
```

## 🧪 Examples

### Working with Custom Fields

```python
# Example: Using custom 'tokens' field for AI cost tracking
work_item_data = {
    "title": "AI Code Generator",
    "description": "Advanced code generation with token tracking",
    "tokens": 15000,  # Custom field for AI token usage
    "estimated_cost": 0.45
}

# The module automatically detects and populates custom fields
result = await mcp.create_manufacturing_work_item(work_item)
```

## 🔒 Security

### Authentication
- Secure PAT token management with encryption
- Token rotation support
- Configurable access scopes

### Best Practices
```python
# Use environment variables for sensitive data
import os

config = {
    'personal_access_token': os.getenv('AZURE_DEVOPS_PAT'),
    'config_encryption_key': os.getenv('MCP_ENCRYPTION_KEY'),
    'secure_configuration': True
}
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- Create an [Issue](https://github.com/Jita81/ADOMCP/issues) for bug reports
- Start a [Discussion](https://github.com/Jita81/ADOMCP/discussions) for questions

## 🙏 Acknowledgments

- Built with the [Standardized Modules Framework v1.0.0](https://github.com/Jita81/Standardized-Modules-Framework-v1.0.0)
- Powered by Azure DevOps REST APIs
- Designed for Model Context Protocol (MCP) integration

## 📊 Project Status

- ✅ **Core Functionality**: Complete
- ✅ **Azure DevOps Integration**: Full support
- ✅ **Custom Field Support**: Validated
- ✅ **Custom Process Adaptation**: Working
- ✅ **Performance Optimization**: Implemented
- ✅ **Security Features**: Production-ready

---

**Made with ❤️ for AI-powered development workflows**

For the latest updates and releases, visit our [GitHub repository](https://github.com/Jita81/ADOMCP).