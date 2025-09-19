"""
Azure DevOps Multi-Platform MCP - Attachment Manager

This module handles work item attachment operations including:
- Creating and uploading attachments (including markdown documents)
- Reading existing attachments from work items
- Managing attachment metadata and content
- Support for chunked uploads for large files
"""

import asyncio
import aiohttp
import base64
import json
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Direct import from local types.py to avoid package import issues
import sys
import os
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Import from local types.py file specifically
import importlib.util
types_spec = importlib.util.spec_from_file_location("mcp_types", os.path.join(current_dir, "types.py"))
mcp_types = importlib.util.module_from_spec(types_spec)
types_spec.loader.exec_module(mcp_types)

WorkItemAttachment = mcp_types.WorkItemAttachment
OperationResult = mcp_types.OperationResult


class AttachmentManager:
    """Manages work item attachments for Azure DevOps Multi-Platform MCP"""

    def __init__(self, organization_url: str, pat: str):
        """
        Initialize the attachment manager
        
        Args:
            organization_url: Azure DevOps organization URL
            pat: Personal Access Token for authentication
        """
        self.organization_url = organization_url
        self.pat = pat
        self.headers = {
            'Authorization': f'Basic {base64.b64encode(f":{pat}".encode()).decode()}',
            'Accept': 'application/json'
        }

    async def upload_attachment(
        self, 
        content: str, 
        filename: str, 
        project: str,
        content_type: str = "text/markdown",
        comment: Optional[str] = None
    ) -> Optional[WorkItemAttachment]:
        """
        Upload content as an attachment to Azure DevOps
        
        Args:
            content: The content to upload (string for markdown)
            filename: Name of the file
            project: Project ID or name
            content_type: MIME type of the content
            comment: Optional comment for the attachment
            
        Returns:
            WorkItemAttachment object if successful, None otherwise
        """
        try:
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content

            # Prepare headers for upload
            upload_headers = self.headers.copy()
            upload_headers['Content-Type'] = 'application/octet-stream'

            # Build the upload URL
            url = f"{self.organization_url}/{project}/_apis/wit/attachments"
            params = {
                'fileName': filename,
                'api-version': '7.1'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=upload_headers,
                    params=params,
                    data=content_bytes
                ) as response:
                    
                    if response.status in [200, 201]:
                        result = await response.json()
                        
                        return WorkItemAttachment(
                            id=result['id'],
                            name=filename,
                            size=len(content_bytes),
                            url=result['url'],
                            content_type=content_type,
                            content=content if isinstance(content, str) else None,
                            upload_date=datetime.now(),
                            comment=comment
                        )
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to upload attachment: {response.status} - {error_text}")
                        return None

        except Exception as e:
            print(f"❌ Error uploading attachment: {str(e)}")
            return None

    async def upload_markdown_document(
        self,
        markdown_content: str,
        filename: str,
        project: str,
        comment: Optional[str] = None
    ) -> Optional[WorkItemAttachment]:
        """
        Upload a markdown document as an attachment
        
        Args:
            markdown_content: The markdown content as a string
            filename: Name of the markdown file (should end with .md)
            project: Project ID or name
            comment: Optional comment for the attachment
            
        Returns:
            WorkItemAttachment object if successful, None otherwise
        """
        if not filename.endswith('.md'):
            filename += '.md'
            
        return await self.upload_attachment(
            content=markdown_content,
            filename=filename,
            project=project,
            content_type="text/markdown",
            comment=comment or "Markdown document attachment"
        )

    async def get_work_item_attachments(
        self,
        work_item_id: int,
        project: str
    ) -> List[WorkItemAttachment]:
        """
        Get all attachments for a work item
        
        Args:
            work_item_id: The work item ID
            project: Project ID or name
            
        Returns:
            List of WorkItemAttachment objects
        """
        try:
            # First, get the work item to find its attachments
            url = f"{self.organization_url}/{project}/_apis/wit/workitems/{work_item_id}"
            params = {
                'api-version': '7.1',
                '$expand': 'relations'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        print(f"❌ Failed to get work item: {response.status}")
                        return []

                    work_item = await response.json()
                    relations = work_item.get('relations', [])
                    
                    attachments = []
                    for relation in relations:
                        if relation.get('rel') == 'AttachedFile':
                            attachment_url = relation.get('url', '')
                            attributes = relation.get('attributes', {})
                            
                            # Extract attachment details
                            attachment_id = attachment_url.split('/')[-1].split('?')[0] if attachment_url else ''
                            filename = attributes.get('name', 'unknown')
                            size = attributes.get('resourceSize', 0)
                            comment = attributes.get('comment', '')
                            
                            # Determine content type from filename
                            content_type, _ = mimetypes.guess_type(filename)
                            if not content_type:
                                content_type = 'application/octet-stream'
                            
                            # For markdown files, try to download the content
                            content = None
                            if filename.endswith('.md') or content_type == 'text/markdown':
                                content = await self._download_attachment_content(attachment_url)
                            
                            attachment = WorkItemAttachment(
                                id=attachment_id,
                                name=filename,
                                size=size,
                                url=attachment_url,
                                content_type=content_type,
                                content=content,
                                comment=comment
                            )
                            attachments.append(attachment)

                    return attachments

        except Exception as e:
            print(f"❌ Error getting work item attachments: {str(e)}")
            return []

    async def _download_attachment_content(self, attachment_url: str) -> Optional[str]:
        """
        Download attachment content (specifically for text/markdown files)
        
        Args:
            attachment_url: The URL of the attachment
            
        Returns:
            Content as string if successful and text-based, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment_url, headers=self.headers) as response:
                    if response.status == 200:
                        # Try to decode as text
                        content = await response.read()
                        try:
                            return content.decode('utf-8')
                        except UnicodeDecodeError:
                            # Not a text file
                            return None
                    else:
                        return None
        except Exception as e:
            print(f"❌ Error downloading attachment content: {str(e)}")
            return None

    async def attach_to_work_item(
        self,
        work_item_id: int,
        project: str,
        attachment: WorkItemAttachment,
        comment: Optional[str] = None
    ) -> bool:
        """
        Attach an uploaded attachment to a work item
        
        Args:
            work_item_id: The work item ID
            project: Project ID or name
            attachment: The WorkItemAttachment object (already uploaded)
            comment: Optional comment for the attachment relation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the attachment relation
            operations = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "AttachedFile",
                        "url": attachment.url,
                        "attributes": {
                            "comment": comment or attachment.comment or f"Attached {attachment.name}",
                            "name": attachment.name,
                            "resourceSize": attachment.size
                        }
                    }
                }
            ]

            url = f"{self.organization_url}/{project}/_apis/wit/workitems/{work_item_id}"
            params = {'api-version': '7.1'}
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    url,
                    headers=headers,
                    params=params,
                    json=operations
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"❌ Error attaching to work item: {str(e)}")
            return False

    async def upload_and_attach_markdown(
        self,
        work_item_id: int,
        project: str,
        markdown_content: str,
        filename: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Upload a markdown document and attach it to a work item in one operation
        
        Args:
            work_item_id: The work item ID
            project: Project ID or name
            markdown_content: The markdown content
            filename: Name of the file
            comment: Optional comment
            
        Returns:
            True if successful, False otherwise
        """
        # First upload the attachment
        attachment = await self.upload_markdown_document(
            markdown_content=markdown_content,
            filename=filename,
            project=project,
            comment=comment
        )
        
        if not attachment:
            return False
            
        # Then attach it to the work item
        return await self.attach_to_work_item(
            work_item_id=work_item_id,
            project=project,
            attachment=attachment,
            comment=comment
        )

    async def create_work_item_with_attachments(
        self,
        project: str,
        work_item_type: str,
        title: str,
        description: str,
        attachments: List[WorkItemAttachment],
        fields: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Create a work item and attach multiple attachments to it
        
        Args:
            project: Project ID or name
            work_item_type: Type of work item (User Story, Task, Bug, etc.)
            title: Work item title
            description: Work item description
            attachments: List of already uploaded attachments
            fields: Additional fields to set
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # First create the work item
            operations = [
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.Description", "value": description}
            ]
            
            # Add any additional fields
            if fields:
                for field_name, field_value in fields.items():
                    operations.append({
                        "op": "add",
                        "path": f"/fields/{field_name}",
                        "value": field_value
                    })
            
            # Add attachment relations
            for attachment in attachments:
                operations.append({
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "AttachedFile",
                        "url": attachment.url,
                        "attributes": {
                            "comment": attachment.comment or f"Attached {attachment.name}",
                            "name": attachment.name,
                            "resourceSize": attachment.size
                        }
                    }
                })

            url = f"{self.organization_url}/{project}/_apis/wit/workitems/${work_item_type}"
            params = {'api-version': '7.1'}
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    params=params,
                    json=operations
                ) as response:
                    
                    if response.status in [200, 201]:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create work item with attachments: {response.status} - {error_text}")
                        return None

        except Exception as e:
            print(f"❌ Error creating work item with attachments: {str(e)}")
            return None
