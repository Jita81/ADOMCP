"""
Azure DevOps AI Manufacturing MCP - Configuration Management

This module provides persistent configuration management for Azure DevOps projects
with versioning, encryption, and automated validation scheduling.
"""

import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import aiosqlite

from .interface import ConfigurationManagerInterface
from .types import AzureDevOpsProjectStructure


class ConfigurationManager(ConfigurationManagerInterface):
    """
    Comprehensive Azure DevOps configuration persistence system
    
    Supports multiple storage backends with encryption, versioning,
    and automated validation scheduling.
    """
    
    def __init__(self, storage_type: str, connection_string: Optional[str] = None, 
                 encryption_key: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            storage_type: Storage backend type ('sqlite', 'postgresql', 'redis')
            connection_string: Database connection string
            encryption_key: Encryption key for sensitive data
        """
        self.storage_type = storage_type
        self.connection_string = connection_string or 'azure_devops_config.db'
        
        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            # Generate a key for demo purposes - in production, use proper key management
            self.cipher = Fernet(Fernet.generate_key())
        
        # Initialize storage backend
        if storage_type == 'sqlite':
            self._init_sqlite_storage()
        elif storage_type == 'postgresql':
            self._init_postgresql_storage()
        elif storage_type == 'redis':
            self._init_redis_storage()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    def _init_sqlite_storage(self):
        """Initialize SQLite storage backend"""
        # Create database schema
        import sqlite3
        conn = sqlite3.connect(self.connection_string)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization TEXT NOT NULL,
                project TEXT NOT NULL,
                version TEXT NOT NULL,
                configuration_data TEXT NOT NULL,  -- Encrypted JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(organization, project, version)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization TEXT NOT NULL,
                project TEXT NOT NULL,
                schedule_expression TEXT NOT NULL,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(organization, project)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_project_config_lookup 
            ON project_configurations(organization, project, is_active)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_validation_schedule_lookup 
            ON validation_schedules(organization, project, is_active)
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_postgresql_storage(self):
        """Initialize PostgreSQL storage backend"""
        # TODO: Implement PostgreSQL schema initialization
        pass
    
    def _init_redis_storage(self):
        """Initialize Redis storage backend"""
        # TODO: Implement Redis configuration
        pass
    
    async def store_project_configuration(self, organization: str, project: str, 
                                        configuration: AzureDevOpsProjectStructure) -> bool:
        """
        Store Azure DevOps project configuration with versioning
        
        Implementation includes serialization, encryption, versioning, and history maintenance.
        """
        try:
            # Generate version based on timestamp
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Serialize configuration to JSON
            config_dict = self._serialize_project_structure(configuration)
            config_json = json.dumps(config_dict)
            
            # Encrypt configuration data
            encrypted_data = self.cipher.encrypt(config_json.encode()).decode()
            
            if self.storage_type == 'sqlite':
                return await self._store_sqlite_configuration(
                    organization, project, version, encrypted_data
                )
            elif self.storage_type == 'postgresql':
                return await self._store_postgresql_configuration(
                    organization, project, version, encrypted_data
                )
            elif self.storage_type == 'redis':
                return await self._store_redis_configuration(
                    organization, project, version, encrypted_data
                )
            
            return False
            
        except Exception as e:
            print(f"Error storing project configuration: {str(e)}")
            return False
    
    async def _store_sqlite_configuration(self, organization: str, project: str, 
                                        version: str, encrypted_data: str) -> bool:
        """Store configuration in SQLite database"""
        try:
            async with aiosqlite.connect(self.connection_string) as db:
                # Deactivate previous versions
                await db.execute(
                    '''UPDATE project_configurations 
                       SET is_active = FALSE 
                       WHERE organization = ? AND project = ?''',
                    (organization, project)
                )
                
                # Insert new configuration
                await db.execute(
                    '''INSERT INTO project_configurations 
                       (organization, project, version, configuration_data, is_active)
                       VALUES (?, ?, ?, ?, TRUE)''',
                    (organization, project, version, encrypted_data)
                )
                
                await db.commit()
                return True
                
        except Exception as e:
            print(f"SQLite storage error: {str(e)}")
            return False
    
    async def _store_postgresql_configuration(self, organization: str, project: str, 
                                            version: str, encrypted_data: str) -> bool:
        """Store configuration in PostgreSQL database"""
        # TODO: Implement PostgreSQL storage
        return False
    
    async def _store_redis_configuration(self, organization: str, project: str, 
                                       version: str, encrypted_data: str) -> bool:
        """Store configuration in Redis"""
        # TODO: Implement Redis storage
        return False
    
    async def get_project_configuration(self, organization: str, project: str, 
                                      version: Optional[str] = None) -> Optional[AzureDevOpsProjectStructure]:
        """
        Retrieve Azure DevOps project configuration with optional versioning
        """
        try:
            if self.storage_type == 'sqlite':
                encrypted_data = await self._get_sqlite_configuration(organization, project, version)
            elif self.storage_type == 'postgresql':
                encrypted_data = await self._get_postgresql_configuration(organization, project, version)
            elif self.storage_type == 'redis':
                encrypted_data = await self._get_redis_configuration(organization, project, version)
            else:
                return None
            
            if not encrypted_data:
                return None
            
            # Decrypt and deserialize
            decrypted_data = self.cipher.decrypt(encrypted_data.encode()).decode()
            config_dict = json.loads(decrypted_data)
            
            return self._deserialize_project_structure(config_dict)
            
        except Exception as e:
            print(f"Error retrieving project configuration: {str(e)}")
            return None
    
    async def _get_sqlite_configuration(self, organization: str, project: str, 
                                      version: Optional[str] = None) -> Optional[str]:
        """Retrieve configuration from SQLite database"""
        try:
            async with aiosqlite.connect(self.connection_string) as db:
                if version:
                    cursor = await db.execute(
                        '''SELECT configuration_data FROM project_configurations 
                           WHERE organization = ? AND project = ? AND version = ?''',
                        (organization, project, version)
                    )
                else:
                    cursor = await db.execute(
                        '''SELECT configuration_data FROM project_configurations 
                           WHERE organization = ? AND project = ? AND is_active = TRUE
                           ORDER BY created_at DESC LIMIT 1''',
                        (organization, project)
                    )
                
                row = await cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            print(f"SQLite retrieval error: {str(e)}")
            return None
    
    async def _get_postgresql_configuration(self, organization: str, project: str, 
                                          version: Optional[str] = None) -> Optional[str]:
        """Retrieve configuration from PostgreSQL database"""
        # TODO: Implement PostgreSQL retrieval
        return None
    
    async def _get_redis_configuration(self, organization: str, project: str, 
                                     version: Optional[str] = None) -> Optional[str]:
        """Retrieve configuration from Redis"""
        # TODO: Implement Redis retrieval
        return None
    
    async def schedule_configuration_validation(self, organization: str, project: str, schedule: str) -> bool:
        """
        Schedule daily configuration validation job
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            schedule: Cron expression for scheduling (e.g., "0 2 * * *")
        """
        try:
            if self.storage_type == 'sqlite':
                return await self._schedule_sqlite_validation(organization, project, schedule)
            elif self.storage_type == 'postgresql':
                return await self._schedule_postgresql_validation(organization, project, schedule)
            elif self.storage_type == 'redis':
                return await self._schedule_redis_validation(organization, project, schedule)
            
            return False
            
        except Exception as e:
            print(f"Error scheduling configuration validation: {str(e)}")
            return False
    
    async def _schedule_sqlite_validation(self, organization: str, project: str, schedule: str) -> bool:
        """Schedule validation in SQLite database"""
        try:
            async with aiosqlite.connect(self.connection_string) as db:
                # Calculate next run time (simplified - would use proper cron parser in production)
                from datetime import datetime, timedelta
                next_run = datetime.now() + timedelta(days=1)  # Simple daily schedule
                
                await db.execute(
                    '''INSERT OR REPLACE INTO validation_schedules 
                       (organization, project, schedule_expression, next_run, is_active)
                       VALUES (?, ?, ?, ?, TRUE)''',
                    (organization, project, schedule, next_run)
                )
                
                await db.commit()
                return True
                
        except Exception as e:
            print(f"SQLite validation scheduling error: {str(e)}")
            return False
    
    async def _schedule_postgresql_validation(self, organization: str, project: str, schedule: str) -> bool:
        """Schedule validation in PostgreSQL database"""
        # TODO: Implement PostgreSQL validation scheduling
        return False
    
    async def _schedule_redis_validation(self, organization: str, project: str, schedule: str) -> bool:
        """Schedule validation in Redis"""
        # TODO: Implement Redis validation scheduling
        return False
    
    def _serialize_project_structure(self, structure: AzureDevOpsProjectStructure) -> Dict[str, Any]:
        """Serialize AzureDevOpsProjectStructure to dictionary"""
        return {
            'organization': structure.organization,
            'project': structure.project,
            'project_id': structure.project_id,
            'project_description': structure.project_description,
            'process_template': structure.process_template,
            'work_item_types': {k: self._serialize_work_item_type(v) for k, v in structure.work_item_types.items()},
            'custom_fields': {k: self._serialize_field_definition(v) for k, v in structure.custom_fields.items()},
            'area_paths': [self._serialize_area_path(ap) for ap in structure.area_paths],
            'iteration_paths': [self._serialize_iteration_path(ip) for ip in structure.iteration_paths],
            'teams': [self._serialize_team_config(t) for t in structure.teams],
            'boards': {k: self._serialize_board_config(v) for k, v in structure.boards.items()},
            'repositories': [self._serialize_repository_info(r) for r in structure.repositories],
            'build_definitions': [self._serialize_build_definition(bd) for bd in structure.build_definitions],
            'analyzed_at': structure.analyzed_at.isoformat(),
            'field_usage_patterns': structure.field_usage_patterns
        }
    
    def _serialize_work_item_type(self, wit: 'WorkItemTypeDefinition') -> Dict[str, Any]:
        """Serialize WorkItemTypeDefinition"""
        return {
            'name': wit.name,
            'reference_name': wit.reference_name,
            'description': wit.description,
            'icon': wit.icon,
            'color': wit.color,
            'is_disabled': wit.is_disabled,
            'states': [{'name': s.name, 'category': s.category, 'color': s.color} for s in wit.states],
            'fields': {k: self._serialize_field_definition(v) for k, v in wit.fields.items()}
        }
    
    def _serialize_field_definition(self, field: 'FieldDefinition') -> Dict[str, Any]:
        """Serialize FieldDefinition"""
        return {
            'reference_name': field.reference_name,
            'name': field.name,
            'type': field.type,
            'usage': field.usage,
            'read_only': field.read_only,
            'can_sort_by': field.can_sort_by,
            'is_queryable': field.is_queryable,
            'is_identity': field.is_identity,
            'is_picklist': field.is_picklist,
            'allowed_values': field.allowed_values
        }
    
    def _serialize_area_path(self, area: 'AreaPath') -> Dict[str, Any]:
        """Serialize AreaPath"""
        return {
            'id': area.id,
            'name': area.name,
            'path': area.path,
            'has_children': area.has_children
        }
    
    def _serialize_iteration_path(self, iteration: 'IterationPath') -> Dict[str, Any]:
        """Serialize IterationPath"""
        return {
            'id': iteration.id,
            'name': iteration.name,
            'path': iteration.path,
            'start_date': iteration.start_date.isoformat() if iteration.start_date else None,
            'finish_date': iteration.finish_date.isoformat() if iteration.finish_date else None
        }
    
    def _serialize_team_config(self, team: 'TeamConfiguration') -> Dict[str, Any]:
        """Serialize TeamConfiguration"""
        return {
            'id': team.id,
            'name': team.name,
            'description': team.description,
            'default_team': team.default_team
        }
    
    def _serialize_board_config(self, board: 'BoardConfiguration') -> Dict[str, Any]:
        """Serialize BoardConfiguration"""
        return {
            'board_id': board.board_id,
            'name': board.name,
            'columns': [{'id': c.id, 'name': c.name, 'item_limit': c.item_limit, 
                        'state_mappings': c.state_mappings, 'column_type': c.column_type} 
                       for c in board.columns],
            'rows': [{'id': r.id, 'name': r.name} for r in board.rows],
            'card_fields': board.card_fields,
            'card_styles': board.card_styles
        }
    
    def _serialize_repository_info(self, repo: 'RepositoryInfo') -> Dict[str, Any]:
        """Serialize RepositoryInfo"""
        return {
            'id': repo.id,
            'name': repo.name,
            'url': repo.url,
            'default_branch': repo.default_branch,
            'size': repo.size
        }
    
    def _serialize_build_definition(self, build_def: 'BuildDefinition') -> Dict[str, Any]:
        """Serialize BuildDefinition"""
        return {
            'id': build_def.id,
            'name': build_def.name,
            'path': build_def.path,
            'type': build_def.type,
            'repository': self._serialize_repository_info(build_def.repository)
        }
    
    def _deserialize_project_structure(self, data: Dict[str, Any]) -> AzureDevOpsProjectStructure:
        """Deserialize dictionary to AzureDevOpsProjectStructure"""
        from .types import (
            AzureDevOpsProjectStructure, WorkItemTypeDefinition, FieldDefinition,
            WorkItemState, AreaPath, IterationPath, TeamConfiguration, 
            BoardConfiguration, BoardColumn, BoardRow, RepositoryInfo, BuildDefinition
        )
        
        # Deserialize work item types
        work_item_types = {}
        for k, v in data.get('work_item_types', {}).items():
            states = [WorkItemState(name=s['name'], category=s['category'], color=s['color']) 
                     for s in v.get('states', [])]
            fields = {fk: FieldDefinition(**fv) for fk, fv in v.get('fields', {}).items()}
            work_item_types[k] = WorkItemTypeDefinition(
                name=v['name'],
                reference_name=v['reference_name'],
                description=v['description'],
                icon=v['icon'],
                color=v['color'],
                is_disabled=v['is_disabled'],
                states=states,
                fields=fields
            )
        
        # Deserialize other components
        custom_fields = {k: FieldDefinition(**v) for k, v in data.get('custom_fields', {}).items()}
        area_paths = [AreaPath(**ap) for ap in data.get('area_paths', [])]
        iteration_paths = [IterationPath(
            id=ip['id'],
            name=ip['name'],
            path=ip['path'],
            start_date=datetime.fromisoformat(ip['start_date']) if ip.get('start_date') else None,
            finish_date=datetime.fromisoformat(ip['finish_date']) if ip.get('finish_date') else None
        ) for ip in data.get('iteration_paths', [])]
        teams = [TeamConfiguration(**t) for t in data.get('teams', [])]
        
        # Deserialize boards
        boards = {}
        for k, v in data.get('boards', {}).items():
            columns = [BoardColumn(**c) for c in v.get('columns', [])]
            rows = [BoardRow(**r) for r in v.get('rows', [])]
            boards[k] = BoardConfiguration(
                board_id=v['board_id'],
                name=v['name'],
                columns=columns,
                rows=rows,
                card_fields=v.get('card_fields', []),
                card_styles=v.get('card_styles', {})
            )
        
        repositories = [RepositoryInfo(**r) for r in data.get('repositories', [])]
        
        # Deserialize build definitions
        build_definitions = []
        for bd in data.get('build_definitions', []):
            repo_info = RepositoryInfo(**bd['repository'])
            build_definitions.append(BuildDefinition(
                id=bd['id'],
                name=bd['name'],
                path=bd['path'],
                type=bd['type'],
                repository=repo_info
            ))
        
        return AzureDevOpsProjectStructure(
            organization=data['organization'],
            project=data['project'],
            project_id=data['project_id'],
            project_description=data['project_description'],
            process_template=data['process_template'],
            work_item_types=work_item_types,
            custom_fields=custom_fields,
            area_paths=area_paths,
            iteration_paths=iteration_paths,
            teams=teams,
            boards=boards,
            repositories=repositories,
            build_definitions=build_definitions,
            analyzed_at=datetime.fromisoformat(data['analyzed_at']),
            field_usage_patterns=data.get('field_usage_patterns', {})
        )
