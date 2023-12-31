# **OpenTelemetry with OTLP Log Parser Readme**
This readme provides instructions on how to work with OpenTelemetry, a powerful observability framework for collecting, processing, and exporting telemetry data from your applications. It also includes information on how to use the OTLP Log Parser to parse and refine trace data generated by OpenTelemetry.

## **OpenTelemetry Overview**
OpenTelemetry is an open-source project that provides a set of APIs, libraries, agents, and instrumentation to enable observability in modern applications. It is designed to help developers and system operators to capture, generate, and export telemetry data, such as traces, metrics, and logs, from their applications and infrastructure. By collecting and analyzing telemetry data, developers can gain insights into the performance, behavior, and issues within their distributed systems.

---

### **Key Components of OpenTelemetry**:
1. **Tracing**: OpenTelemetry's tracing component allows you to capture and visualize the flow of requests through your application. It generates traces, which are representations of the distributed execution of operations. Traces consist of spans, representing individual operations or actions, and they provide valuable information about the timing and dependencies of different components.

2. **Metrics**: OpenTelemetry's metrics component enables you to collect and analyze various performance metrics from your application, such as CPU usage, memory consumption, and request rates. Metrics provide a high-level view of the health and efficiency of your application.

3. **Logging**: OpenTelemetry supports logging and can be used to capture log data from your application. Logs can help you understand the internal state of your application, track errors, and identify potential issues.

4. **Distributed Context Propagation**: OpenTelemetry provides context propagation mechanisms that allow you to pass trace and span context across service boundaries. This ensures that requests across microservices are correlated, allowing you to trace the complete flow of a request.

5. **Exporters**: OpenTelemetry supports various exporters to send telemetry data to different monitoring and observability systems, such as Jaeger, Prometheus, Zipkin, and others. This flexibility enables you to integrate OpenTelemetry with your preferred monitoring tools.

---

## **Running OpenTelemetry**
### **Method 1: Using OpenTelemetry Java Agent**

To run your Java application with OpenTelemetry and collect telemetry data using the OpenTelemetry Java agent, follow these steps:

1. Download the OpenTelemetry Java jar file from the official website: https://opentelemetry.io/docs/instrumentation/java/automatic/
2. Place the downloaded jar file inside your working directory.

3. Open your command line interface.

4. Execute the following command, replacing **`path/to/opentelemetry-javaagent.jar`** with the actual path to the OpenTelemetry Java agent jar file, and **`your-service-name`** with the desired name for your service:

```shell
java -javaagent:path/to/opentelemetry-javaagent.jar -Dotel.service.name=your-service-name --Dotel.traces.exporter=logging-otlp -Dotel.metrics.exporter=none -jar myapp.jar
```
This command starts your application **`myapp.jar`** with the OpenTelemetry Java agent, configures the service name, enables the logging-otlp exporter for exporting traces, and disables metrics export.

If you want to log the output into a text file named **`traces.txt`**, append **`2> traces.txt`** to the command:

```shell
java -javaagent:path/to/opentelemetry-javaagent.jar -Dotel.service.name=your-service-name --Dotel.traces.exporter=logging-otlp -Dotel.metrics.exporter=none -jar myapp.jar 2> traces.txt
```
Now, the trace data will be logged to **`traces.txt`** in your working directory.

---

### **Method 2: Using Docker and Docker Compose**
To collect trace data using Docker and Docker Compose without manually installing OpenTelemetry, follow these steps:

1. Create a **`Dockerfile`** in each microservice's directory with the following content:

```shell
FROM openjdk:17-jdk-slim
WORKDIR /app
COPY /target/*.jar main.jar
ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar .
ENV JAVA_TOOL_OPTIONS "-javaagent:./opentelemetry-javaagent.jar"
CMD ["java", "-jar", "main.jar"]
```

The **`ADD`** command will download the latest OpenTelemetry Java agent JAR file from the specified URL and adds it to the Docker container.
The **`ENV`** command sets the `JAVA_TOOL_OPTIONS` environment variable inside the Docker container, specifying the Java agent JAR file to be used for OpenTelemetry instrumentation.

