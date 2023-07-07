# OpenTelemetryLogParser

OpenTelemetryLogParser is a log parsing utility for OpenTelemetry logs. It allows you to extract structured data from log files generated by OpenTelemetry instrumentation.

## Features

**Trace ID Extraction**: Extract trace IDs from the log file to identify and group related spans.

**Span Merging**: Merge spans from different services with the same trace ID to provide a unified view of the trace.

**Error Log Handling**: Capture and analyze error logs within the trace to identify and investigate any errors or exceptions.

**Process Information**: Include process-related information in the generated JSON file to provide context about the services involved.

**Selective Processing**: The parser processes only the lines that contain OpenTelemetry log data, allowing for efficient extraction of relevant information. Other log data lines are ignored.
## Installation

1. Download the **'otlpLogParser.py'** file from this repository.

2. Locate the log file ( in txt format ) generated from OpenTelemetry instrumentation. The log file should contain the necessary trace information.

## Usage
Run the following command to execute the log parser and generate a JSON file based on trace IDs:

```shell
python otlpLogParser.py <path_to_log_file>
```

Replace <path_to_log_file> with the path to your OpenTelemetry log file.

The tool will parse the log file, extract trace IDs, and merge spans from different services with the same trace ID. The generated JSON file will contain the trace IDs and their corresponding spans.

The OpenTelemetryLogParser selectively processes lines that contain OpenTelemetry log data, allowing for efficient extraction of relevant information. This ensures that only the necessary log data is processed, improving the overall performance of the parser.


