"""
Azure DevOps Multi-Platform MCP - Complete Usage Examples

This module provides comprehensive examples of using the Azure DevOps Multi-Platform MCP
for various cross-platform development scenarios and workflows.
"""

import asyncio
import os
from datetime import datetime
from typing import List

# Import the MCP module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from azure_devops_multiplatform_mcp import (
    create_multiplatform_mcp,
    get_default_configuration,
    WorkItemData,
    WorkItemUpdate,
    AzureDevOpsWorkItemType,
    DevelopmentArtifacts,
    CommitArtifact,
    PullRequestArtifact,
    GitProvider
)


async def basic_usage_example():
    """
    Basic usage example showing project analysis and work item creation
    """
    print("=== Basic Usage Example ===")

    # Get default configuration and customize
    config = get_default_configuration()
    config.update({
        'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        'azure_devops_pat': os.getenv('AZURE_DEVOPS_PAT', 'your-azure-devops-token'),
        'github_token': os.getenv('GITHUB_TOKEN', 'your-github-token'),
        'gitlab_token': os.getenv('GITLAB_TOKEN', 'your-gitlab-token'),
        'default_project': 'MultiPlatform-Demo'
    })
    
    try:
        async with create_multiplatform_mcp(config) as mcp:
            # 1. Analyze project structure
            print("Analyzing project structure...")
            analysis_result = await mcp.analyze_project_structure('myorg', 'AI-Manufacturing-Demo')
            
            if analysis_result.success:
                print(f"✅ Project analysis completed: {analysis_result.message}")
                project_structure = analysis_result.data['project_structure']
                print(f"   - Organization: {project_structure.organization}")
                print(f"   - Project: {project_structure.project}")
                print(f"   - Work Item Types: {len(project_structure.work_item_types)}")
                print(f"   - Teams: {len(project_structure.teams)}")
            else:
                print(f"❌ Project analysis failed: {analysis_result.message}")
                return
            
            # 2. Create a manufacturing work item
            print("\nCreating manufacturing work item...")
            work_item = WorkItemData(
                organization='myorg',
                project='AI-Manufacturing-Demo',
                work_item_type=AzureDevOpsWorkItemType.USER_STORY,
                title='AI Generated User Authentication System',
                description='Implement comprehensive user authentication with JWT tokens, password hashing, and session management.',
                area_path='AI-Manufacturing-Demo\\Security',
                iteration_path='AI-Manufacturing-Demo\\Sprint 1',
                tags=['ai-generated', 'authentication', 'security', 'high-priority'],
                manufacturing_metadata=# No direct replacement needed - using WorkItemData.fields instead(
                    manufacturing_id='ai_auth_system_001',
                    ai_generator='gpt-4-turbo-code-specialist',
                    confidence_score=0.94,
                    complexity_score=8,
                    estimated_duration_hours=16,
                    current_phase=ManufacturingPhase.ANALYSIS
                )
            )
            
            creation_result = await mcp.create_manufacturing_work_item(work_item)
            
            if creation_result.success:
                work_item_id = creation_result.data['work_item_id']
                work_item_url = creation_result.data['work_item_url']
                print(f"✅ Work item created successfully!")
                print(f"   - Work Item ID: {work_item_id}")
                print(f"   - URL: {work_item_url}")
                print(f"   - Manufacturing ID: {creation_result.data['manufacturing_id']}")
            else:
                print(f"❌ Work item creation failed: {creation_result.message}")
            
            # 3. Get system health status
            print("\nChecking system health...")
            health_status = await mcp.get_health_status()
            print(f"✅ System Health: {'Healthy' if health_status.healthy else 'Unhealthy'}")
            print(f"   - Azure DevOps API: {health_status.azure_devops_api_status}")
            print(f"   - Cache: {health_status.cache_status}")
            print(f"   - Database: {health_status.database_status}")
            
    except Exception as e:
        print(f"❌ Error in basic usage example: {str(e)}")


