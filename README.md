# Azure DevOps Multi-Platform MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Azure DevOps](https://img.shields.io/badge/Azure%20DevOps-Compatible-blue.svg)](https://dev.azure.com/)
[![GitHub](https://img.shields.io/badge/GitHub-Compatible-green.svg)](https://github.com/)
[![GitLab](https://img.shields.io/badge/GitLab-Compatible-orange.svg)](https://gitlab.com/)

A comprehensive Model Context Protocol (MCP) module that provides unified integration with Azure DevOps, GitHub, and GitLab, enabling seamless work item management, repository synchronization, and cross-platform development workflows.

## 🚀 Features

### 🔄 Multi-Platform Integration
- **Unified Work Item Management**: Seamless creation and updates across Azure DevOps, GitHub, and GitLab
- **Cross-Platform Synchronization**: Real-time sync of issues, work items, and development activities
- **Custom Field Support**: Full integration with platform-specific custom fields
- **Flexible Data Structures**: API-driven data models that adapt to your requirements

### 📊 Advanced Work Item Operations
- **Dynamic Work Item Creation**: Create and update work items with flexible field mapping
- **Attachment Management**: Upload and manage markdown documents and files attached to work items
- **Multi-Document Support**: Attach multiple documents per work item with full content retrieval
- **Bulk Operations**: Efficient batch processing of work items and issues
- **State Management**: Automated state transitions and workflow progression
- **Field Mapping**: Customizable field mappings between different platforms

### 🔗 Development Artifact Integration
- **Multi-Git Platform Support**: Azure Repos, GitHub, and GitLab repository integration
- **Artifact Linking**: Automatic attachment of commits, pull requests, and releases
- **Repository Synchronization**: Real-time sync of development activities across platforms
- **Cross-Reference Management**: Link work items across different platforms

### ⚡ Performance & Scalability
- **High-Performance Caching**: Multi-tier caching with Redis support for all platforms
- **Intelligent Rate Limiting**: Platform-aware rate limiting and burst capacity management
- **Asynchronous Operations**: Non-blocking operations for maximum throughput
- **Secure Configuration**: Encrypted configuration management with platform tokens

### 📈 Monitoring & Analytics
- **Performance Metrics**: Comprehensive monitoring across all integrated platforms
- **Analytics Integration**: Deep integration with platform-specific analytics
- **Cross-Platform Insights**: Unified view of development activities
- **Health Monitoring**: Real-time status monitoring of all integrations

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Accounts on target platforms (Azure DevOps, GitHub, GitLab)
- Appropriate API tokens for each platform:
  - Azure DevOps: Personal Access Token (PAT)
  - GitHub: Personal Access Token or GitHub App
  - GitLab: Personal Access Token or Project Token
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
    'azure_devops_pat': 'your_azure_devops_token_here',
    'github_token': 'your_github_token_here',
    'gitlab_token': 'your_gitlab_token_here',
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
from azure_devops_multiplatform_mcp import AzureDevOpsMultiPlatformMCP
from azure_devops_multiplatform_mcp.types import WorkItemData

async def main():
    config = {
        'azure_devops_organization_url': 'https://dev.azure.com/YourOrg',
        'azure_devops_pat': 'your_azure_devops_token_here',
        'github_token': 'your_github_token_here',
        'gitlab_token': 'your_gitlab_token_here',
        'default_project': 'YourProject'
    }

    mcp = AzureDevOpsMultiPlatformMCP(config)

    async with mcp:
        # Create a work item with flexible data structure and attachments
        work_item_data = WorkItemData(
            organization="YourOrg",
            project="YourProject",
            work_item_type="User Story",
            title="Authentication Service Implementation",
            description="Implement OAuth-based authentication service",
            fields={
                "System.Tags": "authentication;security;oauth",
                "Microsoft.VSTS.Common.Priority": "2",
                "Custom.Tokens": 15000  # Custom field example
            },
            attachments=[
                # Optional: Add markdown documentation
                # Attachments can be created separately and added here
            ]
        )

        # Create the work item
        result = await mcp.create_work_item(work_item_data)

        if result.success:
            print(f"Created work item: {result.data['id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 Workflow Integration

The module supports flexible workflow integration across platforms:

```
📋 New
    ↓ Initial work item creation and planning

🎯 Active
    ↓ Active development and implementation

🔍 Resolved
    ↓ Review and validation phase

🧪 Test *
    ↓ Testing and quality assurance

🚀 Closed
    ↓ Completion and deployment
```

*Custom states and workflows are automatically detected and supported

## 🔧 API Reference

### Core Classes

#### `AzureDevOpsMultiPlatformMCP`

Main interface for the multi-platform MCP module.

```python
class AzureDevOpsMultiPlatformMCP:
    async def create_work_item(self, work_item_data: WorkItemData) -> OperationResult
    async def update_work_item(self, work_item_id: int, updates: dict) -> OperationResult
    async def transition_work_item_state(self, work_item_id: int, target_state: str) -> OperationResult
    async def attach_artifacts(self, work_item_id: int, artifacts: dict) -> OperationResult
    async def sync_repository_activity(self, repository_url: str, work_item_id: int = None) -> OperationResult
    
    # Attachment Management
    async def get_work_item_attachments(self, work_item_id: int, project: str) -> OperationResult
    async def add_work_item_attachment(self, work_item_id: int, project: str, 
                                     content: str, filename: str) -> OperationResult
    async def remove_work_item_attachment(self, work_item_id: int, project: str, 
                                        attachment_id: str) -> OperationResult
```

## 🧪 Examples

### Working with Attachments and Markdown Documents

```python
# Example: Creating work items with markdown documentation
async def create_work_item_with_documentation():
    # Create markdown documentation
    requirements_doc = """
# Feature Requirements

## Overview
This feature implements user authentication with OAuth 2.0.

## Functional Requirements
1. **User Login**: Support for email/password and social login
2. **Token Management**: JWT tokens with refresh capability
3. **Role-Based Access**: Admin, User, and Guest roles

## Technical Requirements
- OAuth 2.0 compliance
- JWT token implementation
- Database integration for user management
- API rate limiting

## Acceptance Criteria
- ✅ Users can log in with email/password
- ✅ Social login (Google, GitHub) working
- ✅ Tokens expire and refresh correctly
- ✅ Role-based access controls enforced
    """

    design_doc = """
# Technical Design

## Architecture
- **Frontend**: React.js with Auth0 integration
- **Backend**: Python FastAPI with JWT middleware
- **Database**: PostgreSQL with user tables

## API Endpoints
```
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET /auth/profile
```

## Security Considerations
- HTTPS only in production
- Secure JWT secret management
- Rate limiting on auth endpoints
    """

    # Upload documents and create work item
    mcp = AzureDevOpsMultiPlatformMCP(config)
    
    async with mcp:
        # Upload markdown documents
        requirements_attachment = await mcp.attachment_manager.upload_markdown_document(
            markdown_content=requirements_doc,
            filename="requirements.md",
            project="YourProject"
        )
        
        design_attachment = await mcp.attachment_manager.upload_markdown_document(
            markdown_content=design_doc,
            filename="design.md",
            project="YourProject"
        )
        
        # Create work item with attachments
        work_item_data = WorkItemData(
            organization="YourOrg",
            project="YourProject",
            work_item_type="User Story",
            title="OAuth Authentication Implementation",
            description="Implement OAuth-based authentication with comprehensive documentation",
            fields={
                "System.Tags": "authentication;oauth;security",
                "Microsoft.VSTS.Common.Priority": "1",
                "Custom.Tokens": 25000
            },
            attachments=[requirements_attachment, design_attachment]
        )
        
        result = await mcp.create_work_item(work_item_data)
        
        if result.success:
            work_item_id = result.data['id']
            print(f"Created work item {work_item_id} with documentation")
            
            # Read back attachments to verify
            attachments_result = await mcp.get_work_item_attachments(work_item_id, "YourProject")
            
            if attachments_result.success:
                for attachment in attachments_result.data:
                    print(f"Attachment: {attachment.name} ({attachment.size} bytes)")
                    if attachment.content:
                        print(f"Content preview: {attachment.content[:100]}...")
```

### Working with Custom Fields

```python
# Example: Creating work items with custom fields
work_item_data = WorkItemData(
    organization="YourOrg",
    project="YourProject",
    work_item_type="User Story",
    title="Authentication Service Implementation",
    description="Implement OAuth-based authentication service",
    fields={
        "System.Tags": "authentication;security;oauth",
        "Microsoft.VSTS.Common.Priority": "2",
        "Custom.Tokens": 15000,  # Custom field for token tracking
        "Custom.EstimatedCost": 0.45  # Custom field for cost tracking
    }
)

# The module automatically detects and populates custom fields
result = await mcp.create_work_item(work_item_data)
```

### Cross-Platform Operations

```python
# Example: Syncing work items across platforms
async with mcp:
    # Create work item in Azure DevOps
    ado_work_item = await mcp.create_work_item(WorkItemData(
        organization="YourOrg",
        project="YourProject",
        work_item_type="User Story",
        title="Cross-platform feature",
        fields={"System.Tags": "cross-platform;sync"}
    ))

    # Create corresponding GitHub issue
    github_issue = await mcp.create_github_issue(
        owner="yourorg",
        repo="yourrepo",
        title="Cross-platform feature",
        body="Related Azure DevOps work item: #" + str(ado_work_item.data['id']),
        labels=["cross-platform", "sync"]
    )

    # Link them together
    await mcp.link_work_items(
        source_item=ado_work_item.data['id'],
        target_item=github_issue['number'],
        platform="github",
        relationship="related"
    )
```

### Managing Attachments in Work Items

```python
# Example: Adding attachments to existing work items
async def add_documentation_to_work_item(work_item_id: int):
    mcp = AzureDevOpsMultiPlatformMCP(config)
    
    async with mcp:
        # Add a markdown document to an existing work item
        result = await mcp.add_work_item_attachment(
            work_item_id=work_item_id,
            project="YourProject",
            content="""
# Implementation Notes

## Progress Update
- ✅ Database schema designed
- ✅ API endpoints defined
- 🔄 Authentication logic in progress
- ⏳ Frontend integration pending

## Next Steps
1. Complete OAuth integration
2. Add unit tests
3. Performance testing
4. Security review

## Resources
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
            """.strip(),
            filename="implementation_notes.md"
        )
        
        if result.success:
            print("Successfully added implementation notes")
            
        # Read all attachments from the work item
        attachments_result = await mcp.get_work_item_attachments(work_item_id, "YourProject")
        
        if attachments_result.success:
            print(f"Work item {work_item_id} has {len(attachments_result.data)} attachments:")
            for attachment in attachments_result.data:
                print(f"  📄 {attachment.name} ({attachment.content_type})")
                if attachment.content and attachment.content_type == "text/markdown":
                    lines = attachment.content.count('\n') + 1
                    words = len(attachment.content.split())
                    print(f"     📊 {lines} lines, ~{words} words")
```

### Bulk Operations

```python
# Example: Bulk update work items
updates = [
    {"id": 123, "fields": {"System.State": "Active", "System.AssignedTo": "user@example.com"}},
    {"id": 124, "fields": {"System.State": "Resolved", "Custom.Tokens": 12000}},
    {"id": 125, "fields": {"System.Tags": "urgent;bug", "Microsoft.VSTS.Common.Priority": "1"}}
]

async with mcp:
    results = await mcp.bulk_update_work_items(updates)
    successful = sum(1 for r in results if r.success)
    print(f"Successfully updated {successful}/{len(updates)} work items")
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
- Powered by Azure DevOps, GitHub, and GitLab REST APIs
- Designed for Model Context Protocol (MCP) integration
- Supports multiple Git platforms for unified development workflows

## 📊 Project Status

- ✅ **Core Functionality**: Complete
- ✅ **Azure DevOps Integration**: Full support with attachments
- ✅ **Work Item Attachments**: Markdown document support implemented
- ✅ **Multi-Document Support**: Multiple attachments per work item
- ✅ **Content Retrieval**: Full markdown content reading
- ✅ **GitHub Integration**: Full support
- ✅ **GitLab Integration**: Full support
- ✅ **Custom Field Support**: Validated
- ✅ **Cross-Platform Operations**: Working
- ✅ **Performance Optimization**: Implemented
- ✅ **Security Features**: Production-ready

## 🚀 Use Cases

### Development Workflow Automation
- **Unified Issue Tracking**: Manage work items across Azure DevOps, GitHub, and GitLab
- **Automated State Management**: Synchronize work item states across platforms
- **Cross-Platform Linking**: Link related work items across different systems

### CI/CD Integration
- **Artifact Tracking**: Link builds, releases, and deployments to work items
- **Status Synchronization**: Update work item status based on pipeline results
- **Repository Activity Sync**: Monitor commits, PRs, and issues across platforms

### Team Collaboration
- **Multi-Platform Support**: Work across different Git platforms seamlessly
- **Custom Field Mapping**: Synchronize custom fields between platforms
- **Bulk Operations**: Efficiently manage multiple work items simultaneously

---

**Made with ❤️ for multi-platform development workflows**

For the latest updates and releases, visit our [GitHub repository](https://github.com/Jita81/ADOMCP).