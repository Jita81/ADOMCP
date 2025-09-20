"""
Real Azure DevOps API integration endpoint
"""

import json
import base64
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Azure DevOps API operations"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            action = data.get('action')
            config = data.get('config', {})
            
            # Required configuration
            organization_url = config.get('organization_url')
            pat_token = config.get('pat_token')
            project = config.get('project')
            
            if not all([organization_url, pat_token, project]):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "Missing required configuration",
                    "required": ["organization_url", "pat_token", "project"],
                    "example": {
                        "action": "test_connection",
                        "config": {
                            "organization_url": "https://dev.azure.com/YourOrg",
                            "pat_token": "your-pat-token",
                            "project": "ProjectName"
                        }
                    }
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            if action == "test_connection":
                result = self._test_azure_devops_connection(organization_url, pat_token, project)
            elif action == "create_work_item":
                work_item_data = data.get('work_item', {})
                result = self._create_work_item(organization_url, pat_token, project, work_item_data)
            elif action == "get_work_item":
                work_item_id = data.get('work_item_id')
                result = self._get_work_item(organization_url, pat_token, project, work_item_id)
            elif action == "update_work_item":
                work_item_id = data.get('work_item_id')
                updates = data.get('updates', {})
                result = self._update_work_item(organization_url, pat_token, project, work_item_id, updates)
            elif action == "list_work_items":
                wiql = data.get('wiql', "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project")
                result = self._list_work_items(organization_url, pat_token, project, wiql)
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "error": "Invalid action",
                    "available_actions": ["test_connection", "create_work_item", "get_work_item", "update_work_item", "list_work_items"]
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
    
    def _encode_pat(self, pat_token):
        """Encode PAT token for Basic Auth"""
        return base64.b64encode(f":{pat_token}".encode()).decode()
    
    def _make_api_request(self, url, method='GET', data=None, headers=None):
        """Make HTTP request to Azure DevOps API"""
        try:
            if headers is None:
                headers = {}
            
            if data:
                data = json.dumps(data).encode('utf-8')
                if 'Content-Type' not in headers:
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
    
    def _test_azure_devops_connection(self, organization_url, pat_token, project):
        """Test Azure DevOps API connection"""
        auth_header = f'Basic {self._encode_pat(pat_token)}'
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }
        
        # Test project access
        url = f"{organization_url}/_apis/projects/{project}?api-version=7.1"
        result = self._make_api_request(url, headers=headers)
        
        if result['success']:
            project_data = result['data']
            return {
                'success': True,
                'message': 'Azure DevOps connection successful',
                'project': {
                    'id': project_data.get('id'),
                    'name': project_data.get('name'),
                    'description': project_data.get('description'),
                    'state': project_data.get('state')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Azure DevOps connection failed',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_work_item(self, organization_url, pat_token, project, work_item_data):
        """Create a work item in Azure DevOps"""
        auth_header = f'Basic {self._encode_pat(pat_token)}'
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json-patch+json'
        }
        
        work_item_type = work_item_data.get('type', 'User Story')
        title = work_item_data.get('title', 'Test Work Item')
        description = work_item_data.get('description', '')
        
        # Build patch document
        patch_document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            }
        ]
        
        if description:
            patch_document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": description
            })
        
        # Add any additional fields
        fields = work_item_data.get('fields', {})
        for field_path, field_value in fields.items():
            patch_document.append({
                "op": "add",
                "path": f"/fields/{field_path}",
                "value": field_value
            })
        
        encoded_work_item_type = urllib.parse.quote(work_item_type)
        url = f"{organization_url}/{project}/_apis/wit/workitems/${encoded_work_item_type}?api-version=7.1"
        result = self._make_api_request(url, method='POST', data=patch_document, headers=headers)
        
        if result['success']:
            work_item = result['data']
            return {
                'success': True,
                'message': f'Work item created successfully',
                'work_item': {
                    'id': work_item.get('id'),
                    'title': work_item['fields'].get('System.Title'),
                    'type': work_item['fields'].get('System.WorkItemType'),
                    'state': work_item['fields'].get('System.State'),
                    'url': work_item.get('url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to create work item',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_work_item(self, organization_url, pat_token, project, work_item_id):
        """Get a work item from Azure DevOps"""
        if not work_item_id:
            return {
                'success': False,
                'message': 'work_item_id is required'
            }
        
        auth_header = f'Basic {self._encode_pat(pat_token)}'
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json'
        }
        
        url = f"{organization_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        result = self._make_api_request(url, headers=headers)
        
        if result['success']:
            work_item = result['data']
            return {
                'success': True,
                'message': 'Work item retrieved successfully',
                'work_item': {
                    'id': work_item.get('id'),
                    'title': work_item['fields'].get('System.Title'),
                    'description': work_item['fields'].get('System.Description'),
                    'type': work_item['fields'].get('System.WorkItemType'),
                    'state': work_item['fields'].get('System.State'),
                    'assignee': work_item['fields'].get('System.AssignedTo', {}).get('displayName'),
                    'created_date': work_item['fields'].get('System.CreatedDate'),
                    'changed_date': work_item['fields'].get('System.ChangedDate'),
                    'url': work_item.get('url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to retrieve work item',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_work_item(self, organization_url, pat_token, project, work_item_id, updates):
        """Update a work item in Azure DevOps"""
        if not work_item_id:
            return {
                'success': False,
                'message': 'work_item_id is required'
            }
        
        auth_header = f'Basic {self._encode_pat(pat_token)}'
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json-patch+json'
        }
        
        # Build patch document
        patch_document = []
        for field_path, field_value in updates.items():
            patch_document.append({
                "op": "replace",
                "path": f"/fields/{field_path}",
                "value": field_value
            })
        
        url = f"{organization_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        result = self._make_api_request(url, method='PATCH', data=patch_document, headers=headers)
        
        if result['success']:
            work_item = result['data']
            return {
                'success': True,
                'message': 'Work item updated successfully',
                'work_item': {
                    'id': work_item.get('id'),
                    'title': work_item['fields'].get('System.Title'),
                    'type': work_item['fields'].get('System.WorkItemType'),
                    'state': work_item['fields'].get('System.State'),
                    'revision': work_item.get('rev'),
                    'url': work_item.get('url')
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to update work item',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _list_work_items(self, organization_url, pat_token, project, wiql):
        """List work items using WIQL query"""
        auth_header = f'Basic {self._encode_pat(pat_token)}'
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        query_data = {
            "query": wiql
        }
        
        url = f"{organization_url}/{project}/_apis/wit/wiql?api-version=7.1"
        result = self._make_api_request(url, method='POST', data=query_data, headers=headers)
        
        if result['success']:
            query_result = result['data']
            work_items = query_result.get('workItems', [])
            
            return {
                'success': True,
                'message': f'Found {len(work_items)} work items',
                'work_items': work_items,
                'query': wiql,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'message': 'Failed to list work items',
                'error': result.get('error'),
                'status_code': result.get('status_code'),
                'timestamp': datetime.now().isoformat()
            }
    
    def do_GET(self):
        """Get Azure DevOps integration information"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "service": "Azure DevOps Real API Integration",
            "version": "1.0.0",
            "available_actions": [
                "test_connection",
                "create_work_item", 
                "get_work_item",
                "update_work_item",
                "list_work_items"
            ],
            "example_request": {
                "action": "test_connection",
                "config": {
                    "organization_url": "https://dev.azure.com/YourOrg",
                    "pat_token": "your-pat-token",
                    "project": "ProjectName"
                }
            },
            "timestamp": datetime.now().isoformat(),
            "note": "This endpoint makes real API calls to Azure DevOps"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
