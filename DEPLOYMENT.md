# Azure DevOps Multi-Platform MCP - Production Deployment Guide

## 🚀 **Production Deployment with Vercel + Supabase**

This guide covers deploying the Azure DevOps Multi-Platform MCP to production using Vercel for hosting and Supabase for secure API key storage.

### 📋 **Prerequisites**

- **Vercel Account**: [https://vercel.com](https://vercel.com)
- **Supabase Account**: [https://supabase.com](https://supabase.com)
- **GitHub Repository**: Forked or cloned ADOMCP repository
- **API Keys**: Azure DevOps PAT, GitHub Token, GitLab Token (as needed)

---

## 🔧 **Step 1: Supabase Setup**

### **1.1 Create Supabase Project**

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Login to Supabase
supabase login

# Create new project (or use existing)
supabase projects create azure-devops-mcp --org-id your-org-id
```

### **1.2 Configure Database**

```bash
# Link to your Supabase project
supabase link --project-ref your-project-ref

# Run migrations to create API keys table
supabase db push
```

### **1.3 Get Supabase Configuration**

From your Supabase dashboard, collect:
- **Project URL**: `https://your-project-ref.supabase.co`
- **Anon Key**: Public anonymous key
- **Service Key**: Service role secret key (keep secure!)

---

## ⚡ **Step 2: Vercel Deployment**

### **2.1 Install Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login
```

### **2.2 Deploy to Vercel**

```bash
# From repository root
vercel

# Follow prompts:
# - Set up and deploy: Y
# - Which scope: Select your account/team
# - Link to existing project: N (for new deployment)
# - What's your project's name: azure-devops-mcp
# - In which directory is your code located: ./
```

### **2.3 Configure Environment Variables**

In Vercel dashboard or via CLI:

```bash
# Set Supabase configuration
vercel env add SUPABASE_URL
# Enter: https://your-project-ref.supabase.co

vercel env add SUPABASE_ANON_KEY
# Enter: your-anon-key

vercel env add SUPABASE_SERVICE_KEY
# Enter: your-service-key

# Set MCP configuration
vercel env add MCP_SERVER_NAME
# Enter: Azure DevOps Multi-Platform MCP

vercel env add MCP_SERVER_VERSION
# Enter: 2.1.0
```

### **2.4 Deploy with Environment Variables**

```bash
# Redeploy with environment variables
vercel --prod
```

---

## 🔐 **Step 3: Secure API Key Storage**

### **3.1 Store Your API Keys**

Once deployed, store your platform API keys securely:

```bash
# Store Azure DevOps PAT
curl -X POST https://your-vercel-app.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-unique-user-id",
    "platform": "azure_devops",
    "api_key": "your-azure-devops-pat",
    "organization_url": "https://dev.azure.com/YourOrg",
    "project_id": "your-project-guid"
  }'

# Store GitHub Token
curl -X POST https://your-vercel-app.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-unique-user-id",
    "platform": "github",
    "api_key": "ghp_your-github-token"
  }'

# Store GitLab Token (optional)
curl -X POST https://your-vercel-app.vercel.app/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-unique-user-id",
    "platform": "gitlab",
    "api_key": "glpat-your-gitlab-token"
  }'
```

### **3.2 Verify API Key Storage**

```bash
# Test health endpoint
curl https://your-vercel-app.vercel.app/api/health

# Test MCP capabilities
curl https://your-vercel-app.vercel.app/api/capabilities
```

---

## 🤖 **Step 4: MCP Client Integration**

### **4.1 Configure MCP Client**

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "azure-devops-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://your-vercel-app.vercel.app/api/mcp",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

### **4.2 Test MCP Connection**

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "Your MCP Client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

---

## 📚 **Step 5: Using the Deployed MCP**

### **5.1 Available Endpoints**

- **Health Check**: `GET /api/health`
- **MCP Protocol**: `POST /api/mcp`
- **API Keys**: `POST /api/keys`
- **Work Items**: `POST /api/work-items`
- **Documentation**: `GET /api/docs/user-guide`
- **Examples**: `GET /api/docs/examples`

### **5.2 MCP Tools Available**

- **create_work_item**: Create work items across platforms
- **upload_attachment**: Add markdown documents to work items
- **create_epic_feature_story**: Create hierarchical structures
- **link_commits_prs**: Connect development artifacts

### **5.3 Example MCP Usage**

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_work_item",
    "arguments": {
      "user_id": "your-user-id",
      "platform": "azure_devops",
      "work_item_type": "Epic",
      "title": "Authentication System Implementation",
      "description": "Complete OAuth-based authentication system"
    }
  },
  "id": 2
}
```

---

## 🔒 **Security Considerations**

### **API Key Encryption**
- Keys are base64 encoded in Supabase (enhance with proper encryption for production)
- Row Level Security (RLS) enabled on api_keys table
- Service role key required for backend operations

### **Environment Variables**
- All sensitive configuration stored in Vercel environment variables
- Supabase service key never exposed to client-side code
- User isolation via user_id in all operations

### **Production Recommendations**
- Implement proper API key encryption (AES-256)
- Add API rate limiting
- Enable Vercel Analytics and monitoring
- Set up Supabase database backups
- Configure custom domain with SSL

---

## 🚀 **Scaling Considerations**

### **Vercel Limits**
- Function execution time: 30 seconds (configurable)
- Concurrent function executions: 1000 (Pro plan)
- Edge function locations available globally

### **Supabase Limits**
- Free tier: 500MB database, 2GB bandwidth
- Pro tier: 8GB database, 250GB bandwidth
- Upgrade as usage grows

### **Performance Optimization**
- Enable Vercel Edge Functions for faster response times
- Use Supabase connection pooling for database efficiency
- Implement caching for frequently accessed data
- Monitor function execution times and optimize

---

## 📊 **Monitoring & Maintenance**

### **Vercel Analytics**
- Enable Vercel Analytics for function performance
- Monitor error rates and response times
- Set up alerts for function failures

### **Supabase Monitoring**
- Monitor database performance in Supabase dashboard
- Track API key storage and retrieval patterns
- Set up database backup schedules

### **Health Checks**
- Automated health check at `/api/health`
- MCP capabilities verification
- API key storage validation

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Deployment Failed**
```bash
# Check Vercel logs
vercel logs

# Verify environment variables
vercel env ls
```

**Supabase Connection Issues**
```bash
# Test Supabase connection
supabase projects list

# Check migration status
supabase db diff
```

**MCP Integration Problems**
- Verify endpoint URLs in MCP client configuration
- Check API key storage with test requests
- Validate JSON-RPC request format

### **Debug Commands**

```bash
# Test deployment health
curl https://your-app.vercel.app/api/health

# Test MCP initialization
curl -X POST https://your-app.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'

# Check Vercel function logs
vercel logs --follow
```

---

## ✅ **Production Checklist**

- [ ] Supabase project created and configured
- [ ] Database migrations applied successfully
- [ ] Vercel deployment completed
- [ ] Environment variables configured
- [ ] API keys stored securely
- [ ] MCP client integration tested
- [ ] Health endpoints responding
- [ ] Documentation accessible
- [ ] Monitoring and alerts configured
- [ ] Backup and recovery plan established

**🎊 Your Azure DevOps Multi-Platform MCP is now production-ready!**

For support and advanced configuration, see the [User Guide](./USER_GUIDE.md) and [API Documentation](https://your-app.vercel.app/docs).
