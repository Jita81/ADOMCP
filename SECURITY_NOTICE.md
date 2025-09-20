# 🚨 CRITICAL SECURITY UPDATE - AUTHENTICATION REQUIRED

## ⚠️ IMPORTANT NOTICE

**The ADOMCP API now requires authentication to prevent unauthorized access.**

### 🔒 What Changed

Previously, the API only required an email address (`user_id`) to access and manipulate API keys and work items. This created a **critical security vulnerability** where anyone knowing someone's email could:

- Access their stored API keys
- Create work items on their behalf  
- Manipulate their Azure DevOps/GitHub projects
- Upload attachments to their work items

### ✅ Security Fix Implemented

ADOMCP now implements **proper authentication** with:

- **API Key Authentication**: Each user gets a unique, secure API key
- **User Isolation**: Users can only access their own resources
- **Scope-Based Authorization**: Different permissions for different operations
- **Token Expiry**: API keys expire after 1 year
- **Audit Logging**: All access attempts are logged

### 🚀 How to Use the Secure API

#### Step 1: Register and Get Your API Key

```bash
curl -X POST https://adomcp.vercel.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@company.com",
    "purpose": "ADOMCP API access"
  }'
```

**Response:**
```json
{
  "status": "success",
  "api_key": "adomcp_v1_a1b2c3d4_1671234567_0123456789abcdef",
  "scopes": ["read", "write", "manage_keys"],
  "expires_in_days": 365
}
```

#### Step 2: Store Your Platform API Keys Securely

```bash
curl -X POST https://adomcp.vercel.app/api/secure-keys \
  -H "Authorization: Bearer adomcp_v1_a1b2c3d4_1671234567_0123456789abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "azure_devops",
    "api_key": "your-azure-devops-pat",
    "organization_url": "https://dev.azure.com/YourOrg"
  }'
```

#### Step 3: Use the Secure MCP Protocol

```bash
curl -X POST https://adomcp.vercel.app/api/secure-mcp \
  -H "Authorization: Bearer adomcp_v1_a1b2c3d4_1671234567_0123456789abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_work_item",
      "arguments": {
        "platform": "azure_devops",
        "title": "Secure Work Item",
        "work_item_type": "Task"
      }
    },
    "id": 1
  }'
```

### 🔄 Migration from Insecure API

#### ❌ Old (Insecure) Endpoints - DO NOT USE

These endpoints are **deprecated** and **insecure**:
- `/api/keys` - No authentication required
- `/api/mcp` - No authentication required

#### ✅ New (Secure) Endpoints - USE THESE

- `/api/auth` - Register and get API key
- `/api/secure-keys` - Authenticated key management
- `/api/secure-mcp` - Authenticated MCP protocol

### 🛡️ Security Features

#### **Authentication**
- **API Key Format**: `adomcp_v1_<user_hash>_<timestamp>_<random>`
- **HMAC Signatures**: Keys are cryptographically signed
- **Expiry**: Keys expire after 1 year
- **Scopes**: Read, write, and manage_keys permissions

#### **Authorization**
- **User Isolation**: Users can only access their own resources
- **Resource Validation**: All requests validated against authenticated user
- **Scope Checking**: Operations require appropriate permissions

#### **Security Headers**
- **Rate Limiting**: Prevents abuse and brute force
- **Request Validation**: Input sanitization and size limits
- **Correlation IDs**: For tracking and debugging
- **Audit Logging**: All access attempts logged

### 📊 Current Deployment Status

**Secure endpoints are now available at:**
- ✅ `https://adomcp.vercel.app/api/auth` (registration)
- ✅ `https://adomcp.vercel.app/api/secure-keys` (authenticated key management)
- ✅ `https://adomcp.vercel.app/api/secure-mcp` (authenticated MCP protocol)

**Legacy insecure endpoints still exist for backward compatibility but should not be used.**

### 🎯 Recommended Actions

1. **Register immediately** at `/api/auth` to get your secure API key
2. **Update your integrations** to use secure endpoints
3. **Store API keys securely** in your environment/secrets manager
4. **Test your applications** with the new authentication
5. **Monitor logs** for any unauthorized access attempts

### 🆘 Support

If you have any questions about the security update:

- **Documentation**: See updated README.md and ADVANCED_DEPLOYMENT.md
- **Issues**: Create an issue at https://github.com/Jita81/ADOMCP/issues
- **Security Concerns**: Contact the maintainers immediately

### 📝 Implementation Details

The authentication system uses:

- **Memory-based storage** (for this deployment)
- **AES-GCM encryption** for platform API keys
- **HMAC-SHA256** for API key signatures
- **Rate limiting** for all endpoints
- **Correlation IDs** for request tracking

In production deployments with Supabase, tokens and encrypted API keys are stored in a secure database with Row Level Security.

---

**Thank you for helping us maintain the security of ADOMCP! 🙏**

This update ensures that only authorized users can access the API and protects against unauthorized access to sensitive API keys and work items.
