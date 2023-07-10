import os
import json
import argparse
import shutil
import time

def convert_to_json(log_data):
    log_start = log_data.find('{')
    if(log_start == -1 ):
        return (-1,-1)
    log_json = log_data[log_start:]
    
    log_dict = json.loads(log_json)
    

    process_data = log_dict['resource']['attributes']
    process_info = {}
    for attr in process_data:
        attr_key = attr['key']
        attr_value = attr['value']
        if 'intValue' in attr_value:
            value = int(attr_value['intValue'])
            attr_type = 'int64'
        elif 'stringValue' in attr_value:
            value = attr_value['stringValue']
            attr_type = 'string'
        else:
            # Handle other value types if needed
            continue
        process_info[attr_key] = {
            'key': attr_key,
            'type': attr_type,
            'value': value
        }

    # logs_info = log_dict['scopeSpans']
    
    trace_id = log_dict['scopeSpans'][0]['spans'][0]['traceId']
    spans = []

    for scope_span in log_dict['scopeSpans']:
        for span in scope_span['spans']:
            span_data = {
                'traceID': span['traceId'],
                'spanID': span['spanId'],
                'operationName': span['name'],
                'references': [],
                'startTime': int(span['startTimeUnixNano']) // 1000,  # Convert from nanoseconds to microseconds
                'duration': (int(span['endTimeUnixNano']) - int(span['startTimeUnixNano'])) // 1000,  # Convert from nanoseconds to microseconds
                'tags': [],
                'logs':[],
                'processID': 'p1',  # Process ID is set to 'p1' for all spans
                'warnings': None  # Set to None if no warnings available
            }

            if 'parentSpanId' in span:
                span_data['references'].append({
                    'refType': 'CHILD_OF',
                    'traceID': span['traceId'],
                    'spanID': span['parentSpanId']
                })

            if 'attributes' in span:
                for attribute in span['attributes']:
                    attribute_key = attribute['key']
                    attribute_value = attribute['value']

                    if 'intValue' in attribute_value:
                        tag_value = int(attribute_value['intValue'])
                        tag_type = 'int64'
                    elif 'stringValue' in attribute_value:
                        tag_value = attribute_value['stringValue']
                        tag_type = 'string'
                    # Add additional cases for other value types if needed

                    span_data['tags'].append({
                        'key': attribute_key,
                        'type': tag_type,
                        'value': tag_value
                    })

            
            if 'events' in span:
                for event in span['events']:
                    logs_data = {
                        "timestamp" : int(event['timeUnixNano']) // 1000,
                        "fields" :[
                            {
                                "key": "event",
                                "type": "string",
                                "value": event['name']
                            }
                        ]
                    }

                    for attribute in event['attributes']:
                        attribute_key = attribute['key']
                        attribute_value = attribute['value']

                        if 'intValue' in attribute_value:
                            field_value = int(attribute_value['intValue'])
                            field_type = 'int64'
                        elif 'stringValue' in attribute_value:
                            field_value = attribute_value['stringValue']
                            field_type = 'string'
                        # Add additional cases for other value types if needed
                        logs_data['fields'].append({
                            'key': attribute_key,
                            'type': field_type,
                            'value': field_value                            
                        })
                    span_data['logs'].append(logs_data)




            spans.append(span_data)

    json_data = {
        'data': [
            {
                'traceID': trace_id,
                'spans': spans,
                'processes': {
                    'p1': {
                        'serviceName': process_info.get('service.name', {}).get('value', ''),
                        'tags': [
                            {
                                'key': attr_key,
                                'type': process_info[attr_key]['type'],
                                'value': process_info[attr_key]['value']
                            }
                            for attr_key in process_info.keys()
                        ]
                    }
                }
            }
        ],
        
    }

    return (trace_id,json_data)

def load_json_file(file_name):
    with open(file_name, 'r') as file:
        json_data = json.load(file)
    return json_data

def save_json_file(json_data, file_name):
    with open(file_name, 'w') as file:
        json.dump(json_data, file, indent=4)