2. In your **`docker-compose.yml`** file, add the environment variables for each microservice:
```shell
services:
  microservice1:
    build:
      context: ./microservice1
      dockerfile: Dockerfile
    environment:
      - OTEL_SERVICE_NAME=your-service-name
      - OTEL_TRACES_EXPORTER=logging-otlp
      - OTEL_METRICS_EXPORTER=none
  microservice2:
    build:
      context: ./microservice2
      dockerfile: Dockerfile
    environment:
      - OTEL_SERVICE_NAME=your-service-name
      - OTEL_TRACES_EXPORTER=logging-otlp
      - OTEL_METRICS_EXPORTER=none
  # Define more services...
```

Replace **`your-service-name`** with desired name of your services.

3. Run the following command to start the Docker containers and collect trace data:

```shell
docker-compose up
```
By running docker-compose up, The containers run the commands defined in the Dockerfile, which include executing the Java application with the OpenTelemetry Java agent and the specified configuration and collect the trace data without manually installing the OpenTelemetry Java agent.

The trace data will be logged to the standard output (stdout).

4. If you want to log the output into a text file named **`traces.txt`**, append **`2> traces.txt`** to the command:

```shell
docker-compose up 2> traces.txt
```

Now, the trace data will be logged to **`traces.txt`** in your docker-compose directory.

---

## **Parsing and Refining Trace Data**
To parse and refine the trace data logged by OpenTelemetry, you can use the **`otlpLogParser.py`** Python script available at https://github.com/viraj0704/OpenTelemetryLogParser. This script converts the log file into a JSON representation of the trace data.

### OTLP Log Parser Overview
The OTLP Log Parser (**`otlpLogParser.py`**) is a Python script designed to parse and refine the trace data logged by OpenTelemetry when using the **`logging-otlp`** exporter. The primary purpose of this parser is to convert the log output from OpenTelemetry into a more structured and human-readable format, such as JSON, to facilitate further analysis and visualization.

### **Key Features of OTLP Log Parser**:
1. **Parsing Logs**: The parser reads the log file generated by OpenTelemetry, which contains trace and span information in OTLP JSON format.

2. **JSON Output**: The parser converts the log data into JSON format, with each trace represented as a separate JSON file. Each JSON file contains information about spans, including their start time, duration, and any associated metadata.

3. **Trace Aggregation**: When multiple microservices have spans with the same trace ID, the parser aggregates them into a single JSON file. To distinguish between spans of different microservices, the parser assigns process IDs (p1, p2, and so on) to each microservice.

4. **Process Descriptions**: The parser includes descriptions of each microservice's process in the processes object of the JSON file, providing additional context for analysis.

5. **Error Logs**: The parser identifies and displays error logs, making it easier to spot potential issues and troubleshoot problems.

6. **Sorting Spans**: The parser sorts spans based on their starting time, which can be helpful for visualizing the chronological order of operations.

7. **Selective Processing**: The parser processes only the lines that contain OpenTelemetry log data, allowing for efficient extraction of relevant information. Other log data lines are ignored.

8. **Directory Creation**: The parser creates directories for each service based on the service name. The directory of a specific service name will contain traces which contains spans of that particular directory. It also creates a directory named "All" to store all the traces.

### **Steps to Use the OTLP Log Parser:**

1. Ensure you have Python installed on your system.

2. Download the **`otlpLogParser.py`** script from the above GitHub repository.

3. Open a command line interface and navigate to the directory where the script is located.

4. Execute the following command, replacing **`<path_to_folder>`** with the path to the directory which contains the log file generated by OpenTelemetry:

```shell
python otlpLogParser.py -dir <path_to_folder>
```

OR
Execute the following command, replacing **`<path_to_file>`** with the path to the log file generated by OpenTelemetry:

```shell
python otlpLogParser.py -file <path_to_file>
```


This command will generate a JSON file for each trace, using the trace ID as the name of the file. If multiple microservices have spans with the same trace ID, the script will add those spans to the same JSON file and name each microservice's process ID as **`p1`**, **`p2`**, and so on. The description of each microservice will be provided in the **`processes`** object of the JSON file. 

The **`otlpLogParser.py`** script also displays error logs and sorts the spans based on their starting time. Each service will have it's own directory and it will contain the traces which have spans of this service in them.

Using the OTLP Log Parser, you can convert the raw log output from OpenTelemetry into a more structured format, making it easier to analyze and gain insights into the behavior and performance of your distributed systems. This can be particularly useful during testing, debugging, and monitoring phases of your application's development lifecycle.