async def bulk_manufacturing_example():
    """
    Example showing bulk creation and management of manufacturing work items
    """
    print("\n=== Bulk Manufacturing Example ===")
    
    config = get_default_configuration()
    config.update({
        'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        'personal_access_token': os.getenv('AZURE_DEVOPS_PAT', 'your-pat-token'),
        'default_project': 'AI-Manufacturing-Demo'
    })
    
    try:
        async with create_multiplatform_mcp(config) as mcp:
            # Create multiple work items for a complete application
            work_items = []
            
            # Define components to be manufactured
            components = [
                {
                    'title': 'User Authentication Service',
                    'description': 'JWT-based authentication with password hashing',
                    'complexity': 8,
                    'confidence': 0.94,
                    'area': 'Security'
                },
                {
                    'title': 'User Profile Management API',
                    'description': 'RESTful API for user profile CRUD operations',
                    'complexity': 6,
                    'confidence': 0.91,
                    'area': 'API'
                },
                {
                    'title': 'Data Validation Middleware',
                    'description': 'Input validation and sanitization middleware',
                    'complexity': 4,
                    'confidence': 0.96,
                    'area': 'Middleware'
                },
                {
                    'title': 'Error Handling System',
                    'description': 'Centralized error handling and logging',
                    'complexity': 5,
                    'confidence': 0.93,
                    'area': 'Infrastructure'
                },
                {
                    'title': 'Database Connection Pool',
                    'description': 'Optimized database connection management',
                    'complexity': 7,
                    'confidence': 0.89,
                    'area': 'Database'
                }
            ]
            
            # Create work items
            for i, component in enumerate(components):
                work_item = WorkItemData(
                    organization='myorg',
                    project='AI-Manufacturing-Demo',
                    work_item_type=AzureDevOpsWorkItemType.USER_STORY,
                    title=component['title'],
                    description=component['description'],
                    area_path=f"AI-Manufacturing-Demo\\{component['area']}",
                    iteration_path='AI-Manufacturing-Demo\\Sprint 1',
                    tags=['ai-generated', 'bulk-manufacturing', component['area'].lower()],
                    manufacturing_metadata=# No direct replacement needed - using WorkItemData.fields instead(
                        manufacturing_id=f'ai_component_{i+1:03d}',
                        ai_generator='gpt-4-turbo-code-specialist',
                        confidence_score=component['confidence'],
                        complexity_score=component['complexity'],
                        estimated_duration_hours=component['complexity'] * 2,
                        current_phase=ManufacturingPhase.ANALYSIS
                    )
                )
                work_items.append(work_item)
            
            print(f"Creating {len(work_items)} work items in bulk...")
            bulk_result = await mcp.bulk_create_manufacturing_work_items(work_items)
            
            if bulk_result.success:
                successful_creations = sum(1 for r in bulk_result.data['results'] if r.success)
                print(f"✅ Bulk creation completed: {successful_creations}/{len(work_items)} successful")
                
                # Store work item IDs for further processing
                work_item_ids = [
                    r.data['work_item_id'] for r in bulk_result.data['results'] 
                    if r.success
                ]
                
                print(f"   - Created Work Item IDs: {work_item_ids}")
            else:
                print(f"❌ Bulk creation failed: {bulk_result.message}")
                return
            
            # Progress all items through manufacturing phases
            print("\nProgressing work items through manufacturing phases...")
            phases = [
                ManufacturingPhase.PLANNING,
                ManufacturingPhase.CODE_GENERATION,
                ManufacturingPhase.CODE_REVIEW,
                ManufacturingPhase.TESTING
            ]
            
            for phase_index, phase in enumerate(phases):
                print(f"\n  Transitioning to phase: {phase.value}")
                progress_percentage = int((phase_index + 1) / len(phases) * 80)  # 80% when testing starts
                
                for work_item_id in work_item_ids:
                    progress = ManufacturingProgress(
                        current_phase=phase,
                        progress_percentage=progress_percentage,
                        notes=f"Automated progression to {phase.value} phase"
                    )
                    
                    result = await mcp.update_manufacturing_progress(work_item_id, progress)
                    if result.success:
                        print(f"    ✅ Work Item {work_item_id}: {phase.value} ({progress_percentage}%)")
                    else:
                        print(f"    ❌ Work Item {work_item_id}: Failed to update progress")
            
            print(f"\n✅ Bulk manufacturing workflow completed for {len(work_item_ids)} work items")
            
    except Exception as e:
        print(f"❌ Error in bulk manufacturing example: {str(e)}")