def process_log_data(file_name):
    prev_data = ""
    prev_skip = ""
    complete = True
    services_traceId = {}
    with open(file_name, 'r') as file:
        for log_data in file:
            # log_data = file.readline()
            log_check1 = log_data.find("otel.javaagent")
            log_check2 = log_data.find("schemaUrl")
            flag = 0
            if(log_check1 != -1 and log_check2 != -1):
                pass
            elif(log_check1 == -1 and log_check2 == -1):
                if(complete == False):
                    prev_data += (log_data[len(prev_skip):]).rstrip()
                continue
            elif(log_check1 != -1 and log_check2 == -1):
                complete = False
                prev_data = (log_data[log_check1-1:]).rstrip()
                prev_skip = log_data[:log_check1-1]
                continue
            else:
                curr_data = log_data[len(prev_skip):]
                log_data = prev_data + curr_data

            trace_id, log_dict = convert_to_json(log_data)
            if(trace_id == -1):
                continue
            # print(trace_id)
            # print(log_dict)
            file_name = f"{trace_id}.json"
            file_name = "All/" + file_name
            
            if os.path.isfile(file_name):
                # JSON file with the same name exists, update it
                json_data = load_json_file(file_name)

                
                # Find the last processID and increment it
                process_ids = list(json_data['data'][0]['processes'].keys())
                last_process_id = process_ids[-1] if process_ids else 'p0'
                flag = False
                for process_id in process_ids:
                    if json_data['data'][0]['processes'][process_id]['serviceName'] == log_dict['data'][0]['processes']['p1']['serviceName'] :
                        flag = True
                        break
                
                service_name = log_dict['data'][0]['processes']['p1']['serviceName']
                if service_name not in services_traceId.keys():
                    services_traceId[service_name] = [trace_id]
                else:
                    services_traceId[service_name].append(f"{trace_id}")
                if (flag == False):

                    new_process_id = 'p' + str(int(last_process_id[1:]) + 1)

                    # Add span data with new processID
                    spans = log_dict['data'][0]['spans']
                    # print(spans)
                    for span_data in spans:
                        span_data['processID'] = new_process_id

                    json_data['data'][0]['spans'].extend(spans)

                    # Extract process info from log_data
                    process_info = log_dict['data'][0]['processes']['p1']

                    # Add process_info to the process
                    json_data['data'][0]['processes'][new_process_id] = process_info

                    # Save the updated JSON file
                    json_data['data'][0]['spans'] = sorted(json_data['data'][0]['spans'], key=lambda x: x['startTime'])
                    save_json_file(json_data, file_name)
                
            else:
                # JSON file doesn't exist, create a new one
                service_name = log_dict['data'][0]['processes']['p1']['serviceName']
                if service_name not in services_traceId.keys():
                    services_traceId[service_name] = [trace_id]
                else:
                    services_traceId[service_name].append(f"{trace_id}")
                spans = log_dict['data'][0]['spans']
                
                json_data = {
                    'data': [
                        {
                            'traceID': trace_id,
                            'spans': spans,
                            'processes': {
                                'p1': log_dict['data'][0]['processes']['p1']
                            }
                        }
                    ],
                    
                }
                json_data['data'][0]['spans'] = sorted(json_data['data'][0]['spans'], key=lambda x: x['startTime'])
                # Save the JSON file
                save_json_file(json_data, file_name)
    
        return services_traceId
            
        
        

