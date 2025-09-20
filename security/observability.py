"""
OpenTelemetry integration for ADOMCP
Implements distributed tracing, metrics, and structured logging
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from functools import wraps
import threading
from contextlib import contextmanager

# Try to import OpenTelemetry - graceful fallback if not available
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None

# OpenTelemetry imports handled above

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Container for security events"""
    event_id: str
    event_type: str
    timestamp: datetime
    user_id: Optional[str]
    client_ip: str
    endpoint: str
    correlation_id: str
    severity: str  # INFO, WARNING, CRITICAL
    details: Dict[str, Any]
    action_taken: Optional[str] = None

@dataclass
class RequestMetrics:
    """Container for request metrics"""
    correlation_id: str
    endpoint: str
    method: str
    start_time: float
    end_time: Optional[float]
    duration_ms: Optional[float]
    status_code: Optional[int]
    user_id: Optional[str]
    client_ip: str
    user_agent: str
    request_size: int
    response_size: Optional[int]
    error: Optional[str]

class ObservabilityManager:
    """
    Comprehensive observability for ADOMCP using OpenTelemetry
    Implements distributed tracing, metrics, and security event logging
    """
    
    def __init__(self):
        self.service_name = "adomcp"
        self.service_version = "2.2.0"
        self.tracer = None
        self.meter = None
        self.security_events: List[SecurityEvent] = []
        self.request_metrics: List[RequestMetrics] = []
        self.active_requests: Dict[str, RequestMetrics] = {}
        self._lock = threading.Lock()
        
        if OTEL_AVAILABLE:
            self._initialize_telemetry()
        else:
            logger.warning("OpenTelemetry not available - using structured logging only")
    
    def _initialize_telemetry(self):
        """Initialize OpenTelemetry providers and exporters"""
        try:
            # Initialize tracing
            trace_provider = TracerProvider()
            
            # Configure exporters based on environment
            otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
            
            if otlp_endpoint:
                # Production: Use OTLP exporter (e.g., to Jaeger, Zipkin, or cloud providers)
                span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            else:
                # Development: Use console exporter
                span_exporter = ConsoleSpanExporter()
            
            span_processor = BatchSpanProcessor(span_exporter)
            trace_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(trace_provider)
            
            self.tracer = trace.get_tracer(
                instrumenting_module_name=self.service_name,
                instrumenting_library_version=self.service_version
            )
            
            # Initialize metrics
            if otlp_endpoint:
                metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
            else:
                metric_exporter = ConsoleMetricExporter()
            
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=10000  # Export every 10 seconds
            )
            
            metrics_provider = MeterProvider(metric_readers=[metric_reader])
            metrics.set_meter_provider(metrics_provider)
            
            self.meter = metrics.get_meter(
                name=self.service_name,
                version=self.service_version
            )
            
            # Create metrics instruments
            self._create_metrics()
            
            # Auto-instrument HTTP libraries
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()
            
            logger.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {str(e)}")
            self.tracer = None
            self.meter = None
    
    def _create_metrics(self):
        """Create metrics instruments"""
        if not self.meter:
            return
        
        # Request metrics
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )
        
        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_ms",
            description="HTTP request duration in milliseconds",
            unit="ms"
        )
        
        self.request_size = self.meter.create_histogram(
            name="http_request_size_bytes",
            description="HTTP request size in bytes",
            unit="By"
        )
        
        # Security metrics
        self.security_events_counter = self.meter.create_counter(
            name="security_events_total",
            description="Total number of security events",
            unit="1"
        )
        
        self.rate_limit_counter = self.meter.create_counter(
            name="rate_limit_violations_total",
            description="Total number of rate limit violations",
            unit="1"
        )
        
        # API key metrics
        self.api_key_operations_counter = self.meter.create_counter(
            name="api_key_operations_total",
            description="Total number of API key operations",
            unit="1"
        )
    
    def start_request_span(self, correlation_id: str, endpoint: str, method: str,
                          client_ip: str, user_agent: str, request_size: int,
                          user_id: Optional[str] = None) -> Optional[Any]:
        """
        Start a new request span with comprehensive attributes
        """
        if not self.tracer:
            return None
        
        span = self.tracer.start_span(
            name=f"{method} {endpoint}",
            attributes={
                "http.method": method,
                "http.url": endpoint,
                "http.client_ip": client_ip,
                "http.user_agent": user_agent,
                "http.request_size": request_size,
                "service.name": self.service_name,
                "service.version": self.service_version,
                "correlation.id": correlation_id,
                "user.id": user_id or "anonymous"
            }
        )
        
        # Store request metrics
        request_metric = RequestMetrics(
            correlation_id=correlation_id,
            endpoint=endpoint,
            method=method,
            start_time=time.time(),
            end_time=None,
            duration_ms=None,
            status_code=None,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            request_size=request_size,
            response_size=None,
            error=None
        )
        
        with self._lock:
            self.active_requests[correlation_id] = request_metric
        
        return span
    
    def end_request_span(self, correlation_id: str, span: Any, status_code: int,
                        response_size: int, error: Optional[str] = None):
        """
        End request span and record metrics
        """
        if span and self.tracer:
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.response_size", response_size)
            
            if error:
                span.record_exception(Exception(error))
                span.set_status(trace.Status(trace.StatusCode.ERROR, error))
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
            
            span.end()
        
        # Update request metrics
        with self._lock:
            if correlation_id in self.active_requests:
                request_metric = self.active_requests[correlation_id]
                end_time = time.time()
                request_metric.end_time = end_time
                request_metric.duration_ms = (end_time - request_metric.start_time) * 1000
                request_metric.status_code = status_code
                request_metric.response_size = response_size
                request_metric.error = error
                
                # Move to completed metrics
                self.request_metrics.append(request_metric)
                del self.active_requests[correlation_id]
                
                # Record telemetry metrics
                self._record_request_metrics(request_metric)
    
    def _record_request_metrics(self, request_metric: RequestMetrics):
        """Record metrics to OpenTelemetry"""
        if not self.meter:
            return
        
        labels = {
            "method": request_metric.method,
            "endpoint": request_metric.endpoint,
            "status_code": str(request_metric.status_code or 0),
            "success": "true" if request_metric.error is None else "false"
        }
        
        self.request_counter.add(1, labels)
        
        if request_metric.duration_ms:
            self.request_duration.record(request_metric.duration_ms, labels)
        
        if request_metric.request_size:
            self.request_size.record(request_metric.request_size, labels)
    
    def log_security_event(self, event_type: str, correlation_id: str, 
                          client_ip: str, endpoint: str, severity: str = "INFO",
                          user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                          action_taken: Optional[str] = None):
        """
        Log security events with structured data
        """
        security_event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            client_ip=client_ip,
            endpoint=endpoint,
            correlation_id=correlation_id,
            severity=severity,
            details=details or {},
            action_taken=action_taken
        )
        
        with self._lock:
            self.security_events.append(security_event)
        
        # Log structured event
        logger.info(
            f"Security Event: {event_type}",
            extra={
                "event_id": security_event.event_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "client_ip": client_ip,
                "endpoint": endpoint,
                "severity": severity,
                "user_id": user_id,
                "details": details,
                "action_taken": action_taken
            }
        )
        
        # Record security metrics
        if self.meter:
            self.security_events_counter.add(1, {
                "event_type": event_type,
                "severity": severity,
                "endpoint": endpoint
            })
    
    def log_rate_limit_violation(self, correlation_id: str, client_ip: str, 
                                endpoint: str, limit_type: str, user_id: Optional[str] = None):
        """
        Log rate limit violations
        """
        self.log_security_event(
            event_type="rate_limit_violation",
            correlation_id=correlation_id,
            client_ip=client_ip,
            endpoint=endpoint,
            severity="WARNING",
            user_id=user_id,
            details={
                "limit_type": limit_type,
                "timestamp": datetime.now().isoformat()
            },
            action_taken="request_blocked"
        )
        
        if self.meter:
            self.rate_limit_counter.add(1, {
                "limit_type": limit_type,
                "endpoint": endpoint
            })
    
    def log_api_key_operation(self, operation: str, correlation_id: str,
                             user_id: str, platform: str, success: bool,
                             details: Optional[Dict[str, Any]] = None):
        """
        Log API key operations for audit trail
        """
        self.log_security_event(
            event_type="api_key_operation",
            correlation_id=correlation_id,
            client_ip="internal",  # Internal operation
            endpoint="/api/keys",
            severity="INFO" if success else "WARNING",
            user_id=user_id,
            details={
                "operation": operation,
                "platform": platform,
                "success": success,
                **(details or {})
            }
        )
        
        if self.meter:
            self.api_key_operations_counter.add(1, {
                "operation": operation,
                "platform": platform,
                "success": "true" if success else "false"
            })
    
    @contextmanager
    def trace_operation(self, operation_name: str, correlation_id: str, **attributes):
        """
        Context manager for tracing operations
        """
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(
            name=operation_name,
            attributes={
                "correlation.id": correlation_id,
                **attributes
            }
        ) as span:
            yield span
    
    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get metrics summary for the specified time window
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            # Filter recent request metrics
            recent_requests = [
                r for r in self.request_metrics
                if r.end_time and datetime.fromtimestamp(r.end_time) > cutoff_time
            ]
            
            # Filter recent security events
            recent_events = [
                e for e in self.security_events
                if e.timestamp > cutoff_time
            ]
        
        # Calculate metrics
        if recent_requests:
            response_times = [r.duration_ms for r in recent_requests if r.duration_ms]
            success_count = len([r for r in recent_requests if r.error is None])
            
            summary = {
                "time_window_minutes": time_window_minutes,
                "request_count": len(recent_requests),
                "success_rate": (success_count / len(recent_requests)) * 100,
                "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
                "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                "security_events_count": len(recent_events),
                "critical_events_count": len([e for e in recent_events if e.severity == "CRITICAL"]),
                "endpoints": list(set([r.endpoint for r in recent_requests])),
                "unique_users": len(set([r.user_id for r in recent_requests if r.user_id])),
                "unique_ips": len(set([r.client_ip for r in recent_requests]))
            }
        else:
            summary = {
                "time_window_minutes": time_window_minutes,
                "request_count": 0,
                "success_rate": 0,
                "avg_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "security_events_count": len(recent_events),
                "critical_events_count": len([e for e in recent_events if e.severity == "CRITICAL"]),
                "endpoints": [],
                "unique_users": 0,
                "unique_ips": 0
            }
        
        return summary

# Decorator for automatic tracing
def trace_function(operation_name: Optional[str] = None):
    """
    Decorator to automatically trace function calls
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            correlation_id = kwargs.get('correlation_id', str(uuid.uuid4()))
            
            with observability_manager.trace_operation(op_name, correlation_id):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Global observability manager instance
observability_manager = ObservabilityManager()

def start_request_trace(correlation_id: str, endpoint: str, method: str,
                       client_ip: str, user_agent: str, request_size: int,
                       user_id: Optional[str] = None):
    """Convenience function to start request tracing"""
    return observability_manager.start_request_span(
        correlation_id, endpoint, method, client_ip, user_agent, request_size, user_id
    )

def end_request_trace(correlation_id: str, span: Any, status_code: int,
                     response_size: int, error: Optional[str] = None):
    """Convenience function to end request tracing"""
    observability_manager.end_request_span(correlation_id, span, status_code, response_size, error)