async def git_integration_example():
    """
    Example showing multi-platform Git integration with artifact attachment
    """
    print("\n=== Git Integration Example ===")
    
    config = get_default_configuration()
    config.update({
        'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        'personal_access_token': os.getenv('AZURE_DEVOPS_PAT', 'your-pat-token'),
        'github_token': os.getenv('GITHUB_TOKEN', 'your-github-token'),
        'gitlab_token': os.getenv('GITLAB_TOKEN', 'your-gitlab-token'),
        'default_project': 'AI-Manufacturing-Demo'
    })
    
    try:
        async with create_multiplatform_mcp(config) as mcp:
            # First create a work item to attach artifacts to
            work_item = WorkItemData(
                organization='myorg',
                project='AI-Manufacturing-Demo',
                work_item_type=AzureDevOpsWorkItemType.FEATURE,
                title='Multi-Platform Git Integration Feature',
                description='Demonstrate Git integration across Azure Repos, GitHub, and GitLab',
                manufacturing_metadata=# No direct replacement needed - using WorkItemData.fields instead(
                    manufacturing_id='git_integration_001',
                    ai_generator='gpt-4-turbo',
                    confidence_score=0.92,
                    current_phase=ManufacturingPhase.CODE_GENERATION
                )
            )
            
            creation_result = await mcp.create_manufacturing_work_item(work_item)
            if not creation_result.success:
                print(f"❌ Failed to create work item: {creation_result.message}")
                return
            
            work_item_id = creation_result.data['work_item_id']
            print(f"✅ Created work item {work_item_id} for Git integration demo")
            
            # Example 1: Azure Repos integration
            print("\n1. Azure Repos Integration:")
            azure_repos_artifacts = DevelopmentArtifacts(
                repository_url='https://dev.azure.com/myorg/AI-Manufacturing-Demo/_git/main-repo',
                provider=GitProvider.AZURE_REPOS,
                organization='myorg',
                project='AI-Manufacturing-Demo',
                repository_id='main-repo',
                commits=[
                    CommitArtifact(
                        commit_hash='a1b2c3d4e5f6',
                        commit_message=f'AI: Implement authentication service #{work_item_id}',
                        author='AI Manufacturing Bot',
                        author_email='ai-bot@company.com',
                        timestamp=datetime.now(),
                        repository_url='https://dev.azure.com/myorg/AI-Manufacturing-Demo/_git/main-repo',
                        branch='feature/authentication-service',
                        files_changed=['src/auth.py', 'tests/test_auth.py', 'docs/auth.md'],
                        additions=250,
                        deletions=5,
                        work_item_mentions=[work_item_id]
                    )
                ]
            )
            
            azure_result = await mcp.attach_development_artifacts(work_item_id, azure_repos_artifacts)
            if azure_result.success:
                print(f"   ✅ Azure Repos: {azure_result.artifact_count} artifacts attached")
            else:
                print(f"   ❌ Azure Repos: {azure_result.message}")
            
            # Example 2: GitHub integration
            print("\n2. GitHub Integration:")
            github_artifacts = DevelopmentArtifacts(
                repository_url='https://github.com/myorg/ai-manufacturing-demo',
                provider=GitProvider.GITHUB,
                commits=[
                    CommitArtifact(
                        commit_hash='b2c3d4e5f6a1',
                        commit_message=f'AI: Add user profile management #{work_item_id}',
                        author='AI Manufacturing Bot',
                        author_email='ai-bot@company.com',
                        timestamp=datetime.now(),
                        repository_url='https://github.com/myorg/ai-manufacturing-demo',
                        branch='feature/user-profiles',
                        files_changed=['src/profiles.py', 'tests/test_profiles.py'],
                        additions=180,
                        deletions=12,
                        work_item_mentions=[work_item_id]
                    )
                ],
                pull_requests=[
                    PullRequestArtifact(
                        pr_url='https://github.com/myorg/ai-manufacturing-demo/pull/42',
                        pr_id=42,
                        title=f'AI: User Profile Management System #{work_item_id}',
                        description=f'Implements user profile CRUD operations as specified in work item #{work_item_id}',
                        status='open',
                        author='AI Manufacturing Bot',
                        reviewers=['senior-dev', 'tech-lead'],
                        created_date=datetime.now(),
                        source_branch='feature/user-profiles',
                        target_branch='main',
                        work_item_links=[work_item_id]
                    )
                ]
            )
            
            github_result = await mcp.attach_development_artifacts(work_item_id, github_artifacts)
            if github_result.success:
                print(f"   ✅ GitHub: {github_result.artifact_count} artifacts attached")
            else:
                print(f"   ❌ GitHub: {github_result.message}")
            
            # Example 3: GitLab integration
            print("\n3. GitLab Integration:")
            gitlab_artifacts = DevelopmentArtifacts(
                repository_url='https://gitlab.com/myorg/ai-manufacturing-demo',
                provider=GitProvider.GITLAB,
                commits=[
                    CommitArtifact(
                        commit_hash='c3d4e5f6a1b2',
                        commit_message=f'AI: Database connection pooling #{work_item_id}',
                        author='AI Manufacturing Bot',
                        author_email='ai-bot@company.com',
                        timestamp=datetime.now(),
                        repository_url='https://gitlab.com/myorg/ai-manufacturing-demo',
                        branch='feature/db-pooling',
                        files_changed=['src/database.py', 'config/db_config.yaml'],
                        additions=95,
                        deletions=8,
                        work_item_mentions=[work_item_id]
                    )
                ]
            )
            
            gitlab_result = await mcp.attach_development_artifacts(work_item_id, gitlab_artifacts)
            if gitlab_result.success:
                print(f"   ✅ GitLab: {gitlab_result.artifact_count} artifacts attached")
            else:
                print(f"   ❌ GitLab: {gitlab_result.message}")
            
            # Repository activity monitoring setup
            print("\n4. Setting up Repository Activity Monitoring:")
            repositories = [
                'https://dev.azure.com/myorg/AI-Manufacturing-Demo/_git/main-repo',
                'https://github.com/myorg/ai-manufacturing-demo',
                'https://gitlab.com/myorg/ai-manufacturing-demo'
            ]
            
            work_item_patterns = [f'#{work_item_id}', f'work-item-{work_item_id}', f'wi{work_item_id}']
            
            for repo_url in repositories:
                print(f"   Setting up monitoring for: {repo_url}")
                await mcp.monitor_repository_activity(repo_url, work_item_patterns)
                print(f"   ✅ Monitoring configured for work item patterns: {work_item_patterns}")
            
            print(f"\n✅ Git integration example completed for work item {work_item_id}")
            
    except Exception as e:
        print(f"❌ Error in Git integration example: {str(e)}")


