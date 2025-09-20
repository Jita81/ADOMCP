"""
Real GitHub API integration endpoint
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle GitHub API operations"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            action = data.get('action')
            config = data.get('config', {})
            
            # Required configuration
            github_token = config.get('github_token')
            repository = config.get('repository')  # Format: "owner/repo"
            
            if not all([github_token, repository]):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "Missing required configuration",
                    "required": ["github_token", "repository"],
                    "example": {
                        "action": "test_connection",
                        "config": {
                            "github_token": "ghp_your-token",
                            "repository": "owner/repo-name"
                        }
                    }
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            if action == "test_connection":
                result = self._test_github_connection(github_token, repository)
            elif action == "create_issue":
                issue_data = data.get('issue', {})
                result = self._create_issue(github_token, repository, issue_data)
            elif action == "get_issue":
                issue_number = data.get('issue_number')
                result = self._get_issue(github_token, repository, issue_number)
            elif action == "update_issue":
                issue_number = data.get('issue_number')
                updates = data.get('updates', {})
                result = self._update_issue(github_token, repository, issue_number, updates)
            elif action == "list_issues":
                filters = data.get('filters', {})
                result = self._list_issues(github_token, repository, filters)
            elif action == "get_repository":
                result = self._get_repository(github_token, repository)
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "Invalid action",
                    "available_actions": ["test_connection", "create_issue", "get_issue", "update_issue", "list_issues", "get_repository"]
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            self.send_response(200 if result.get('success') else 500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": "Invalid JSON in request body"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "error": f"Internal server error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            return
    
    def _make_github_request(self, url, method='GET', data=None, github_token=None):
        """Make HTTP request to GitHub API"""
        try:
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'ADOMCP-Integration/1.0'
            }
            
            if data:
                data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                return {
                    'success': True,
                    'status_code': response.status,
                    'data': json.loads(response_data) if response_data else None
                }
                
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_data)
            except:
                error_json = {"message": error_data}
            
            return {
                'success': False,
                'status_code': e.code,
                'error': error_json
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_github_connection(self, github_token, repository):
        """Test GitHub API connection"""
        url = f"https://api.github.com/repos/{repository}"
        result = self._make_github_request(url, github_token=github_token)
        
        if result['success']:
            repo_data = result['data']
            return {
                'success': True,
                'message': 'GitHub connection successful',
                'repository': {
                    'id': repo_data.get('id'),
                    'name': repo_data.get('name'),
                    'full_name': repo_data.get('full_name'),
                    'description': repo_data.get('description'),
                    'private': repo_data.get('private'),
                    'default_branch': repo_data.get('default_branch'),
                    'html_url': repo_data.get('html_url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'GitHub connection failed',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_issue(self, github_token, repository, issue_data):
        """Create an issue in GitHub"""
        url = f"https://api.github.com/repos/{repository}/issues"
        
        issue_payload = {
            'title': issue_data.get('title', 'New Issue'),
            'body': issue_data.get('body', ''),
        }
        
        # Optional fields
        if 'labels' in issue_data:
            issue_payload['labels'] = issue_data['labels']
        if 'assignees' in issue_data:
            issue_payload['assignees'] = issue_data['assignees']
        if 'milestone' in issue_data:
            issue_payload['milestone'] = issue_data['milestone']
        
        result = self._make_github_request(url, method='POST', data=issue_payload, github_token=github_token)
        
        if result['success']:
            issue = result['data']
            return {
                'success': True,
                'message': 'GitHub issue created successfully',
                'issue': {
                    'id': issue.get('id'),
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'html_url': issue.get('html_url'),
                    'created_at': issue.get('created_at')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to create GitHub issue',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_issue(self, github_token, repository, issue_number):
        """Get an issue from GitHub"""
        if not issue_number:
            return {
                'success': False,
                'message': 'issue_number is required'
            }
        
        url = f"https://api.github.com/repos/{repository}/issues/{issue_number}"
        result = self._make_github_request(url, github_token=github_token)
        
        if result['success']:
            issue = result['data']
            return {
                'success': True,
                'message': 'GitHub issue retrieved successfully',
                'issue': {
                    'id': issue.get('id'),
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'body': issue.get('body'),
                    'state': issue.get('state'),
                    'labels': [label['name'] for label in issue.get('labels', [])],
                    'assignees': [assignee['login'] for assignee in issue.get('assignees', [])],
                    'created_at': issue.get('created_at'),
                    'updated_at': issue.get('updated_at'),
                    'html_url': issue.get('html_url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to retrieve GitHub issue',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_issue(self, github_token, repository, issue_number, updates):
        """Update an issue in GitHub"""
        if not issue_number:
            return {
                'success': False,
                'message': 'issue_number is required'
            }
        
        url = f"https://api.github.com/repos/{repository}/issues/{issue_number}"
        result = self._make_github_request(url, method='PATCH', data=updates, github_token=github_token)
        
        if result['success']:
            issue = result['data']
            return {
                'success': True,
                'message': 'GitHub issue updated successfully',
                'issue': {
                    'id': issue.get('id'),
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'html_url': issue.get('html_url'),
                    'updated_at': issue.get('updated_at')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to update GitHub issue',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _list_issues(self, github_token, repository, filters):
        """List issues from GitHub"""
        url = f"https://api.github.com/repos/{repository}/issues"
        
        # Add query parameters
        params = {}
        if 'state' in filters:
            params['state'] = filters['state']
        if 'labels' in filters:
            params['labels'] = ','.join(filters['labels'])
        if 'assignee' in filters:
            params['assignee'] = filters['assignee']
        if 'per_page' in filters:
            params['per_page'] = min(filters['per_page'], 100)  # GitHub limit
        
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        result = self._make_github_request(url, github_token=github_token)
        
        if result['success']:
            issues = result['data']
            issue_list = []
            
            for issue in issues:
                # Skip pull requests (they appear in issues API)
                if 'pull_request' not in issue:
                    issue_list.append({
                        'id': issue.get('id'),
                        'number': issue.get('number'),
                        'title': issue.get('title'),
                        'state': issue.get('state'),
                        'labels': [label['name'] for label in issue.get('labels', [])],
                        'created_at': issue.get('created_at'),
                        'html_url': issue.get('html_url')
                    })
            
            return {
                'success': True,
                'message': f'Found {len(issue_list)} GitHub issues',
                'issues': issue_list,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to list GitHub issues',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_repository(self, github_token, repository):
        """Get repository information"""
        url = f"https://api.github.com/repos/{repository}"
        result = self._make_github_request(url, github_token=github_token)
        
        if result['success']:
            repo = result['data']
            return {
                'success': True,
                'message': 'Repository information retrieved successfully',
                'repository': {
                    'id': repo.get('id'),
                    'name': repo.get('name'),
                    'full_name': repo.get('full_name'),
                    'description': repo.get('description'),
                    'private': repo.get('private'),
                    'default_branch': repo.get('default_branch'),
                    'language': repo.get('language'),
                    'size': repo.get('size'),
                    'stargazers_count': repo.get('stargazers_count'),
                    'forks_count': repo.get('forks_count'),
                    'open_issues_count': repo.get('open_issues_count'),
                    'created_at': repo.get('created_at'),
                    'updated_at': repo.get('updated_at'),
                    'html_url': repo.get('html_url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to get repository information',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def do_GET(self):
        """Get GitHub integration information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "service": "GitHub Real API Integration",
            "version": "1.0.0",
            "available_actions": [
                "test_connection",
                "create_issue",
                "get_issue",
                "update_issue", 
                "list_issues",
                "get_repository"
            ],
            "example_request": {
                "action": "test_connection",
                "config": {
                    "github_token": "ghp_your-token",
                    "repository": "owner/repo-name"
                }
            },
            "timestamp": datetime.now().isoformat(),
            "note": "This endpoint makes real API calls to GitHub"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
