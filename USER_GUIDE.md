# Azure DevOps Multi-Platform MCP - User Guide

## 🎯 **Overview**

The Azure DevOps Multi-Platform MCP provides unified work item management across Azure DevOps, GitHub, and GitLab platforms with secure API key storage and comprehensive documentation support. Perfect for AI agents that need structured, contextual information across development platforms.

### **🌟 Key Benefits**

- **Unified Platform Management**: Single interface for Azure DevOps, GitHub, and GitLab
- **Perfect Context Boundaries**: Hierarchical structure optimized for AI agent consumption
- **Secure API Storage**: Encrypted API key management with Supabase
- **Rich Documentation**: Markdown attachment support for comprehensive context
- **Cross-Platform Integration**: Seamless synchronization and linking
- **Production Ready**: Deployed on Vercel with enterprise-grade security

---

## 🚀 **Quick Start**

### **Step 1: Store Your API Keys**

Before using any MCP functionality, securely store your platform API keys:

```bash
# Store Azure DevOps PAT
curl -X POST https://your-mcp-server.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-unique-user-id",
    "platform": "azure_devops",
    "api_key": "your-azure-devops-pat",
    "organization_url": "https://dev.azure.com/YourOrg",
    "project_id": "your-project-guid"
  }'

# Store GitHub Token
curl -X POST https://your-mcp-server.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-unique-user-id",
    "platform": "github", 
    "api_key": "ghp_your-github-token"
  }'
```

### **Step 2: Initialize MCP Connection**

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "Your AI Agent",
      "version": "1.0"
    }
  },
  "id": 1
}
```

### **Step 3: Create Your First Work Item**

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_work_item",
    "arguments": {
      "user_id": "your-user-id",
      "platform": "azure_devops",
      "work_item_type": "User Story",
      "title": "Implement user authentication",
      "description": "Add OAuth-based authentication system with multi-factor support"
    }
  },
  "id": 2
}
```

---

## 🏗️ **Hierarchical Work Item Structure**

The MCP maintains perfect context boundaries for AI agent consumption:

### **Epic Level - Strategic Context**
```json
{
  "scope": "Product-level strategy and business requirements",
  "documentation": "Comprehensive product requirements document",
  "context_boundary": "Strategic vision without implementation details",
  "example": {
    "title": "Authentication System Implementation",
    "description": "Complete OAuth-based authentication system",
    "attachments": ["product_requirements.md"],
    "ai_context": "Business objectives, market requirements, success criteria"
  }
}
```

### **Feature Level - Technical Context**
```json
{
  "scope": "Component-level technical design and architecture", 
  "documentation": "Requirements and technical design documents",
  "context_boundary": "Technical architecture without business strategy",
  "example": {
    "title": "OAuth Integration Framework",
    "description": "Third-party OAuth provider integration",
    "attachments": ["technical_requirements.md", "architecture_design.md"],
    "ai_context": "Component design, API specifications, integration patterns"
  }
}
```

### **User Story Level - Implementation Context**
```json
{
  "scope": "Implementation-level code and development",
  "documentation": "TDD specifications and implementation guides", 
  "context_boundary": "Implementation details without architecture complexity",
  "example": {
    "title": "Google OAuth Integration",
    "description": "Implement Google OAuth 2.0 authentication flow",
    "attachments": ["tdd_specification.md"],
    "ai_context": "Code requirements, test scenarios, implementation details"
  }
}
```

---

## 🔧 **MCP Tools Reference**

### **create_work_item**

Create work items across platforms with context preservation.

```json
{
  "name": "create_work_item",
  "inputSchema": {
    "user_id": "string (required)",
    "platform": "azure_devops | github | gitlab",
    "work_item_type": "Epic | Feature | User Story | Bug | Task",
    "title": "string (required)",
    "description": "string (optional)",
    "fields": "object (optional)",
    "attachments": "array (optional)"
  },
  "example": {
    "user_id": "user123",
    "platform": "azure_devops",
    "work_item_type": "Feature",
    "title": "User Authentication Framework",
    "description": "Comprehensive authentication system with OAuth support",
    "fields": {
      "System.Tags": "authentication;security;oauth",
      "Microsoft.VSTS.Common.Priority": "1",
      "Custom.Tokens": 25000
    }
  }
}
```

### **upload_attachment**

Upload markdown documents and attachments to work items.

```json
{
  "name": "upload_attachment",
  "inputSchema": {
    "user_id": "string (required)",
    "work_item_id": "string (required)",
    "content": "string (required)",
    "filename": "string (required)",
    "content_type": "string (optional, default: text/markdown)"
  },
  "example": {
    "user_id": "user123",
    "work_item_id": "64",
    "content": "# Technical Requirements\n\n## Authentication Flow\n...",
    "filename": "technical_requirements.md",
    "content_type": "text/markdown"
  }
}
```

### **create_epic_feature_story**

Create complete hierarchical structures with documentation.