async def monitoring_and_dashboard_example():
    """
    Example showing monitoring capabilities and dashboard generation
    """
    print("\n=== Monitoring and Dashboard Example ===")
    
    config = get_default_configuration()
    config.update({
        'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        'personal_access_token': os.getenv('AZURE_DEVOPS_PAT', 'your-pat-token'),
        'enable_metrics': True,
        'metrics_backend': 'prometheus',
        'default_project': 'AI-Manufacturing-Demo'
    })
    
    try:
        async with create_multiplatform_mcp(config) as mcp:
            # Generate manufacturing dashboard
            print("Generating manufacturing dashboard...")
            dashboard = await mcp.generate_manufacturing_dashboard('myorg', 'AI-Manufacturing-Demo')
            
            print(f"📊 Manufacturing Dashboard for {dashboard.organization}/{dashboard.project}")
            print(f"   Generated at: {dashboard.generated_at}")
            print(f"   Active Work Items: {dashboard.active_work_items}")
            print(f"   Completed Work Items: {dashboard.completed_work_items}")
            
            # Manufacturing velocity metrics
            if dashboard.manufacturing_velocity:
                print("\n   Manufacturing Velocity by Phase:")
                for phase, metrics in dashboard.manufacturing_velocity.items():
                    if isinstance(metrics, dict):
                        print(f"     {phase}:")
                        print(f"       - Avg Duration: {metrics.get('average_duration_seconds', 0):.1f}s")
                        print(f"       - Success Rate: {metrics.get('success_rate_percentage', 0):.1f}%")
                        print(f"       - Throughput: {metrics.get('throughput', 0)} items")
            
            # Quality metrics
            if dashboard.quality_metrics:
                print("\n   Quality Metrics:")
                for metric, value in dashboard.quality_metrics.items():
                    print(f"     {metric}: {value}")
            
            # Bottlenecks
            if dashboard.bottlenecks:
                print("\n   ⚠️  Identified Bottlenecks:")
                for bottleneck in dashboard.bottlenecks:
                    print(f"     - {bottleneck}")
            else:
                print("\n   ✅ No bottlenecks identified")
            
            # Team performance
            if dashboard.team_performance:
                print("\n   Team Performance:")
                for metric, value in dashboard.team_performance.items():
                    print(f"     {metric}: {value}")
            
            # System health monitoring
            print("\nSystem Health Monitoring:")
            health = await mcp.get_health_status()
            
            print(f"   Overall Health: {'🟢 Healthy' if health.healthy else '🔴 Unhealthy'}")
            print(f"   Azure DevOps API: {health.azure_devops_api_status}")
            print(f"   Cache System: {health.cache_status}")
            print(f"   Database: {health.database_status}")
            print(f"   Last Check: {health.last_check}")
            
            if health.details:
                print("   Health Details:")
                for key, value in health.details.items():
                    print(f"     {key}: {value}")
            
            print("\n✅ Monitoring and dashboard example completed")
            
    except Exception as e:
        print(f"❌ Error in monitoring example: {str(e)}")


