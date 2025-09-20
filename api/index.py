"""
Minimal test deployment for Vercel
"""

def handler(request, response):
    """Simple handler for Vercel"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "status": "healthy",
            "service": "Azure DevOps Multi-Platform MCP",
            "message": "Vercel deployment successful!",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
