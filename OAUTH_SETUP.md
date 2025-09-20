# 🔐 OAuth Authentication Setup Guide

## Overview

ADOMCP now supports OAuth authentication with GitHub, Google, and Microsoft providers. This provides a more secure and user-friendly authentication experience compared to API keys.

## 🎯 Benefits of OAuth

- **Security**: No need to share or store API keys
- **User Experience**: Familiar login flow with trusted providers
- **Permissions**: Granular access control via OAuth scopes
- **Revocation**: Users can revoke access anytime from provider settings
- **Identity**: Real user identity verification

## 🛠️ OAuth Provider Setup

### GitHub OAuth Application

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Create a new OAuth App with:
   - **Application name**: `ADOMCP - Your Instance`
   - **Homepage URL**: `https://adomcp.vercel.app`
   - **Authorization callback URL**: `https://adomcp.vercel.app/api/oauth/callback/github`
3. Save the **Client ID** and **Client Secret**

### Google OAuth Application

1. Go to [Google Cloud Console](https://console.developers.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 Client ID:
   - **Application type**: Web application
   - **Authorized redirect URIs**: `https://adomcp.vercel.app/api/oauth/callback/google`
5. Save the **Client ID** and **Client Secret**

### Microsoft OAuth Application

1. Go to [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Register a new application:
   - **Name**: `ADOMCP - Your Instance`
   - **Redirect URI**: `https://adomcp.vercel.app/api/oauth/callback/microsoft`
3. Go to Certificates & secrets, create new client secret
4. Save the **Application (client) ID** and **Client Secret**

## 🔧 Environment Variables

Add these to your Vercel environment variables or `.env` file:

```bash
# GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret

# Google OAuth (optional)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth (optional)
MICROSOFT_OAUTH_CLIENT_ID=your-microsoft-client-id
MICROSOFT_OAUTH_CLIENT_SECRET=your-microsoft-client-secret
```

## 🚀 OAuth Authentication Flow

### 1. Initiate Login

```bash
# See available providers
curl https://adomcp.vercel.app/api/oauth

# Start GitHub OAuth flow
curl https://adomcp.vercel.app/api/oauth/login?provider=github
```

### 2. User Authorization

User is redirected to provider (GitHub/Google/Microsoft) to authorize your application.

### 3. Callback Processing

Provider redirects back to `/api/oauth/callback/{provider}` with authorization code.

### 4. Session Token

User receives HTML page with session token:
```
adomcp_oauth_github_a1b2c3d4_1671234567
```

### 5. Authenticated Requests

Use session token in API requests:

```bash
curl -H "Authorization: Bearer adomcp_oauth_github_a1b2c3d4_1671234567" \
     https://adomcp.vercel.app/api/oauth_mcp \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 🔍 OAuth Endpoints

### Authentication Endpoints

- **GET /api/oauth** - OAuth service information
- **GET /api/oauth/login?provider={provider}** - Initiate OAuth flow
- **GET /api/oauth/callback/{provider}** - OAuth callback handler
- **GET /api/oauth/logout** - Logout (requires Authorization header)
- **GET /api/oauth/status** - Check authentication status

### Protected Endpoints

- **GET/POST /api/oauth_mcp** - OAuth-protected MCP JSON-RPC

## 🧪 Testing OAuth

### Check Available Providers

```bash
curl https://adomcp.vercel.app/api/oauth
```

### Test Protected Endpoint (Unauthorized)

```bash
curl https://adomcp.vercel.app/api/oauth_mcp
# Returns: OAuth authentication required
```

### Test Protected Endpoint (Authorized)

```bash
curl -H "Authorization: Bearer your-oauth-session-token" \
     https://adomcp.vercel.app/api/oauth_mcp \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 🔐 Security Features

### CSRF Protection
- State parameters prevent cross-site request forgery
- Secure random state generation and validation

### Session Management
- Time-limited sessions with automatic expiry
- Refresh token support for long-lived access
- Secure session token generation

### User Isolation
- Each user can only access their own resources
- Provider-based user identity verification
- Granular permission scopes

## 🎯 Integration with MCP Clients

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "adomcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "FETCH_URL": "https://adomcp.vercel.app/api/oauth_mcp",
        "FETCH_HEADERS": "Authorization: Bearer your-oauth-session-token"
      }
    }
  }
}
```

### Direct HTTP Integration

```javascript
const headers = {
  'Authorization': 'Bearer adomcp_oauth_github_...',
  'Content-Type': 'application/json'
};

const response = await fetch('https://adomcp.vercel.app/api/oauth_mcp', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/list',
    id: 1
  })
});
```

## 🆘 Troubleshooting

### Common Issues

1. **"Provider not configured"**
   - Check environment variables are set correctly
   - Verify OAuth app settings match callback URLs

2. **"Invalid state parameter"**
   - CSRF protection triggered
   - Start fresh OAuth flow

3. **"Authentication failed"**
   - Check OAuth app permissions
   - Verify callback URL configuration

### Debug Information

```bash
# Check OAuth status
curl -H "Authorization: Bearer your-token" \
     https://adomcp.vercel.app/api/oauth/status

# View provider configuration
curl https://adomcp.vercel.app/api/oauth
```

## 🔄 Migration from API Key Auth

If you were using the previous API key authentication:

1. **Keep existing API keys** for backward compatibility
2. **New users** should use OAuth authentication
3. **Gradually migrate** existing integrations to OAuth
4. **OAuth provides better security** and user experience

Both authentication methods will work simultaneously during the transition period.
