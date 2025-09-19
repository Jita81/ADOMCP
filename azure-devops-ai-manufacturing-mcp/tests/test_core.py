"""
Azure DevOps AI Manufacturing MCP - Core Tests

This module contains unit tests for the core Azure DevOps AI Manufacturing functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from types import (
    ManufacturingWorkItem, ManufacturingMetadata, ManufacturingPhase,
    AzureDevOpsWorkItemType, OperationResult
)
from core import AzureDevOpsAIManufacturingMCP


class TestAzureDevOpsAIManufacturingMCP:
    """Test cases for Azure DevOps AI Manufacturing MCP core functionality"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            'azure_devops_organization_url': 'https://dev.azure.com/testorg',
            'personal_access_token': 'test-pat-token',
            'config_storage': 'sqlite',
            'config_db_url': ':memory:',
            'cache_ttl_seconds': 3600,
            'persistent_cache': False
        }
    
    @pytest.fixture
    def sample_work_item(self):
        """Sample manufacturing work item for testing"""
        return ManufacturingWorkItem(
            organization='testorg',
            project='testproject',
            work_item_type=AzureDevOpsWorkItemType.USER_STORY,
            title='AI Generated Authentication Service',
            description='Implement JWT-based authentication service using AI code generation',
            area_path='testproject\\Authentication',
            iteration_path='testproject\\Sprint 1',
            tags=['ai-generated', 'authentication'],
            manufacturing_metadata=ManufacturingMetadata(
                manufacturing_id='ai_auth_001',
                ai_generator='gpt-4-code-specialist',
                confidence_score=0.94,
                current_phase=ManufacturingPhase.ANALYSIS
            )
        )
    
    def test_initialization(self, sample_config):
        """Test MCP initialization with configuration"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        assert mcp.organization_url == sample_config['azure_devops_organization_url']
        assert mcp.personal_access_token == sample_config['personal_access_token']
        assert mcp.config_manager is not None
        assert mcp.workflow_manager is not None
        assert mcp.artifact_manager is not None
        assert mcp.cache_manager is not None
    
    def test_pat_encoding(self, sample_config):
        """Test Personal Access Token encoding"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        encoded_pat = mcp._encode_pat('test-token')
        
        # Verify the encoding follows Azure DevOps Basic Auth pattern
        import base64
        expected = base64.b64encode(':test-token'.encode()).decode()
        assert encoded_pat == expected
    
    @pytest.mark.asyncio
    async def test_create_manufacturing_work_item_success(self, sample_config, sample_work_item):
        """Test successful manufacturing work item creation"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Mock the project configuration
        mock_project_config = Mock()
        mock_project_config.organization = 'testorg'
        mock_project_config.project = 'testproject'
        
        with patch.object(mcp, 'get_project_configuration', return_value=mock_project_config):
            with patch('aiohttp.ClientSession') as mock_session:
                # Mock successful API response
                mock_response = AsyncMock()
                mock_response.status = 201
                mock_response.json = AsyncMock(return_value={
                    'id': 12345,
                    '_links': {
                        'html': {'href': 'https://dev.azure.com/testorg/testproject/_workitems/edit/12345'}
                    }
                })
                
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                mcp._session = mock_session.return_value.__aenter__.return_value
                
                result = await mcp.create_manufacturing_work_item(sample_work_item)
                
                assert result.success is True
                assert result.data['work_item_id'] == 12345
                assert 'manufacturing_id' in result.data
    
    @pytest.mark.asyncio
    async def test_create_manufacturing_work_item_missing_config(self, sample_config, sample_work_item):
        """Test work item creation with missing project configuration"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Mock missing project configuration
        with patch.object(mcp, 'get_project_configuration', return_value=None):
            result = await mcp.create_manufacturing_work_item(sample_work_item)
            
            assert result.success is False
            assert result.error_code == 'PROJECT_CONFIG_MISSING'
    
    def test_prepare_work_item_data(self, sample_config, sample_work_item):
        """Test work item data preparation for Azure DevOps API"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        operations = mcp._prepare_work_item_data(sample_work_item)
        
        # Verify basic fields are included
        title_op = next((op for op in operations if op['path'] == '/fields/System.Title'), None)
        assert title_op is not None
        assert title_op['value'] == sample_work_item.title
        
        # Verify manufacturing metadata fields
        manufacturing_id_op = next((op for op in operations if op['path'] == '/fields/Custom.AI.ManufacturingId'), None)
        assert manufacturing_id_op is not None
        assert manufacturing_id_op['value'] == sample_work_item.manufacturing_metadata.manufacturing_id
        
        # Verify tags are properly formatted
        tags_op = next((op for op in operations if op['path'] == '/fields/System.Tags'), None)
        assert tags_op is not None
        assert tags_op['value'] == 'ai-generated; authentication'
    
    @pytest.mark.asyncio
    async def test_analyze_project_structure_cached(self, sample_config):
        """Test project structure analysis with cached result"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Mock cached project structure
        mock_cached_structure = Mock()
        mock_cached_structure.analyzed_at = datetime.now()
        mock_cached_structure.organization = 'testorg'
        mock_cached_structure.project = 'testproject'
        
        with patch.object(mcp.cache_manager, 'get_project_structure', return_value=mock_cached_structure):
            with patch.object(mcp, '_is_cache_fresh', return_value=True):
                result = await mcp.analyze_project_structure('testorg', 'testproject')
                
                assert result.success is True
                assert 'retrieved from cache' in result.message
                assert result.data['project_structure'] == mock_cached_structure
    
    @pytest.mark.asyncio
    async def test_analyze_project_structure_fresh_analysis(self, sample_config):
        """Test project structure analysis with fresh data fetch"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Mock no cached data
        with patch.object(mcp.cache_manager, 'get_project_structure', return_value=None):
            with patch.object(mcp, '_perform_full_project_analysis') as mock_analysis:
                with patch.object(mcp.config_manager, 'store_project_configuration', return_value=True):
                    with patch.object(mcp, 'schedule_daily_configuration_validation'):
                        
                        mock_structure = Mock()
                        mock_structure.organization = 'testorg'
                        mock_structure.project = 'testproject'
                        mock_analysis.return_value = mock_structure
                        
                        result = await mcp.analyze_project_structure('testorg', 'testproject')
                        
                        assert result.success is True
                        assert 'analyzed and cached successfully' in result.message
                        mock_analysis.assert_called_once_with('testorg', 'testproject')
    
    def test_is_cache_fresh(self, sample_config):
        """Test cache freshness validation"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Test fresh cache (within TTL)
        fresh_time = datetime.now()
        assert mcp._is_cache_fresh(fresh_time) is True
        
        # Test stale cache (beyond TTL)
        from datetime import timedelta
        stale_time = datetime.now() - timedelta(seconds=7200)  # 2 hours ago
        assert mcp._is_cache_fresh(stale_time) is False
    
    @pytest.mark.asyncio
    async def test_bulk_create_manufacturing_work_items(self, sample_config, sample_work_item):
        """Test bulk creation of manufacturing work items"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        # Create multiple work items
        work_items = [sample_work_item] * 3  # 3 identical work items for testing
        
        with patch.object(mcp, 'create_manufacturing_work_item') as mock_create:
            # Mock successful creation for all items
            mock_create.return_value = OperationResult(
                success=True,
                message="Work item created successfully",
                data={'work_item_id': 12345}
            )
            
            result = await mcp.bulk_create_manufacturing_work_items(work_items)
            
            assert result.success is True
            assert 'successful' in result.message
            assert mock_create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, sample_config):
        """Test health status monitoring"""
        mcp = AzureDevOpsAIManufacturingMCP(sample_config)
        
        health_status = await mcp.get_health_status()
        
        assert health_status.healthy is True
        assert health_status.azure_devops_api_status == "healthy"
        assert health_status.cache_status == "healthy"
        assert health_status.database_status == "healthy"
        assert health_status.last_check is not None


class TestWorkItemDataPreparation:
    """Test cases for work item data preparation"""
    
    def test_prepare_work_item_with_all_fields(self):
        """Test work item preparation with all possible fields"""
        config = {'azure_devops_organization_url': 'https://dev.azure.com/test'}
        mcp = AzureDevOpsAIManufacturingMCP(config)
        
        work_item = ManufacturingWorkItem(
            organization='test',
            project='test',
            work_item_type=AzureDevOpsWorkItemType.TASK,
            title='Test Task',
            description='Test Description',
            area_path='Test\\Area',
            iteration_path='Test\\Iteration',
            assigned_to='test@example.com',
            state='New',
            priority=1,
            tags=['tag1', 'tag2'],
            custom_fields={'Custom.Field': 'Custom Value'},
            manufacturing_metadata=ManufacturingMetadata(
                manufacturing_id='test_001',
                ai_generator='test-ai',
                confidence_score=0.95,
                complexity_score=3,
                estimated_duration_hours=8,
                current_phase=ManufacturingPhase.CODE_GENERATION,
                progress_percentage=25
            )
        )
        
        operations = mcp._prepare_work_item_data(work_item)
        
        # Verify all fields are present
        field_paths = [op['path'] for op in operations]
        
        expected_paths = [
            '/fields/System.Title',
            '/fields/System.Description',
            '/fields/System.AreaPath',
            '/fields/System.IterationPath',
            '/fields/System.AssignedTo',
            '/fields/System.State',
            '/fields/Microsoft.VSTS.Common.Priority',
            '/fields/System.Tags',
            '/fields/Custom.AI.ManufacturingId',
            '/fields/Custom.AI.Generator',
            '/fields/Custom.AI.ConfidenceScore',
            '/fields/Custom.AI.CurrentPhase',
            '/fields/Custom.AI.ProgressPercentage',
            '/fields/Custom.AI.ComplexityScore',
            '/fields/Custom.AI.EstimatedDurationHours',
            '/fields/Custom.Field'
        ]
        
        for expected_path in expected_paths:
            assert expected_path in field_paths, f"Missing field path: {expected_path}"
        
        # Verify tags formatting
        tags_op = next(op for op in operations if op['path'] == '/fields/System.Tags')
        assert tags_op['value'] == 'tag1; tag2'
    
    def test_prepare_work_item_minimal_fields(self):
        """Test work item preparation with minimal required fields"""
        config = {'azure_devops_organization_url': 'https://dev.azure.com/test'}
        mcp = AzureDevOpsAIManufacturingMCP(config)
        
        work_item = ManufacturingWorkItem(
            organization='test',
            project='test',
            work_item_type=AzureDevOpsWorkItemType.USER_STORY,
            title='Minimal Work Item'
        )
        
        operations = mcp._prepare_work_item_data(work_item)
        
        # Should only have title operation
        assert len(operations) == 1
        assert operations[0]['path'] == '/fields/System.Title'
        assert operations[0]['value'] == 'Minimal Work Item'


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
