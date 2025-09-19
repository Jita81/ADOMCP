"""
Azure DevOps Multi-Platform MCP - Performance Monitoring

This module provides comprehensive monitoring for Azure DevOps, GitHub, and GitLab
with performance metrics, system health, and business insights.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .types import (
    HealthStatus, DashboardData, OperationResult
)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Optional[Dict[str, str]] = None
    unit: str = ""


@dataclass
class WorkflowMetrics:
    """Multi-platform workflow metrics"""
    organization: str
    project: str
    phase: str
    duration_seconds: float
    success: bool
    work_item_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class AzureDevOpsMultiPlatformMonitor:
    """
    Comprehensive multi-platform monitoring for Azure DevOps, GitHub, and GitLab

    Monitoring Categories:
    1. Performance Metrics (response times, throughput, error rates)
    2. Workflow Metrics (cycle times, quality scores, bottlenecks)
    3. System Health (API connectivity, cache performance, database health)
    4. Business Metrics (work item velocity, success rates)
    5. Multi-platform Analytics integration for advanced insights
    """
    
    def __init__(self, metrics_backend: str = 'prometheus'):
        """
        Initialize monitoring backend with Azure DevOps integration
        
        Args:
            metrics_backend: Metrics storage backend ('prometheus', 'influxdb', 'cloudwatch')
        """
        self.metrics_backend = metrics_backend
        
        # In-memory metrics storage for demonstration
        self._performance_metrics: List[PerformanceMetric] = []
        self._manufacturing_metrics: List[ManufacturingMetrics] = []
        self._system_health_history: List[HealthStatus] = []
        
        # Metrics aggregation cache
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        
        # Initialize metrics backend
        self._init_metrics_backend()
    
    def _init_metrics_backend(self):
        """Initialize metrics backend (Prometheus, InfluxDB, etc.)"""
        if self.metrics_backend == 'prometheus':
            self._init_prometheus_metrics()
        elif self.metrics_backend == 'influxdb':
            self._init_influxdb_metrics()
        elif self.metrics_backend == 'cloudwatch':
            self._init_cloudwatch_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        try:
            from prometheus_client import Counter, Histogram, Gauge
            
            # Manufacturing performance metrics
            self.manufacturing_duration_histogram = Histogram(
                'azure_devops_manufacturing_phase_duration_seconds',
                'Duration of manufacturing phases',
                ['organization', 'project', 'phase', 'success']
            )
            
            self.manufacturing_operations_counter = Counter(
                'azure_devops_manufacturing_operations_total',
                'Total manufacturing operations',
                ['organization', 'project', 'phase', 'operation_type', 'status']
            )
            
            self.work_items_active_gauge = Gauge(
                'azure_devops_work_items_active',
                'Number of active work items',
                ['organization', 'project', 'phase']
            )
            
            # System health metrics
            self.api_response_time_histogram = Histogram(
                'azure_devops_api_response_time_seconds',
                'Azure DevOps API response times',
                ['endpoint', 'status_code']
            )
            
            self.cache_hit_rate_gauge = Gauge(
                'azure_devops_cache_hit_rate',
                'Cache hit rate percentage',
                ['cache_type']
            )
            
            print("Prometheus metrics initialized")
            
        except ImportError:
            print("Prometheus client not available - using in-memory metrics only")
    
    def _init_influxdb_metrics(self):
        """Initialize InfluxDB metrics"""
        # TODO: Implement InfluxDB integration
        pass
    
    def _init_cloudwatch_metrics(self):
        """Initialize CloudWatch metrics"""
        # TODO: Implement CloudWatch integration
        pass
    
    async def track_manufacturing_performance(self, organization: str, project: str,
                                            work_item_id: int, phase: ManufacturingPhase, 
                                            duration: float, success: bool, metadata: Optional[Dict[str, Any]] = None):
        """
        Track manufacturing phase performance with Azure DevOps Analytics
        
        Args:
            organization: Azure DevOps organization
            project: Azure DevOps project
            work_item_id: Work item ID
            phase: Manufacturing phase
            duration: Phase duration in seconds
            success: Whether the phase completed successfully
            metadata: Additional metadata for the operation
        """
        try:
            # Create manufacturing metrics record
            manufacturing_metric = ManufacturingMetrics(
                organization=organization,
                project=project,
                phase=phase,
                duration_seconds=duration,
                success=success,
                work_item_id=work_item_id,
                metadata=metadata or {}
            )
            
            # Store in memory
            self._manufacturing_metrics.append(manufacturing_metric)
            
            # Update Prometheus metrics if available
            if hasattr(self, 'manufacturing_duration_histogram'):
                self.manufacturing_duration_histogram.labels(
                    organization=organization,
                    project=project,
                    phase=phase.value,
                    success=str(success)
                ).observe(duration)
                
                self.manufacturing_operations_counter.labels(
                    organization=organization,
                    project=project,
                    phase=phase.value,
                    operation_type='phase_transition',
                    status='success' if success else 'failure'
                ).inc()
            
            # Create performance metrics
            performance_metric = PerformanceMetric(
                metric_name='manufacturing_phase_duration',
                value=duration,
                tags={
                    'organization': organization,
                    'project': project,
                    'phase': phase.value,
                    'work_item_id': str(work_item_id),
                    'success': str(success)
                },
                unit='seconds'
            )
            
            self._performance_metrics.append(performance_metric)
            
            # Invalidate dashboard cache
            self._invalidate_dashboard_cache(organization, project)
            
        except Exception as e:
            print(f"Error tracking manufacturing performance: {str(e)}")
    
    async def track_api_performance(self, endpoint: str, duration: float, status_code: int):
        """Track Azure DevOps API performance"""
        try:
            # Update Prometheus metrics if available
            if hasattr(self, 'api_response_time_histogram'):
                self.api_response_time_histogram.labels(
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).observe(duration)
            
            # Create performance metric
            performance_metric = PerformanceMetric(
                metric_name='api_response_time',
                value=duration,
                tags={
                    'endpoint': endpoint,
                    'status_code': str(status_code)
                },
                unit='seconds'
            )
            
            self._performance_metrics.append(performance_metric)
            
        except Exception as e:
            print(f"Error tracking API performance: {str(e)}")
    
    async def track_cache_performance(self, cache_type: str, hit_rate: float):
        """Track cache performance metrics"""
        try:
            # Update Prometheus metrics if available
            if hasattr(self, 'cache_hit_rate_gauge'):
                self.cache_hit_rate_gauge.labels(cache_type=cache_type).set(hit_rate)
            
            # Create performance metric
            performance_metric = PerformanceMetric(
                metric_name='cache_hit_rate',
                value=hit_rate,
                tags={'cache_type': cache_type},
                unit='percentage'
            )
            
            self._performance_metrics.append(performance_metric)
            
        except Exception as e:
            print(f"Error tracking cache performance: {str(e)}")
    
    async def generate_manufacturing_dashboard(self, organization: str, project: str) -> DashboardData:
        """
        Generate real-time manufacturing dashboard using Azure DevOps data
        
        Dashboard Components:
        - Manufacturing velocity charts using Azure DevOps Analytics
        - Work item cycle time analysis
        - Quality metrics from Azure Pipelines
        - Team performance metrics
        - Bottleneck identification using Azure Boards data
        """
        try:
            # Check cache first
            cache_key = f"dashboard:{organization}:{project}"
            cached_dashboard = self._get_cached_dashboard(cache_key)
            if cached_dashboard:
                return cached_dashboard
            
            # Generate fresh dashboard data
            dashboard_data = await self._generate_fresh_dashboard_data(organization, project)
            
            # Cache the dashboard data
            self._cache_dashboard(cache_key, dashboard_data)
            
            return dashboard_data
            
        except Exception as e:
            print(f"Error generating manufacturing dashboard: {str(e)}")
            return DashboardData(
                organization=organization,
                project=project,
                manufacturing_velocity={},
                active_work_items=0,
                completed_work_items=0,
                quality_metrics={},
                bottlenecks=[],
                team_performance={}
            )
    
    async def _generate_fresh_dashboard_data(self, organization: str, project: str) -> DashboardData:
        """Generate fresh dashboard data from metrics and Azure DevOps"""
        # Filter metrics for the specific organization and project
        project_metrics = [
            m for m in self._manufacturing_metrics 
            if m.organization == organization and m.project == project
        ]
        
        # Calculate manufacturing velocity
        manufacturing_velocity = await self._calculate_manufacturing_velocity(project_metrics)
        
        # Count active and completed work items
        active_work_items = await self._count_active_work_items(organization, project)
        completed_work_items = await self._count_completed_work_items(organization, project)
        
        # Calculate quality metrics
        quality_metrics = await self._calculate_quality_metrics(project_metrics)
        
        # Identify bottlenecks
        bottlenecks = await self._identify_bottlenecks(project_metrics)
        
        # Calculate team performance
        team_performance = await self._calculate_team_performance(organization, project)
        
        return DashboardData(
            organization=organization,
            project=project,
            manufacturing_velocity=manufacturing_velocity,
            active_work_items=active_work_items,
            completed_work_items=completed_work_items,
            quality_metrics=quality_metrics,
            bottlenecks=bottlenecks,
            team_performance=team_performance
        )
    
    async def _calculate_manufacturing_velocity(self, metrics: List[ManufacturingMetrics]) -> Dict[str, float]:
        """Calculate manufacturing velocity metrics"""
        if not metrics:
            return {}
        
        # Group metrics by phase
        phase_metrics = {}
        for metric in metrics:
            phase_name = metric.phase.value
            if phase_name not in phase_metrics:
                phase_metrics[phase_name] = []
            phase_metrics[phase_name].append(metric)
        
        # Calculate average duration and success rate for each phase
        velocity_metrics = {}
        for phase_name, phase_data in phase_metrics.items():
            avg_duration = sum(m.duration_seconds for m in phase_data) / len(phase_data)
            success_rate = sum(1 for m in phase_data if m.success) / len(phase_data) * 100
            throughput = len(phase_data)  # Number of items processed
            
            velocity_metrics[phase_name] = {
                'average_duration_seconds': round(avg_duration, 2),
                'success_rate_percentage': round(success_rate, 2),
                'throughput': throughput
            }
        
        return velocity_metrics
    
    async def _count_active_work_items(self, organization: str, project: str) -> int:
        """Count active work items from recent metrics"""
        # Get unique work item IDs from recent metrics (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_metrics = [
            m for m in self._manufacturing_metrics
            if (m.organization == organization and m.project == project and 
                m.timestamp >= cutoff_time and m.phase != ManufacturingPhase.COMPLETION)
        ]
        
        active_work_items = set(m.work_item_id for m in recent_metrics)
        return len(active_work_items)
    
    async def _count_completed_work_items(self, organization: str, project: str) -> int:
        """Count completed work items from recent metrics"""
        # Get work items that reached completion phase
        cutoff_time = datetime.now() - timedelta(days=30)  # Last 30 days
        completion_metrics = [
            m for m in self._manufacturing_metrics
            if (m.organization == organization and m.project == project and 
                m.timestamp >= cutoff_time and m.phase == ManufacturingPhase.COMPLETION and m.success)
        ]
        
        completed_work_items = set(m.work_item_id for m in completion_metrics)
        return len(completed_work_items)
    
    async def _calculate_quality_metrics(self, metrics: List[ManufacturingMetrics]) -> Dict[str, Any]:
        """Calculate quality metrics from manufacturing data"""
        if not metrics:
            return {}
        
        # Overall success rate
        total_operations = len(metrics)
        successful_operations = sum(1 for m in metrics if m.success)
        overall_success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        # Success rate by phase
        phase_success_rates = {}
        phase_groups = {}
        for metric in metrics:
            phase_name = metric.phase.value
            if phase_name not in phase_groups:
                phase_groups[phase_name] = []
            phase_groups[phase_name].append(metric)
        
        for phase_name, phase_metrics in phase_groups.items():
            successful = sum(1 for m in phase_metrics if m.success)
            total = len(phase_metrics)
            success_rate = (successful / total * 100) if total > 0 else 0
            phase_success_rates[phase_name] = round(success_rate, 2)
        
        # Average cycle time (from analysis to completion)
        cycle_times = []
        work_item_phases = {}
        
        # Group metrics by work item to calculate cycle times
        for metric in metrics:
            if metric.work_item_id not in work_item_phases:
                work_item_phases[metric.work_item_id] = []
            work_item_phases[metric.work_item_id].append(metric)
        
        # Calculate cycle time for work items that have both start and end phases
        for work_item_id, work_item_metrics in work_item_phases.items():
            work_item_metrics.sort(key=lambda x: x.timestamp)
            
            # Find first and last successful operations
            first_operation = None
            last_operation = None
            
            for metric in work_item_metrics:
                if metric.success:
                    if first_operation is None:
                        first_operation = metric
                    last_operation = metric
            
            if first_operation and last_operation and first_operation != last_operation:
                cycle_time = (last_operation.timestamp - first_operation.timestamp).total_seconds()
                cycle_times.append(cycle_time)
        
        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
        
        return {
            'overall_success_rate_percentage': round(overall_success_rate, 2),
            'phase_success_rates': phase_success_rates,
            'average_cycle_time_seconds': round(avg_cycle_time, 2),
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'work_items_with_complete_cycles': len(cycle_times)
        }
    
    async def _identify_bottlenecks(self, metrics: List[ManufacturingMetrics]) -> List[str]:
        """Identify bottlenecks in the manufacturing process"""
        if not metrics:
            return []
        
        bottlenecks = []
        
        # Group by phase and calculate average duration
        phase_durations = {}
        phase_failure_rates = {}
        
        for metric in metrics:
            phase_name = metric.phase.value
            if phase_name not in phase_durations:
                phase_durations[phase_name] = []
                phase_failure_rates[phase_name] = []
            
            phase_durations[phase_name].append(metric.duration_seconds)
            phase_failure_rates[phase_name].append(not metric.success)
        
        # Calculate averages
        avg_durations = {}
        failure_rates = {}
        
        for phase_name in phase_durations:
            avg_durations[phase_name] = sum(phase_durations[phase_name]) / len(phase_durations[phase_name])
            failure_rates[phase_name] = sum(phase_failure_rates[phase_name]) / len(phase_failure_rates[phase_name]) * 100
        
        # Identify bottlenecks based on duration and failure rate
        overall_avg_duration = sum(avg_durations.values()) / len(avg_durations) if avg_durations else 0
        overall_failure_rate = sum(failure_rates.values()) / len(failure_rates) if failure_rates else 0
        
        for phase_name in avg_durations:
            # Phase is a bottleneck if it takes significantly longer than average
            if avg_durations[phase_name] > overall_avg_duration * 1.5:
                bottlenecks.append(f"High duration in {phase_name} phase ({avg_durations[phase_name]:.1f}s avg)")
            
            # Phase is a bottleneck if it has high failure rate
            if failure_rates[phase_name] > overall_failure_rate * 2 and failure_rates[phase_name] > 10:
                bottlenecks.append(f"High failure rate in {phase_name} phase ({failure_rates[phase_name]:.1f}%)")
        
        return bottlenecks
    
    async def _calculate_team_performance(self, organization: str, project: str) -> Dict[str, Any]:
        """Calculate team performance metrics"""
        # This would integrate with Azure DevOps Analytics API to get team-specific data
        # For now, return simulated team performance data
        
        return {
            'total_teams': 3,
            'active_teams': 3,
            'team_velocity': {
                'Team A': {'story_points_per_sprint': 45, 'cycle_time_days': 3.2},
                'Team B': {'story_points_per_sprint': 38, 'cycle_time_days': 4.1},
                'Team C': {'story_points_per_sprint': 52, 'cycle_time_days': 2.8}
            },
            'collaboration_score': 8.5,  # Out of 10
            'knowledge_sharing_index': 7.2  # Out of 10
        }
    
    async def monitor_azure_devops_api_health(self) -> HealthStatus:
        """Monitor Azure DevOps API connectivity and rate limits"""
        try:
            # Simulate API health check
            # In a real implementation, this would make actual API calls to Azure DevOps
            api_status = "healthy"
            cache_status = "healthy"
            database_status = "healthy"
            
            # Check recent API performance metrics
            recent_api_metrics = [
                m for m in self._performance_metrics
                if (m.metric_name == 'api_response_time' and 
                    m.timestamp >= datetime.now() - timedelta(minutes=5))
            ]
            
            # Determine API health based on recent metrics
            if recent_api_metrics:
                avg_response_time = sum(m.value for m in recent_api_metrics) / len(recent_api_metrics)
                if avg_response_time > 5.0:  # More than 5 seconds average
                    api_status = "degraded"
                elif avg_response_time > 10.0:  # More than 10 seconds average
                    api_status = "unhealthy"
            
            # Check cache performance
            cache_metrics = [
                m for m in self._performance_metrics
                if (m.metric_name == 'cache_hit_rate' and 
                    m.timestamp >= datetime.now() - timedelta(minutes=5))
            ]
            
            if cache_metrics:
                avg_hit_rate = sum(m.value for m in cache_metrics) / len(cache_metrics)
                if avg_hit_rate < 70:  # Less than 70% hit rate
                    cache_status = "degraded"
                elif avg_hit_rate < 50:  # Less than 50% hit rate
                    cache_status = "unhealthy"
            
            overall_healthy = all(status == "healthy" for status in [api_status, cache_status, database_status])
            
            health_status = HealthStatus(
                healthy=overall_healthy,
                azure_devops_api_status=api_status,
                cache_status=cache_status,
                database_status=database_status,
                details={
                    'recent_api_calls': len(recent_api_metrics),
                    'average_response_time': sum(m.value for m in recent_api_metrics) / len(recent_api_metrics) if recent_api_metrics else 0,
                    'cache_hit_rate': sum(m.value for m in cache_metrics) / len(cache_metrics) if cache_metrics else 0,
                    'total_performance_metrics': len(self._performance_metrics),
                    'total_manufacturing_metrics': len(self._manufacturing_metrics)
                }
            )
            
            # Store health status in history
            self._system_health_history.append(health_status)
            
            # Keep only last 100 health checks
            if len(self._system_health_history) > 100:
                self._system_health_history = self._system_health_history[-100:]
            
            return health_status
            
        except Exception as e:
            return HealthStatus(
                healthy=False,
                azure_devops_api_status="error",
                cache_status="unknown",
                database_status="unknown",
                details={'error': str(e)}
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        if not self._performance_metrics:
            return {}
        
        # Calculate summary statistics
        api_metrics = [m for m in self._performance_metrics if m.metric_name == 'api_response_time']
        cache_metrics = [m for m in self._performance_metrics if m.metric_name == 'cache_hit_rate']
        manufacturing_metrics = [m for m in self._performance_metrics if m.metric_name == 'manufacturing_phase_duration']
        
        summary = {
            'total_metrics_collected': len(self._performance_metrics),
            'collection_period_hours': 24,  # Assuming 24-hour collection period
            'api_performance': {
                'total_api_calls': len(api_metrics),
                'average_response_time': sum(m.value for m in api_metrics) / len(api_metrics) if api_metrics else 0,
                'max_response_time': max(m.value for m in api_metrics) if api_metrics else 0,
                'min_response_time': min(m.value for m in api_metrics) if api_metrics else 0
            },
            'cache_performance': {
                'average_hit_rate': sum(m.value for m in cache_metrics) / len(cache_metrics) if cache_metrics else 0,
                'cache_types_monitored': len(set(m.tags.get('cache_type', '') for m in cache_metrics if m.tags))
            },
            'manufacturing_performance': {
                'total_phase_transitions': len(manufacturing_metrics),
                'average_phase_duration': sum(m.value for m in manufacturing_metrics) / len(manufacturing_metrics) if manufacturing_metrics else 0
            }
        }
        
        return summary
    
    # Dashboard caching methods
    def _get_cached_dashboard(self, cache_key: str) -> Optional[DashboardData]:
        """Get cached dashboard data"""
        if cache_key in self._metrics_cache and cache_key in self._cache_expiry:
            if datetime.now() < self._cache_expiry[cache_key]:
                return self._metrics_cache[cache_key]
            else:
                # Expired cache
                del self._metrics_cache[cache_key]
                del self._cache_expiry[cache_key]
        
        return None
    
    def _cache_dashboard(self, cache_key: str, dashboard_data: DashboardData):
        """Cache dashboard data"""
        self._metrics_cache[cache_key] = dashboard_data
        self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)  # 5-minute cache
    
    def _invalidate_dashboard_cache(self, organization: str, project: str):
        """Invalidate dashboard cache for specific project"""
        cache_key = f"dashboard:{organization}:{project}"
        if cache_key in self._metrics_cache:
            del self._metrics_cache[cache_key]
        if cache_key in self._cache_expiry:
            del self._cache_expiry[cache_key]