async def complete_manufacturing_workflow_example():
    """
    Complete end-to-end manufacturing workflow example
    """
    print("\n=== Complete Manufacturing Workflow Example ===")
    
    config = get_default_configuration()
    config.update({
        'azure_devops_organization_url': 'https://dev.azure.com/myorg',
        'personal_access_token': os.getenv('AZURE_DEVOPS_PAT', 'your-pat-token'),
        'github_token': os.getenv('GITHUB_TOKEN', 'your-github-token'),
        'enable_metrics': True,
        'default_project': 'AI-Manufacturing-Demo'
    })
    
    try:
        async with create_multiplatform_mcp(config) as mcp:
            print("🏭 Starting complete AI manufacturing workflow...")
            
            # Step 1: Project Analysis
            print("\n1️⃣ Analyzing Azure DevOps project structure...")
            analysis_result = await mcp.analyze_project_structure('myorg', 'AI-Manufacturing-Demo')
            
            if not analysis_result.success:
                print(f"❌ Project analysis failed: {analysis_result.message}")
                return
            
            print("✅ Project structure analyzed and cached")
            
            # Step 2: Create Manufacturing Epic
            print("\n2️⃣ Creating manufacturing epic...")
            epic = WorkItemData(
                organization='myorg',
                project='AI-Manufacturing-Demo',
                work_item_type=AzureDevOpsWorkItemType.EPIC,
                title='AI-Generated E-Commerce Platform',
                description='Complete e-commerce platform generated using AI manufacturing processes',
                area_path='AI-Manufacturing-Demo\\E-Commerce',
                iteration_path='AI-Manufacturing-Demo\\Release 1',
                tags=['ai-generated', 'epic', 'e-commerce'],
                manufacturing_metadata=# No direct replacement needed - using WorkItemData.fields instead(
                    manufacturing_id='epic_ecommerce_001',
                    ai_generator='gpt-4-turbo-architecture',
                    confidence_score=0.92,
                    complexity_score=10,
                    estimated_duration_hours=200
                )
            )
            
            epic_result = await mcp.create_manufacturing_work_item(epic)
            if not epic_result.success:
                print(f"❌ Epic creation failed: {epic_result.message}")
                return
            
            epic_id = epic_result.data['work_item_id']
            print(f"✅ Epic created: #{epic_id}")
            
            # Step 3: Create Feature Work Items
            print("\n3️⃣ Creating feature work items...")
            features = [
                {
                    'title': 'User Management System',
                    'description': 'User registration, authentication, and profile management',
                    'complexity': 8,
                    'confidence': 0.94
                },
                {
                    'title': 'Product Catalog Service',
                    'description': 'Product listing, search, and category management',
                    'complexity': 7,
                    'confidence': 0.91
                },
                {
                    'title': 'Shopping Cart & Checkout',
                    'description': 'Shopping cart functionality and payment processing',
                    'complexity': 9,
                    'confidence': 0.87
                },
                {
                    'title': 'Order Management System',
                    'description': 'Order processing, tracking, and fulfillment',
                    'complexity': 8,
                    'confidence': 0.89
                }
            ]
            
            feature_work_items = []
            for i, feature in enumerate(features):
                work_item = WorkItemData(
                    organization='myorg',
                    project='AI-Manufacturing-Demo',
                    work_item_type=AzureDevOpsWorkItemType.FEATURE,
                    title=feature['title'],
                    description=feature['description'],
                    area_path='AI-Manufacturing-Demo\\E-Commerce',
                    iteration_path='AI-Manufacturing-Demo\\Sprint 1',
                    tags=['ai-generated', 'feature', 'e-commerce'],
                    manufacturing_metadata=# No direct replacement needed - using WorkItemData.fields instead(
                        manufacturing_id=f'feature_ecom_{i+1:03d}',
                        ai_generator='gpt-4-turbo-feature-specialist',
                        confidence_score=feature['confidence'],
                        complexity_score=feature['complexity'],
                        estimated_duration_hours=feature['complexity'] * 6
                    )
                )
                feature_work_items.append(work_item)
            
            bulk_result = await mcp.bulk_create_manufacturing_work_items(feature_work_items)
            successful_features = [r for r in bulk_result.data['results'] if r.success]
            feature_ids = [r.data['work_item_id'] for r in successful_features]
            
            print(f"✅ Created {len(successful_features)} feature work items: {feature_ids}")
            
            # Step 4: Manufacturing Process Simulation
            print("\n4️⃣ Simulating manufacturing process...")
            all_work_items = [epic_id] + feature_ids
            
            manufacturing_phases = [
                (ManufacturingPhase.PLANNING, 20),
                (ManufacturingPhase.CODE_GENERATION, 40),
                (ManufacturingPhase.CODE_REVIEW, 60),
                (ManufacturingPhase.TESTING, 80),
                (ManufacturingPhase.INTEGRATION, 90),
                (ManufacturingPhase.DEPLOYMENT, 95),
                (ManufacturingPhase.COMPLETION, 100)
            ]
            
            for phase, progress_pct in manufacturing_phases:
                print(f"\n   📋 Phase: {phase.value} ({progress_pct}%)")
                
                for work_item_id in all_work_items:
                    progress = ManufacturingProgress(
                        current_phase=phase,
                        progress_percentage=progress_pct,
                        notes=f"Automated progression to {phase.value} phase"
                    )
                    
                    result = await mcp.update_manufacturing_progress(work_item_id, progress)
                    status = "✅" if result.success else "❌"
                    print(f"     {status} Work Item #{work_item_id}: {phase.value}")
                    
                    # Attach artifacts during code generation phase
                    if phase == ManufacturingPhase.CODE_GENERATION and result.success:
                        artifacts = DevelopmentArtifacts(
                            repository_url='https://github.com/myorg/ai-ecommerce-platform',
                            provider=GitProvider.GITHUB,
                            commits=[
                                CommitArtifact(
                                    commit_hash=f'commit_{work_item_id}_{phase.value[:4]}',
                                    commit_message=f'AI: Implement {phase.value} for work item #{work_item_id}',
                                    author='AI Manufacturing Bot',
                                    author_email='ai-bot@company.com',
                                    timestamp=datetime.now(),
                                    repository_url='https://github.com/myorg/ai-ecommerce-platform',
                                    branch=f'feature/work-item-{work_item_id}',
                                    files_changed=[f'src/feature_{work_item_id}.py', f'tests/test_feature_{work_item_id}.py'],
                                    additions=150 + (work_item_id % 100),
                                    deletions=5 + (work_item_id % 10),
                                    work_item_mentions=[work_item_id]
                                )
                            ]
                        )
                        
                        artifact_result = await mcp.attach_development_artifacts(work_item_id, artifacts)
                        if artifact_result.success:
                            print(f"       🔗 Artifacts attached: {artifact_result.artifact_count}")
                
                # Brief pause to simulate processing time
                await asyncio.sleep(0.5)
            
            # Step 5: Generate Final Dashboard
            print("\n5️⃣ Generating final manufacturing dashboard...")
            dashboard = await mcp.generate_manufacturing_dashboard('myorg', 'AI-Manufacturing-Demo')
            
            print(f"\n📊 Final Manufacturing Dashboard:")
            print(f"   Total Work Items Processed: {len(all_work_items)}")
            print(f"   Active Work Items: {dashboard.active_work_items}")
            print(f"   Completed Work Items: {dashboard.completed_work_items}")
            
            if dashboard.manufacturing_velocity:
                print(f"   Manufacturing Velocity: {len(dashboard.manufacturing_velocity)} phases tracked")
            
            if dashboard.bottlenecks:
                print(f"   Bottlenecks Identified: {len(dashboard.bottlenecks)}")
            else:
                print("   ✅ No bottlenecks identified")
            
            # Step 6: Health Check
            print("\n6️⃣ Final system health check...")
            health = await mcp.get_health_status()
            
            print(f"   System Health: {'🟢 Healthy' if health.healthy else '🔴 Unhealthy'}")
            if health.details:
                print(f"   Performance Metrics: {health.details.get('total_performance_metrics', 0)} collected")
                print(f"   Manufacturing Metrics: {health.details.get('total_manufacturing_metrics', 0)} collected")
            
            print(f"\n🎉 Complete manufacturing workflow finished successfully!")
            print(f"   Epic: #{epic_id}")
            print(f"   Features: {feature_ids}")
            print(f"   Total Processing Time: Simulated end-to-end workflow")
            
    except Exception as e:
        print(f"❌ Error in complete workflow example: {str(e)}")


async def main():
    """
    Main function to run all examples
    """
    print("🚀 Azure DevOps AI Manufacturing MCP - Examples")
    print("=" * 60)
    
    examples = [
        ("Basic Usage", basic_usage_example),
        ("Bulk Manufacturing", bulk_manufacturing_example),
        ("Git Integration", git_integration_example),
        ("Monitoring & Dashboard", monitoring_and_dashboard_example),
        ("Complete Workflow", complete_manufacturing_workflow_example)
    ]
    
    for example_name, example_func in examples:
        try:
            print(f"\n🔧 Running {example_name} Example...")
            await example_func()
            print(f"✅ {example_name} Example completed successfully")
        except Exception as e:
            print(f"❌ {example_name} Example failed: {str(e)}")
        
        print("-" * 60)
    
    print("\n🎯 All examples completed!")
    print("\nNext steps:")
    print("1. Set your Azure DevOps PAT: export AZURE_DEVOPS_PAT='your-token'")
    print("2. Configure your organization URL in the examples")
    print("3. Run individual examples or customize for your use case")
    print("4. Check the docs/ directory for detailed documentation")


if __name__ == '__main__':
    # Run all examples
    asyncio.run(main())
