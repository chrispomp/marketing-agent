import logging
import os
from google.cloud import logging as cloud_logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
# [MODIFIED] Import paths updated for the new, stable Google Cloud exporters
from opentelemetry.exporter.google.cloud.monitoring import GoogleCloudMonitoringMetricsExporter
from opentelemetry.exporter.google.cloud.trace import GoogleCloudTraceExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

def setup_logging_metrics():
    """
    Configures Google Cloud Logging and sets up OpenTelemetry for metrics and tracing.
    """
    # Configure Cloud Logging
    try:
        client = cloud_logging.Client()
        client.setup_logging()
        logging.info("Successfully set up Google Cloud Logging.")
    except Exception as e:
        # Fallback to basic logging if Cloud Logging setup fails
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Could not set up Google Cloud Logging: {e}. Falling back to basicConfig.")

    # Configure OpenTelemetry for Cloud Monitoring and Cloud Trace
    resource = Resource.create({"service.name": "marketing-agent"})
    
    # Set up the TracerProvider for Cloud Trace
    tracer_provider = TracerProvider(resource=resource)
    # [MODIFIED] Use the updated GoogleCloudTraceExporter class
    trace_exporter = GoogleCloudTraceExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Set up the MeterProvider for Cloud Monitoring
    # [MODIFIED] Use the updated GoogleCloudMonitoringMetricsExporter class
    metrics_exporter = GoogleCloudMonitoringMetricsExporter()
    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(metrics_exporter)],
        resource=resource,
    )
    metrics.set_meter_provider(meter_provider)
    logging.info("OpenTelemetry for metrics and tracing has been configured.")

# Initialize logging and telemetry
setup_logging_metrics()

# Global instances for logging, tracing, and metrics
LOGGER = logging.getLogger("marketing-agent")
TRACER = trace.get_tracer(__name__)
METER = metrics.get_meter(__name__)

# Define custom metrics
REQUEST_COUNTER = METER.create_counter(
    name="requests_total",
    description="Total number of requests processed."
)
ERROR_COUNTER = METER.create_counter(
    name="errors_total",
    description="Total number of errors encountered."
)
LATENCY_MS = METER.create_histogram(
    name="latency_ms",
    description="Request latency in milliseconds.",
    unit="ms"
)
