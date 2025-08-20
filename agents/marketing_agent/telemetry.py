import logging
import os
from google.cloud import logging as cloud_logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.gcp_monitoring import GcpMonitoringMetricsExporter
from opentelemetry.exporter.gcp_trace import GcpTraceExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

def setup_logging_metrics():
    # Cloud Logging
    try:
        client = cloud_logging.Client()
        client.setup_logging()
    except Exception:
        logging.basicConfig(level=logging.INFO)

    # OpenTelemetry -> Cloud Monitoring/Trace
    resource = Resource.create({"service.name": "marketing-agent"})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(GcpTraceExporter()))
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(GcpMonitoringMetricsExporter())],
        resource=resource,
    )
    metrics.set_meter_provider(meter_provider)

LOGGER = logging.getLogger("marketing-agent")
TRACER = trace.get_tracer(__name__)
METER = metrics.get_meter(__name__)

# Basic counters/histograms
REQUEST_COUNTER = METER.create_counter("requests_total")
ERROR_COUNTER = METER.create_counter("errors_total")
LATENCY_MS = METER.create_histogram("latency_ms")
