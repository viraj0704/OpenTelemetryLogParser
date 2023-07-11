import os
import json
import argparse
import shutil
import time

def load_json_file(file_name):
    with open(file_name, 'r') as file:
        json_data = json.load(file)
    return json_data

def save_json_file(json_data, file_name):
    with open(file_name, 'w') as file:
        json.dump(json_data, file, indent=4)

def getProcessInfo(process_data):
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
    return process_info

def getScopeData(scope_span):
    scope_data = [
        {
            'key': "otel.scope.name",
            'type': "string",
            'value': scope_span['scope']['name']
        },
        {
            'key': "otel.library.name",
            'type': "string",
            'value': scope_span['scope']['name']
        },
        {
            'key': "otel.scope.version",
            'type': "string",
            'value': scope_span['scope']['version']
        },
        {
            'key': "otel.library.version",
            'type': "string",
            'value': scope_span['scope']['version']
        }
    ]
    return scope_data

def setReferences(span,span_data):
    if 'parentSpanId' in span:
        span_data['references'].append({
            'refType': 'CHILD_OF',
            'traceID': span['traceId'],
            'spanID': span['parentSpanId']
        })
    return span_data

def setTags(span,span_data):
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
    return span_data

def setLogsData(span,span_data):
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
    
    return span_data

def getTraceData(trace_id,spans,process_info):
    trace_data = {
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
    return trace_data


def convert_to_json(log_data):
    log_start = log_data.find('{')
    if(log_start == -1 ):
        return {-1:""}
    log_json = log_data[log_start:]
    
    log_dict = json.loads(log_json)
    

    process_data = log_dict['resource']['attributes']
    process_info = getProcessInfo(process_data)
    
    trace_ids = {}

    for scope_span in log_dict['scopeSpans']:
        scope_data = getScopeData(scope_span)
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
            span_data = setReferences(span,span_data)
            span_data = setTags(span,span_data)
            span_data['tags'].extend(scope_data)
            span_data = setLogsData(span,span_data)
            if span['traceId'] in trace_ids:
                trace_ids[span['traceId']].append(span_data)
            else:
                trace_ids[span['traceId']] = [span_data]

    trace_id_data = {}
    for trace_id,spans in trace_ids.items():
        trace_data = getTraceData(trace_id,spans,process_info)
        trace_id_data[trace_id] = trace_data

    return trace_id_data

def checkData(log_data,prev_data,prev_skip,complete):
    passFlag = True
    # Check if it openTelemetry Data
    log_check1 = log_data.find("otel.javaagent")
    log_check2 = log_data.find("schemaUrl")
    if(log_check1 != -1 and log_check2 != -1):
        passFlag = True
    elif(log_check1 == -1 and log_check2 == -1):
        if(complete == False):
            prev_data += (log_data[len(prev_skip):]).rstrip()
        passFlag = False
    elif(log_check1 != -1 and log_check2 == -1):
        complete = False
        prev_data = (log_data[log_check1-1:]).rstrip()
        prev_skip = log_data[:log_check1-1]
        passFlag = False
    else:
        curr_data = log_data[len(prev_skip):]
        log_data = prev_data + curr_data
        passFlag = True

    return (log_data,prev_data,prev_skip,complete,passFlag)


def processLogData(log_data,services_traceId):
    trace_id_json_data = convert_to_json(log_data)
    for trace_id,log_dict in trace_id_json_data.items():
        if(trace_id == -1):
            continue

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
            json_data = log_dict
            json_data['data'][0]['spans'] = sorted(json_data['data'][0]['spans'], key=lambda x: x['startTime'])
            # Save the JSON file
            save_json_file(json_data, file_name)

        service_name = log_dict['data'][0]['processes']['p1']['serviceName']
        if service_name not in services_traceId.keys():
            services_traceId[service_name] = [trace_id]
        else:
            services_traceId[service_name].append(f"{trace_id}")
    
    return services_traceId

def processLogFile(file_name):
    prev_data = ""
    prev_skip = ""
    complete = True
    services_traceId = {}
    with open(file_name, 'r') as file:
        for log_data in file:
            (log_data,prev_data,prev_skip,complete,passFlag) = checkData(log_data,prev_data,prev_skip,complete)
            
            if passFlag == False:
                continue
            services_traceId = processLogData(log_data,services_traceId)

        return services_traceId
            
def setup():
    if(os.path.isdir("All") == False):
        os.mkdir('All')

    for f in os.listdir("All"):
        os.remove(os.path.join("All", f))

    with open("maps.txt","w") as f:
        f.close()

def addTracesToDirectory(service_dict):
    for key, values in service_dict.items():
        if(os.path.isdir(key)):
                for f in os.listdir(key):
                    os.remove(os.path.join(key, f))
        else:
            os.mkdir(key)
        for value in values:
            shutil.copy2(f"All/{value}.json",f"{key}/")

def processLogDirectory(dir_path):
    service_dict = {}
    for file_name in os.listdir(dir_path):
        if file_name.endswith('.txt') or file_name.endswith('.log'):
            file_path = os.path.join(dir_path,file_name)
            service_traceId = processLogFile(file_path)
            with open("maps.txt","a") as f:
                for key, value in service_traceId.items():
                    service_dict[key] = value
                    # print(f"---{key}---")
                    f.write(f'{key} -> {value}\n')
            f.close()
    return service_dict
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenTelemetry Log Parser')

    # Add the file path argument
    parser.add_argument('-file', help='Path to the log file')
    parser.add_argument('-dir', help='Path to the Directory containing log file')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Get the file path from the arguments
    file_path = args.file
    dir_path = args.dir

    setup()

    if dir_path != None :
        service_dict = processLogDirectory(dir_path)
    else:
        service_dict = processLogFile(file_path)
    addTracesToDirectory(service_dict)