if __name__ == '__main__':
    # log_data = '[otel.javaagent 2023-07-03 16:29:47:222 +0530] [BatchSpanProcessor_WorkerThread-1] INFO io.opentelemetry.exporter.logging.otlp.OtlpJsonLoggingSpanExporter - {"resource":{"attributes":[{"key":"host.arch","value":{"stringValue":"x86_64"}},{"key":"host.name","value":{"stringValue":"viraj.goyanka-C02CPU2QMD6M"}},{"key":"os.description","value":{"stringValue":"Mac OS X 12.6.4"}},{"key":"os.type","value":{"stringValue":"darwin"}},{"key":"process.command_args","value":{"arrayValue":{"values":[{"stringValue":"/Library/Java/JavaVirtualMachines/jdk-20.jdk/Contents/Home/bin/java"},{"stringValue":"-javaagent:../opentelemetry-javaagent.jar"},{"stringValue":"-Dotel.service.name=ms-one"},{"stringValue":"-Dotel.traces.exporter=logging-otlp"},{"stringValue":"-Dotel.metrics.exporter=none"},{"stringValue":"-jar"},{"stringValue":"target/ms-one-0.0.1-SNAPSHOT.jar"}]}}},{"key":"process.executable.path","value":{"stringValue":"/Library/Java/JavaVirtualMachines/jdk-20.jdk/Contents/Home/bin/java"}},{"key":"process.pid","value":{"intValue":"9780"}},{"key":"process.runtime.description","value":{"stringValue":"Oracle Corporation Java HotSpot(TM) 64-Bit Server VM 20.0.1+9-29"}},{"key":"process.runtime.name","value":{"stringValue":"Java(TM) SE Runtime Environment"}},{"key":"process.runtime.version","value":{"stringValue":"20.0.1+9-29"}},{"key":"service.name","value":{"stringValue":"ms-one"}},{"key":"telemetry.auto.version","value":{"stringValue":"1.26.0"}},{"key":"telemetry.sdk.language","value":{"stringValue":"java"}},{"key":"telemetry.sdk.name","value":{"stringValue":"opentelemetry"}},{"key":"telemetry.sdk.version","value":{"stringValue":"1.26.0"}}]},"scopeSpans":[{"scope":{"name":"io.opentelemetry.http-url-connection","version":"1.26.0-alpha","attributes":[]},"spans":[{"traceId":"c9815fed398a628696d0c2fed056db03","spanId":"895f83f2a840e4cf","parentSpanId":"8b46a20c416cd2b4","name":"GET","kind":3,"startTimeUnixNano":"1688381984681440156","endTimeUnixNano":"1688381984961836245","attributes":[{"key":"http.status_code","value":{"intValue":"200"}},{"key":"net.peer.name","value":{"stringValue":"localhost"}},{"key":"net.peer.port","value":{"intValue":"8081"}},{"key":"http.response_content_length","value":{"intValue":"13"}},{"key":"net.protocol.version","value":{"stringValue":"1.1"}},{"key":"http.method","value":{"stringValue":"GET"}},{"key":"thread.name","value":{"stringValue":"http-nio-8080-exec-1"}},{"key":"thread.id","value":{"intValue":"44"}},{"key":"net.protocol.name","value":{"stringValue":"http"}},{"key":"http.url","value":{"stringValue":"http://localhost:8081/"}}],"events":[],"links":[],"status":{}}]},{"scope":{"name":"io.opentelemetry.tomcat-10.0","version":"1.26.0-alpha","attributes":[]},"spans":[{"traceId":"c9815fed398a628696d0c2fed056db03","spanId":"4b2aeee6ae0f16f8","name":"GET /customer","kind":2,"startTimeUnixNano":"1688381984505297000","endTimeUnixNano":"1688381984990068750","attributes":[{"key":"http.target","value":{"stringValue":"/customer"}},{"key":"net.sock.peer.addr","value":{"stringValue":"0:0:0:0:0:0:0:1"}},{"key":"user_agent.original","value":{"stringValue":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}},{"key":"net.host.name","value":{"stringValue":"localhost"}},{"key":"thread.name","value":{"stringValue":"http-nio-8080-exec-1"}},{"key":"http.route","value":{"stringValue":"/customer"}},{"key":"http.status_code","value":{"intValue":"200"}},{"key":"net.sock.host.addr","value":{"stringValue":"0:0:0:0:0:0:0:1"}},{"key":"net.host.port","value":{"intValue":"8080"}},{"key":"http.response_content_length","value":{"intValue":"13"}},{"key":"net.protocol.version","value":{"stringValue":"1.1"}},{"key":"http.scheme","value":{"stringValue":"http"}},{"key":"http.method","value":{"stringValue":"GET"}},{"key":"net.protocol.name","value":{"stringValue":"http"}},{"key":"thread.id","value":{"intValue":"44"}},{"key":"net.sock.peer.port","value":{"intValue":"56021"}}],"events":[],"links":[],"status":{}}]},{"scope":{"name":"io.opentelemetry.spring-webmvc-6.0","version":"1.26.0-alpha","attributes":[]},"spans":[{"traceId":"c9815fed398a628696d0c2fed056db03","spanId":"8b46a20c416cd2b4","parentSpanId":"4b2aeee6ae0f16f8","name":"MsOneController.get","kind":1,"startTimeUnixNano":"1688381984607309806","endTimeUnixNano":"1688381984988796825","attributes":[{"key":"thread.name","value":{"stringValue":"http-nio-8080-exec-1"}},{"key":"thread.id","value":{"intValue":"44"}}],"events":[],"links":[],"status":{}}]}],"schemaUrl":"https://opentelemetry.io/schemas/1.19.0"}'
    # log_data_2 = '[otel.javaagent 2023-07-03 16:29:49:878 +0530] [BatchSpanProcessor_WorkerThread-1] INFO io.opentelemetry.exporter.logging.otlp.OtlpJsonLoggingSpanExporter - {"resource":{"attributes":[{"key":"host.arch","value":{"stringValue":"x86_64"}},{"key":"host.name","value":{"stringValue":"viraj.goyanka-C02CPU2QMD6M"}},{"key":"os.description","value":{"stringValue":"Mac OS X 12.6.4"}},{"key":"os.type","value":{"stringValue":"darwin"}},{"key":"process.command_args","value":{"arrayValue":{"values":[{"stringValue":"/Library/Java/JavaVirtualMachines/jdk-20.jdk/Contents/Home/bin/java"},{"stringValue":"-javaagent:../opentelemetry-javaagent.jar"},{"stringValue":"-Dotel.service.name=ms-two"},{"stringValue":"-Dotel.traces.exporter=logging-otlp"},{"stringValue":"-Dotel.metrics.exporter=none"},{"stringValue":"-jar"},{"stringValue":"target/ms-two-0.0.1-SNAPSHOT.jar"}]}}},{"key":"process.executable.path","value":{"stringValue":"/Library/Java/JavaVirtualMachines/jdk-20.jdk/Contents/Home/bin/java"}},{"key":"process.pid","value":{"intValue":"9784"}},{"key":"process.runtime.description","value":{"stringValue":"Oracle Corporation Java HotSpot(TM) 64-Bit Server VM 20.0.1+9-29"}},{"key":"process.runtime.name","value":{"stringValue":"Java(TM) SE Runtime Environment"}},{"key":"process.runtime.version","value":{"stringValue":"20.0.1+9-29"}},{"key":"service.name","value":{"stringValue":"ms-two"}},{"key":"telemetry.auto.version","value":{"stringValue":"1.26.0"}},{"key":"telemetry.sdk.language","value":{"stringValue":"java"}},{"key":"telemetry.sdk.name","value":{"stringValue":"opentelemetry"}},{"key":"telemetry.sdk.version","value":{"stringValue":"1.26.0"}}]},"scopeSpans":[{"scope":{"name":"io.opentelemetry.tomcat-10.0","version":"1.26.0-alpha","attributes":[]},"spans":[{"traceId":"c9815fed398a628696d0c2fed056db03","spanId":"96b9af97e4e26e74","parentSpanId":"895f83f2a840e4cf","name":"GET /","kind":2,"startTimeUnixNano":"1688381984807272000","endTimeUnixNano":"1688381984960474507","attributes":[{"key":"http.target","value":{"stringValue":"/"}},{"key":"net.sock.peer.addr","value":{"stringValue":"127.0.0.1"}},{"key":"user_agent.original","value":{"stringValue":"Java/20.0.1"}},{"key":"net.host.name","value":{"stringValue":"localhost"}},{"key":"thread.name","value":{"stringValue":"http-nio-8081-exec-1"}},{"key":"http.route","value":{"stringValue":"/"}},{"key":"http.status_code","value":{"intValue":"200"}},{"key":"net.sock.host.addr","value":{"stringValue":"127.0.0.1"}},{"key":"net.host.port","value":{"intValue":"8081"}},{"key":"http.response_content_length","value":{"intValue":"13"}},{"key":"net.protocol.version","value":{"stringValue":"1.1"}},{"key":"http.scheme","value":{"stringValue":"http"}},{"key":"http.method","value":{"stringValue":"GET"}},{"key":"net.protocol.name","value":{"stringValue":"http"}},{"key":"thread.id","value":{"intValue":"41"}},{"key":"net.sock.peer.port","value":{"intValue":"56022"}}],"events":[],"links":[],"status":{}}]},{"scope":{"name":"io.opentelemetry.spring-webmvc-6.0","version":"1.26.0-alpha","attributes":[]},"spans":[{"traceId":"c9815fed398a628696d0c2fed056db03","spanId":"83b88f8bad86831b","parentSpanId":"96b9af97e4e26e74","name":"MsTwoController.get","kind":1,"startTimeUnixNano":"1688381984916218360","endTimeUnixNano":"1688381984959221885","attributes":[{"key":"thread.name","value":{"stringValue":"http-nio-8081-exec-1"}},{"key":"thread.id","value":{"intValue":"41"}}],"events":[],"links":[],"status":{}}]}],"schemaUrl":"https://opentelemetry.io/schemas/1.19.0"}'
    parser = argparse.ArgumentParser(description='OpenTelemetry Log Parser')

    # Add the file path argument
    parser.add_argument('file', help='Path to the log file')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Get the file path from the arguments
    dir_path = args.file

    service_dict = {}
    if(os.path.isdir("All") == False):
        os.mkdir('All')

    for f in os.listdir("All"):
        os.remove(os.path.join("All", f))

    with open("maps.txt","w") as f:
        f.close()

    for file_name in os.listdir(dir_path):
        if file_name.endswith('.txt') or file_name.endswith('.log'):
            file_path = os.path.join(dir_path,file_name)
            # print(file_name)
            service_traceId = process_log_data(file_path)
            with open("maps.txt","a") as f:
                for key, value in service_traceId.items():
                    service_dict[key] = value
                    # print(f"---{key}---")
                    f.write(f'{key} -> {value}\n')
            f.close()

    for key, values in service_dict.items():
        if(os.path.isdir(key)):
                for f in os.listdir(key):
                    os.remove(os.path.join(key, f))
        else:
            os.mkdir(key)
        for value in values:
            shutil.copy2(f"All/{value}.json",f"{key}/")
