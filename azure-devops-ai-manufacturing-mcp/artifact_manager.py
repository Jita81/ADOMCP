"""
Azure DevOps AI Manufacturing MCP - Artifact Management

This module provides comprehensive Git platform integration with Azure DevOps focus,
supporting Azure Repos, GitHub, and GitLab with unified artifact attachment.
"""

import re
import aiohttp
import base64
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime

from .interface import ArtifactManagerInterface
from .types import (
    ArtifactResult, ArtifactLink, CommitArtifact, PullRequestArtifact,
    GitProvider, OperationResult
)


class ArtifactManager(ArtifactManagerInterface):
    """
    Comprehensive Git platform integration with Azure DevOps
    
    Supports Azure Repos, GitHub, and GitLab with unified interface
    for artifact attachment, monitoring, and synchronization.
    """
    
    def __init__(self, azure_repos_token: Optional[str] = None, github_token: Optional[str] = None,
                 gitlab_token: Optional[str] = None, default_provider: str = 'azure_repos'):
        """
        Initialize artifact manager with multi-platform Git integration
        
        Args:
            azure_repos_token: Azure DevOps Personal Access Token
            github_token: GitHub Personal Access Token
            gitlab_token: GitLab Personal Access Token
            default_provider: Default Git provider ('azure_repos', 'github', 'gitlab')
        """
        self.azure_repos_client = AzureReposClient(azure_repos_token) if azure_repos_token else None
        self.github_client = GitHubClient(github_token) if github_token else None
        self.gitlab_client = GitLabClient(gitlab_token) if gitlab_token else None
        self.default_provider = default_provider
        
        # Pattern for detecting work item mentions in commit messages
        self.work_item_pattern = re.compile(r'#(\d+)')
    
    async def attach_commit_artifacts(self, organization: str, project: str, work_item_id: int, 
                                    repository_url: str, commit_hashes: List[str]) -> ArtifactResult:
        """
        Attach commit artifacts to Azure DevOps work items
        
        Implementation:
        1. Detect repository provider (Azure Repos/GitHub/GitLab) from URL
        2. Fetch commit details (message, author, timestamp, files)
        3. Create Azure DevOps work item relations for commit links
        4. Update work item with commit metadata in custom fields
        5. Use Azure DevOps native Git integration for Azure Repos
        """
        try:
            # Detect Git provider from repository URL
            provider = self._detect_git_provider(repository_url)
            
            attached_artifacts = []
            successful_attachments = 0
            
            for commit_hash in commit_hashes:
                try:
                    # Fetch commit details from appropriate provider
                    commit_details = await self._fetch_commit_details(
                        provider, repository_url, commit_hash
                    )
                    
                    if commit_details:
                        # Create Azure DevOps work item relation
                        artifact_link = await self._create_commit_work_item_relation(
                            organization, project, work_item_id, commit_details
                        )
                        
                        if artifact_link:
                            attached_artifacts.append(artifact_link)
                            successful_attachments += 1
                
                except Exception as e:
                    print(f"Error attaching commit {commit_hash}: {str(e)}")
                    continue
            
            return ArtifactResult(
                success=successful_attachments > 0,
                artifact_count=successful_attachments,
                attached_artifacts=attached_artifacts,
                message=f"Successfully attached {successful_attachments}/{len(commit_hashes)} commits"
            )
            
        except Exception as e:
            return ArtifactResult(
                success=False,
                artifact_count=0,
                attached_artifacts=[],
                message=f"Error attaching commit artifacts: {str(e)}"
            )
    
    async def attach_pull_request_artifacts(self, organization: str, project: str, 
                                          work_item_id: int, pr_url: str) -> ArtifactResult:
        """
        Attach pull/merge request artifacts
        
        Implementation:
        1. Parse PR URL to determine provider and repository
        2. Fetch PR details (status, reviewers, checks, description)
        3. Monitor PR status changes and update work item accordingly
        4. Create work item relations for PR links
        5. Use Azure DevOps PR integration for Azure Repos
        """
        try:
            # Parse PR URL and detect provider
            provider, pr_details = await self._parse_pr_url_and_fetch_details(pr_url)
            
            if not pr_details:
                return ArtifactResult(
                    success=False,
                    artifact_count=0,
                    attached_artifacts=[],
                    message="Failed to fetch pull request details"
                )
            
            # Create Azure DevOps work item relation for PR
            artifact_link = await self._create_pr_work_item_relation(
                organization, project, work_item_id, pr_details
            )
            
            if artifact_link:
                return ArtifactResult(
                    success=True,
                    artifact_count=1,
                    attached_artifacts=[artifact_link],
                    message="Pull request artifact attached successfully"
                )
            else:
                return ArtifactResult(
                    success=False,
                    artifact_count=0,
                    attached_artifacts=[],
                    message="Failed to create work item relation for pull request"
                )
                
        except Exception as e:
            return ArtifactResult(
                success=False,
                artifact_count=0,
                attached_artifacts=[],
                message=f"Error attaching pull request artifact: {str(e)}"
            )
    
    async def monitor_repository_activity(self, repository_url: str, 
                                        work_item_patterns: List[str]) -> None:
        """
        Monitor repository for manufacturing-related activity
        
        Implementation:
        1. Set up service hooks for repository events (commits, PRs, builds)
        2. Filter events based on work item ID patterns in commit messages
        3. Automatically update related Azure DevOps work items
        4. Track build and deployment status from Azure Pipelines, GitHub Actions, GitLab CI
        """
        try:
            provider = self._detect_git_provider(repository_url)
            
            if provider == GitProvider.AZURE_REPOS:
                await self._setup_azure_repos_monitoring(repository_url, work_item_patterns)
            elif provider == GitProvider.GITHUB:
                await self._setup_github_monitoring(repository_url, work_item_patterns)
            elif provider == GitProvider.GITLAB:
                await self._setup_gitlab_monitoring(repository_url, work_item_patterns)
            
        except Exception as e:
            print(f"Error setting up repository monitoring: {str(e)}")
    
    def _detect_git_provider(self, repository_url: str) -> GitProvider:
        """Detect Git provider from repository URL"""
        parsed_url = urlparse(repository_url.lower())
        
        if 'dev.azure.com' in parsed_url.netloc or 'visualstudio.com' in parsed_url.netloc:
            return GitProvider.AZURE_REPOS
        elif 'github.com' in parsed_url.netloc:
            return GitProvider.GITHUB
        elif 'gitlab.com' in parsed_url.netloc or 'gitlab' in parsed_url.netloc:
            return GitProvider.GITLAB
        else:
            # Default to configured provider
            return GitProvider(self.default_provider)
    
    async def _fetch_commit_details(self, provider: GitProvider, repository_url: str, 
                                  commit_hash: str) -> Optional[CommitArtifact]:
        """Fetch commit details from appropriate Git provider"""
        try:
            if provider == GitProvider.AZURE_REPOS and self.azure_repos_client:
                return await self.azure_repos_client.get_commit_details(repository_url, commit_hash)
            elif provider == GitProvider.GITHUB and self.github_client:
                return await self.github_client.get_commit_details(repository_url, commit_hash)
            elif provider == GitProvider.GITLAB and self.gitlab_client:
                return await self.gitlab_client.get_commit_details(repository_url, commit_hash)
            else:
                return None
        except Exception as e:
            print(f"Error fetching commit details: {str(e)}")
            return None
    
    async def _parse_pr_url_and_fetch_details(self, pr_url: str) -> tuple[GitProvider, Optional[PullRequestArtifact]]:
        """Parse PR URL and fetch details from appropriate provider"""
        try:
            provider = self._detect_git_provider(pr_url)
            
            if provider == GitProvider.AZURE_REPOS and self.azure_repos_client:
                pr_details = await self.azure_repos_client.get_pull_request_details(pr_url)
            elif provider == GitProvider.GITHUB and self.github_client:
                pr_details = await self.github_client.get_pull_request_details(pr_url)
            elif provider == GitProvider.GITLAB and self.gitlab_client:
                pr_details = await self.gitlab_client.get_merge_request_details(pr_url)
            else:
                pr_details = None
            
            return provider, pr_details
            
        except Exception as e:
            print(f"Error parsing PR URL and fetching details: {str(e)}")
            return GitProvider.AZURE_REPOS, None
    
    async def _create_commit_work_item_relation(self, organization: str, project: str, 
                                              work_item_id: int, commit_details: CommitArtifact) -> Optional[ArtifactLink]:
        """Create Azure DevOps work item relation for commit"""
        try:
            # In a real implementation, this would use Azure DevOps REST API
            # to create work item relations and hyperlinks
            
            # For Azure Repos, use native Git commit linking
            if 'dev.azure.com' in commit_details.repository_url:
                relation_type = "ArtifactLink"
                commit_url = f"{commit_details.repository_url}/commit/{commit_details.commit_hash}"
            else:
                # For external Git providers, use hyperlink relation
                relation_type = "Hyperlink"
                commit_url = f"{commit_details.repository_url}/commit/{commit_details.commit_hash}"
            
            # Create artifact link object
            artifact_link = ArtifactLink(
                link_type="commit",
                url=commit_url,
                title=f"Commit {commit_details.commit_hash[:8]}: {commit_details.commit_message[:50]}",
                description=f"Commit by {commit_details.author} on {commit_details.timestamp.strftime('%Y-%m-%d %H:%M')}",
                metadata={
                    'commit_hash': commit_details.commit_hash,
                    'author': commit_details.author,
                    'files_changed': len(commit_details.files_changed),
                    'additions': commit_details.additions,
                    'deletions': commit_details.deletions,
                    'branch': commit_details.branch
                }
            )
            
            # TODO: Make actual API call to Azure DevOps to create the relation
            # url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}/relations?api-version=6.0"
            # relation_data = {
            #     "rel": relation_type,
            #     "url": commit_url,
            #     "attributes": {
            #         "comment": artifact_link.description
            #     }
            # }
            # response = await self._make_azure_devops_api_call('POST', url, relation_data)
            
            return artifact_link
            
        except Exception as e:
            print(f"Error creating commit work item relation: {str(e)}")
            return None
    
    async def _create_pr_work_item_relation(self, organization: str, project: str, 
                                          work_item_id: int, pr_details: PullRequestArtifact) -> Optional[ArtifactLink]:
        """Create Azure DevOps work item relation for pull request"""
        try:
            # Create artifact link object
            artifact_link = ArtifactLink(
                link_type="pull_request",
                url=pr_details.pr_url,
                title=f"PR #{pr_details.pr_id}: {pr_details.title}",
                description=f"Pull request by {pr_details.author} - Status: {pr_details.status}",
                metadata={
                    'pr_id': pr_details.pr_id,
                    'status': pr_details.status,
                    'author': pr_details.author,
                    'reviewers': pr_details.reviewers,
                    'source_branch': pr_details.source_branch,
                    'target_branch': pr_details.target_branch,
                    'created_date': pr_details.created_date.isoformat(),
                    'work_item_links': pr_details.work_item_links
                }
            )
            
            # TODO: Make actual API call to Azure DevOps to create the relation
            
            return artifact_link
            
        except Exception as e:
            print(f"Error creating PR work item relation: {str(e)}")
            return None
    
    async def _setup_azure_repos_monitoring(self, repository_url: str, work_item_patterns: List[str]):
        """Set up Azure Repos service hooks for monitoring"""
        # TODO: Implement Azure DevOps service hooks setup
        # This would configure webhooks for:
        # - Code pushed events
        # - Pull request events
        # - Build completed events
        pass
    
    async def _setup_github_monitoring(self, repository_url: str, work_item_patterns: List[str]):
        """Set up GitHub webhooks for monitoring"""
        # TODO: Implement GitHub webhooks setup
        pass
    
    async def _setup_gitlab_monitoring(self, repository_url: str, work_item_patterns: List[str]):
        """Set up GitLab webhooks for monitoring"""
        # TODO: Implement GitLab webhooks setup
        pass