```json
{
  "name": "create_epic_feature_story",
  "inputSchema": {
    "user_id": "string (required)",
    "epic_title": "string (required)",
    "epic_description": "string (required)",
    "features": "array (optional)",
    "stories": "array (optional)"
  },
  "example": {
    "user_id": "user123",
    "epic_title": "Authentication System",
    "epic_description": "Complete OAuth-based authentication system",
    "features": [
      {
        "title": "OAuth Integration Framework",
        "description": "Third-party OAuth provider integration",
        "stories": [
          {
            "title": "Google OAuth Implementation",
            "description": "Implement Google OAuth 2.0 flow"
          }
        ]
      }
    ]
  }
}
```

---

## 🔗 **Cross-Platform Integration**

### **GitHub Integration**

Synchronize Azure DevOps work items with GitHub issues:

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_work_item",
    "arguments": {
      "user_id": "user123",
      "platform": "github",
      "work_item_type": "issue",
      "title": "[Azure DevOps #68] User Authentication Implementation",
      "description": "Synchronized from Azure DevOps User Story #68\n\n## Implementation Context\n..."
    }
  }
}
```

### **Development Artifact Linking**

Connect commits, pull requests, and merges to work items:

```json
{
  "method": "tools/call",
  "params": {
    "name": "link_commits_prs",
    "arguments": {
      "user_id": "user123",
      "work_item_id": "68",
      "artifacts": [
        {
          "type": "commit",
          "platform": "github",
          "sha": "4961bfa8",
          "message": "Feature Release: Work Item Attachment Management",
          "url": "https://github.com/owner/repo/commit/4961bfa8"
        },
        {
          "type": "pull_request",
          "platform": "github", 
          "number": "1",
          "title": "Implement attachment management",
          "url": "https://github.com/owner/repo/pull/1"
        }
      ]
    }
  }
}
```

---

## 📚 **Rich Documentation Support**

### **Markdown Document Management**

The MCP supports comprehensive markdown documentation at each hierarchical level:

**Epic Level Documents:**
- Product Requirements Document (PRD)
- Business Case and Market Analysis
- Success Metrics and KPIs
- Implementation Strategy

**Feature Level Documents:**
- Technical Requirements Specification
- Architecture Design Document
- API Specifications
- Integration Guidelines

**Story Level Documents:**
- Test-Driven Development (TDD) Specifications
- Implementation Guidelines
- Code Review Checklists
- Acceptance Criteria

### **Document Upload Example**

```bash
# Upload comprehensive technical requirements
curl -X POST https://your-mcp-server.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "upload_attachment",
      "arguments": {
        "user_id": "user123",
        "work_item_id": "65",
        "content": "# OAuth Integration Framework - Technical Requirements\n\n## Overview\nThis document outlines the technical requirements for implementing OAuth 2.0 integration...\n\n## Architecture\n- **Authentication Flow**: Authorization Code Grant\n- **Token Management**: JWT with refresh token rotation\n- **Provider Support**: Google, GitHub, Microsoft\n\n## Security Requirements\n- PKCE implementation for public clients\n- State parameter for CSRF protection\n- Secure token storage with encryption\n\n## API Endpoints\n```\nPOST /auth/oauth/initiate\nGET  /auth/oauth/callback\nPOST /auth/oauth/refresh\nPOST /auth/oauth/revoke\n```\n\n## Implementation Guidelines\n...",
        "filename": "oauth_technical_requirements.md"
      }
    },
    "id": 3
  }'
```

---

## 🤖 **AI Agent Optimization**

### **Context Boundary Benefits**

The hierarchical structure provides optimal context for AI agents:

**Query Patterns:**
```javascript
// Get strategic context without implementation noise
await mcp.getWorkItem("epic", 64) 
// Returns: Product requirements, business objectives, success criteria

// Get technical context without business strategy
await mcp.getWorkItem("feature", 65)
// Returns: Architecture design, API specs, technical requirements

// Get implementation context without architecture complexity  
await mcp.getWorkItem("story", 68)
// Returns: TDD specs, code requirements, acceptance criteria
```

**Cross-Platform Traceability:**
```javascript
// Follow relationships while maintaining context boundaries
const epicContext = await mcp.getWorkItem("epic", 64);
const linkedFeatures = await mcp.getLinkedItems(64, "features");
const githubIssues = await mcp.getCrossPlattformLinks(64, "github");