class AzureReposClient:
    """Azure Repos API integration client"""
    
    def __init__(self, personal_access_token: str):
        """Initialize Azure Repos client with PAT"""
        self.pat = personal_access_token
        self.headers = {
            'Authorization': f'Basic {self._encode_pat(personal_access_token)}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _encode_pat(self, pat: str) -> str:
        """Encode Personal Access Token for Basic Auth"""
        return base64.b64encode(f":{pat}".encode()).decode()
    
    async def get_commit_details(self, repository_url: str, commit_hash: str) -> Optional[CommitArtifact]:
        """
        Get commit details from Azure Repos
        
        API Endpoint:
        GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repositoryId}/commits/{commitId}
        """
        try:
            # Parse Azure Repos URL to extract organization, project, and repository
            url_parts = self._parse_azure_repos_url(repository_url)
            if not url_parts:
                return None
            
            organization, project, repository_id = url_parts
            
            api_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository_id}/commits/{commit_hash}?api-version=6.0"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract work item mentions from commit message
                        work_item_mentions = self._extract_work_item_mentions(data.get('comment', ''))
                        
                        return CommitArtifact(
                            commit_hash=data.get('commitId', commit_hash),
                            commit_message=data.get('comment', ''),
                            author=data.get('author', {}).get('name', ''),
                            author_email=data.get('author', {}).get('email', ''),
                            timestamp=datetime.fromisoformat(data.get('author', {}).get('date', '').replace('Z', '+00:00')),
                            repository_url=repository_url,
                            branch='main',  # TODO: Get actual branch from API
                            files_changed=[],  # TODO: Fetch changed files
                            additions=0,  # TODO: Get from changeset
                            deletions=0,  # TODO: Get from changeset
                            work_item_mentions=work_item_mentions
                        )
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching Azure Repos commit details: {str(e)}")
            return None
    
    async def get_pull_request_details(self, pr_url: str) -> Optional[PullRequestArtifact]:
        """
        Get pull request details from Azure Repos
        
        API Endpoint:
        GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repositoryId}/pullrequests/{pullRequestId}
        """
        try:
            # Parse PR URL to extract details
            pr_parts = self._parse_azure_repos_pr_url(pr_url)
            if not pr_parts:
                return None
            
            organization, project, repository_id, pr_id = pr_parts
            
            api_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}?api-version=6.0"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract work item links from PR description
                        work_item_links = self._extract_work_item_mentions(data.get('description', ''))
                        
                        return PullRequestArtifact(
                            pr_url=pr_url,
                            pr_id=int(pr_id),
                            title=data.get('title', ''),
                            description=data.get('description', ''),
                            status=data.get('status', ''),
                            author=data.get('createdBy', {}).get('displayName', ''),
                            reviewers=[r.get('displayName', '') for r in data.get('reviewers', [])],
                            created_date=datetime.fromisoformat(data.get('creationDate', '').replace('Z', '+00:00')),
                            completed_date=datetime.fromisoformat(data.get('closedDate', '').replace('Z', '+00:00')) if data.get('closedDate') else None,
                            source_branch=data.get('sourceRefName', '').replace('refs/heads/', ''),
                            target_branch=data.get('targetRefName', '').replace('refs/heads/', ''),
                            work_item_links=work_item_links
                        )
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching Azure Repos PR details: {str(e)}")
            return None
    
    def _parse_azure_repos_url(self, repository_url: str) -> Optional[tuple[str, str, str]]:
        """Parse Azure Repos URL to extract organization, project, and repository"""
        # Example: https://dev.azure.com/organization/project/_git/repository
        try:
            parsed = urlparse(repository_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 4 and path_parts[2] == '_git':
                organization = path_parts[0]
                project = path_parts[1]
                repository = path_parts[3]
                return organization, project, repository
            
            return None
        except:
            return None
    
    def _parse_azure_repos_pr_url(self, pr_url: str) -> Optional[tuple[str, str, str, str]]:
        """Parse Azure Repos PR URL to extract organization, project, repository, and PR ID"""
        # Example: https://dev.azure.com/organization/project/_git/repository/pullrequest/123
        try:
            parsed = urlparse(pr_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 6 and path_parts[2] == '_git' and path_parts[4] == 'pullrequest':
                organization = path_parts[0]
                project = path_parts[1]
                repository = path_parts[3]
                pr_id = path_parts[5]
                return organization, project, repository, pr_id
            
            return None
        except:
            return None
    
    def _extract_work_item_mentions(self, text: str) -> List[int]:
        """Extract work item ID mentions from text"""
        matches = re.findall(r'#(\d+)', text)
        return [int(match) for match in matches]


class GitHubClient:
    """GitHub API integration client"""
    
    def __init__(self, token: str):
        """Initialize GitHub client with personal access token"""
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    async def get_commit_details(self, repository_url: str, commit_hash: str) -> Optional[CommitArtifact]:
        """Get commit details from GitHub API"""
        try:
            # Parse GitHub repository URL
            repo_parts = self._parse_github_url(repository_url)
            if not repo_parts:
                return None
            
            owner, repo = repo_parts
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_hash}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        work_item_mentions = self._extract_work_item_mentions(data.get('commit', {}).get('message', ''))
                        
                        return CommitArtifact(
                            commit_hash=data.get('sha', commit_hash),
                            commit_message=data.get('commit', {}).get('message', ''),
                            author=data.get('commit', {}).get('author', {}).get('name', ''),
                            author_email=data.get('commit', {}).get('author', {}).get('email', ''),
                            timestamp=datetime.fromisoformat(data.get('commit', {}).get('author', {}).get('date', '').replace('Z', '+00:00')),
                            repository_url=repository_url,
                            branch='main',  # TODO: Get actual branch
                            files_changed=[f.get('filename', '') for f in data.get('files', [])],
                            additions=data.get('stats', {}).get('additions', 0),
                            deletions=data.get('stats', {}).get('deletions', 0),
                            work_item_mentions=work_item_mentions
                        )
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching GitHub commit details: {str(e)}")
            return None
    
    async def get_pull_request_details(self, pr_url: str) -> Optional[PullRequestArtifact]:
        """Get pull request details from GitHub API"""
        try:
            # Parse GitHub PR URL
            pr_parts = self._parse_github_pr_url(pr_url)
            if not pr_parts:
                return None
            
            owner, repo, pr_number = pr_parts
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        work_item_links = self._extract_work_item_mentions(data.get('body', ''))
                        
                        return PullRequestArtifact(
                            pr_url=pr_url,
                            pr_id=data.get('number', 0),
                            title=data.get('title', ''),
                            description=data.get('body', ''),
                            status=data.get('state', ''),
                            author=data.get('user', {}).get('login', ''),
                            reviewers=[],  # TODO: Fetch reviewers from separate API
                            created_date=datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00')),
                            completed_date=datetime.fromisoformat(data.get('merged_at', '').replace('Z', '+00:00')) if data.get('merged_at') else None,
                            source_branch=data.get('head', {}).get('ref', ''),
                            target_branch=data.get('base', {}).get('ref', ''),
                            work_item_links=work_item_links
                        )
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching GitHub PR details: {str(e)}")
            return None
    
    def _parse_github_url(self, repository_url: str) -> Optional[tuple[str, str]]:
        """Parse GitHub repository URL to extract owner and repo"""
        # Example: https://github.com/owner/repo
        try:
            parsed = urlparse(repository_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].replace('.git', '')
                return owner, repo
            
            return None
        except:
            return None
    
    def _parse_github_pr_url(self, pr_url: str) -> Optional[tuple[str, str, str]]:
        """Parse GitHub PR URL to extract owner, repo, and PR number"""
        # Example: https://github.com/owner/repo/pull/123
        try:
            parsed = urlparse(pr_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 4 and path_parts[2] == 'pull':
                owner = path_parts[0]
                repo = path_parts[1]
                pr_number = path_parts[3]
                return owner, repo, pr_number
            
            return None
        except:
            return None
    
    def _extract_work_item_mentions(self, text: str) -> List[int]:
        """Extract work item ID mentions from text"""
        matches = re.findall(r'#(\d+)', text)
        return [int(match) for match in matches]


class GitLabClient:
    """GitLab API integration client"""
    
    def __init__(self, token: str):
        """Initialize GitLab client with personal access token"""
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    async def get_commit_details(self, repository_url: str, commit_hash: str) -> Optional[CommitArtifact]:
        """Get commit details from GitLab API"""
        # TODO: Implement GitLab commit details fetching
        return None
    
    async def get_merge_request_details(self, mr_url: str) -> Optional[PullRequestArtifact]:
        """Get merge request details from GitLab API"""
        # TODO: Implement GitLab merge request details fetching
        return None
    
    def _extract_work_item_mentions(self, text: str) -> List[int]:
        """Extract work item ID mentions from text"""
        matches = re.findall(r'#(\d+)', text)
        return [int(match) for match in matches]