// Result: Complete traceability without context bleeding
```

### **Perfect for AI Agent Workflows**

- **Strategic Planning**: AI agents get complete product context from Epics
- **Technical Design**: AI agents access architecture details from Features  
- **Implementation**: AI agents get focused development context from Stories
- **Cross-Platform**: AI agents maintain consistency across platforms
- **Documentation**: AI agents access rich markdown content for comprehensive context

---

## 🔒 **Security & API Key Management**

### **Secure Storage**

API keys are encrypted and stored securely in Supabase:

- **Encryption**: Base64 encoding (enhance with AES-256 for production)
- **Row Level Security**: Users can only access their own API keys
- **Environment Isolation**: Separate storage per user and platform
- **Audit Trail**: Created/updated timestamps for all key operations

### **Required API Keys**

**Azure DevOps:**
- Personal Access Token (PAT) with Work Item read/write permissions
- Organization URL and Project ID for context

**GitHub:**
- Personal Access Token with `repo` and `issues` permissions
- Optional: Organization access for enterprise features

**GitLab:**
- Personal Access Token with `api` and `read_repository` permissions
- Project ID for specific project access

### **Permission Validation**

```bash
# Test API key permissions
curl -X GET https://your-mcp-server.vercel.app/api/keys/validate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "platform": "azure_devops"
  }'
```

---

## 📊 **Monitoring & Analytics**

### **Health Monitoring**

```bash
# Check MCP server health
curl https://your-mcp-server.vercel.app/api/health

# Response includes:
{
  "status": "healthy",
  "service": "Azure DevOps Multi-Platform MCP",
  "version": "2.1.0",
  "mcp_capabilities": [
    "work_item_management",
    "attachment_support",
    "cross_platform_integration"
  ]
}
```

### **Usage Analytics**

Monitor MCP usage through Vercel Analytics:
- Function execution times
- Request/response patterns
- Error rates and debugging
- Geographic distribution
- Platform usage statistics

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**API Key Not Found**
```bash
# Verify API key storage
curl -X POST https://your-mcp-server.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","platform":"azure_devops","api_key":"your-pat"}'
```

**Permission Denied**
- Verify API token has appropriate permissions for the target platform
- Check organization/project access in platform settings
- Ensure PAT is not expired

**MCP Connection Failed**
```json
// Test MCP initialization
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {"clientInfo": {"name": "Test Client", "version": "1.0"}},
  "id": 1
}
```

**Work Item Creation Failed**
- Verify required fields for work item type
- Check custom field names and data types
- Ensure user has create permissions in target project

### **Debug Commands**

```bash
# Get MCP capabilities
curl https://your-mcp-server.vercel.app/api/capabilities

# Test work item creation
curl -X POST https://your-mcp-server.vercel.app/api/work-items \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "platform": "azure_devops",
    "work_item_type": "User Story",
    "title": "Test Work Item"
  }'

# Check Vercel logs
vercel logs --follow
```

---

## 🎓 **Advanced Usage**

### **Bulk Operations**

Create multiple work items with relationships:

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_epic_feature_story",
    "arguments": {
      "user_id": "user123",
      "epic_title": "E-commerce Platform",
      "features": [
        {
          "title": "User Management",
          "stories": [
            {"title": "User Registration"},
            {"title": "User Authentication"},
            {"title": "Profile Management"}
          ]
        },
        {
          "title": "Product Catalog",
          "stories": [
            {"title": "Product Listing"},
            {"title": "Product Search"},
            {"title": "Product Details"}
          ]
        }
      ]
    }
  }
}
```

### **Custom Field Mapping**

Handle platform-specific custom fields:

```json
{
  "fields": {
    // Azure DevOps specific
    "Custom.Tokens": 15000,
    "Microsoft.VSTS.Common.Priority": "1",
    "System.Tags": "authentication;security",
    
    // GitHub specific (via labels)
    "labels": ["enhancement", "security", "high-priority"],
    
    // GitLab specific
    "labels": ["authentication", "backend"],
    "milestone": "v2.1.0"
  }
}
```

---

## 📖 **Resources & Support**

### **Documentation**

- **API Reference**: [https://your-mcp-server.vercel.app/docs](https://your-mcp-server.vercel.app/docs)
- **User Guide**: [https://your-mcp-server.vercel.app/api/docs/user-guide](https://your-mcp-server.vercel.app/api/docs/user-guide)
- **Examples**: [https://your-mcp-server.vercel.app/api/docs/examples](https://your-mcp-server.vercel.app/api/docs/examples)
- **Deployment Guide**: [./DEPLOYMENT.md](./DEPLOYMENT.md)

### **Platform Documentation**

- **Azure DevOps REST API**: [https://docs.microsoft.com/en-us/rest/api/azure/devops/](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
- **GitHub REST API**: [https://docs.github.com/en/rest](https://docs.github.com/en/rest)
- **GitLab REST API**: [https://docs.gitlab.com/ee/api/](https://docs.gitlab.com/ee/api/)
- **MCP Specification**: [https://spec.modelcontextprotocol.io/](https://spec.modelcontextprotocol.io/)

### **Community & Support**

- **GitHub Repository**: [https://github.com/Jita81/ADOMCP](https://github.com/Jita81/ADOMCP)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/Jita81/ADOMCP/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/Jita81/ADOMCP/discussions)

---

**🎊 The Azure DevOps Multi-Platform MCP provides the perfect foundation for AI agents managing complex development workflows across multiple platforms while maintaining precise context boundaries for optimal performance!**
