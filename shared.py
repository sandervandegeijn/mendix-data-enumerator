from playwright.sync_api import sync_playwright, Playwright
import pandas as pd
import re
import os
import requests
import json

def validate_url(url):
    # Regex for HTTP/HTTPS URL validation
    regex = re.compile(
        r'^(https?://)' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def get_database_tables(page):
    database_tables_raw = page.evaluate('() => mx.meta.getMap();')
    database_tables = []
    for key in database_tables_raw.keys():
        database_tables.append(key)
    return pd.DataFrame(database_tables, columns=["Database tables"])

def get_dataframe_for_table(page, table_name):
    js_code = """
            (inputvar) => {
                return new Promise((resolve) => {
                    function returndata(data){
                        resolve(data);
                    }
                    function returnerror(error){
                        resolve("");
                    }
                    mx.data.get({
                        xpath: "//"+inputvar,
                        filter: { offset: 0, amount: 10 },
                        callback: function(data) {
                            returndata(data);
                        },
                        error: function(error){
                            returnerror(error);
                        }
                    });
                });
            }
            """
    data = page.evaluate(js_code, table_name)
    if len(data)!=0:
        datakey = None
        if "jsonData" in data[0]:
            datakey = "jsonData"
        elif "_jsonData" in data[0]:
            datakey = "_jsonData"
        else:
            return None

        if len(data[0][datakey]['attributes'])!=0:
            extracted_data = []
            for item in data:
                json_data = item[datakey]['attributes']
                row = {key: value['value'] for key, value in json_data.items()}
                extracted_data.append(row)

            df = pd.DataFrame(extracted_data)
            return df
    return None

def add_download_column(fileID: str, table:str, url:str, page) -> str:
    js_code = """
        (input) => {
            return new Promise((resolve, reject) => {
                const xpath = "//" + input.table + "[FileID=" + input.fileId + "]";
                mx.data.get({
                    xpath: xpath,
                    callback: function(objects) {
                        if (objects && objects.length > 0) {
                            const fileDocument = objects[0];
                            const guid = fileDocument.jsonData.guid;
                            resolve(guid);
                        } else {
                            reject("No FileDocument found with the given FileID.");
                        }
                    },
                    error: function(error) {
                        reject("An error occurred while retrieving the FileDocument: " + error.message);
                    }
                });
            });
        }
        """

    input_param = {
        "fileId": fileID,
        "table": table
    }
    guid = page.evaluate(js_code, input_param)
    return f"{url}/file?guid={guid}"

def judge_data(database_name, df):
    api_endpoint = "http://localhost:11434/api/chat"
    headers = {'Content-Type': 'application/json'}

    example = """
        {
            "sensitivity_score": 8,
            "highest_category_score": 9,
            "average_category_score": 8,
            "explanation": "The document contains highly sensitive personal and financial information.",
            "examples" : "Examples that explain the scores",
            "personal_information_score": 9,
            "financial_information_score": 9,
            "health_information_score": 7,
            "authentication_information_score": 8,
            "other_sensitive_information_score": 0
        }

        """
    
    prompt = f"""
        You are a security expert tasked with assessing structured JSON data scraped from public APIs to determine if there is any sensitive information present. Your goal is to identify potential sensitive data and provide a sensitivity score.

        Sensitive information includes:
        - Personal Identifiable Information (PII): names, addresses, phone numbers, email addresses, social security numbers, etc. Take into account that things like social security numbers are more senstive than i.e. emailaddresses
        - Financial Data: credit card numbers, bank account details, transaction records, etc.
        - Health Records: medical history, prescriptions, health insurance details, etc.
        - Authentication Details: passwords, PINs, secret questions and answers, etc.
        - Other sensitive data: Any other information that could be considered confidential or proprietary.

        Use the following scoring system to rate the sensitivity of the data:
        - 0: No sensitive data
        - 1-3: Low sensitivity data
        - 4-6: Moderate sensitivity data
        - 7-9: High sensitivity data
        - 10: Extremely sensitive data

        Follow these steps to assess the JSON data:
        1. Parse the JSON data and list all key-value pairs.
        2. For each key-value pair, check if the value contains sensitive information as defined above.
        3. Assign a sensitivity score to each key-value pair based on the content.
        4. Calculate the overall sensitivity score for the entire dataset by averaging the scores of individual key-value pairs.
        5. Provide a brief explanation for the overall score.


        The data is structured in database tables that are formatted as pandas dataframes. The data is below:

        =======DATA==========
        """
    
    prompt += f"\nDatabase name: {database_name}"
    prompt += f"\nData:\n\n"
    prompt += df.to_json(orient="records")
    
    prompt += """


        =======END OF DATA==========
        Expected output will be a json object. Do not return anything other than the json object The JSON object should contain:

        {
            "sensitivity_score": INTEGER,
            "highest_category_score": INTEGER,
            "average_category_score": INTEGER,
            "explanation": "EXPLANATION",
            "examples": "EXAMPLES OF DATA THAT EXPLAIN THE SCORES",
            "personal_information_score": INTEGER,
            "financial_information_score": INTEGER,
            "health_information_score": INTEGER,
            "authentication_information_score": INTEGER,
            "other_sensitive_information_score": INTEGER
        }
        if the scores can't be calculated, return 0. It must be an integer. If the result of the calculation is "n/a" return integer 0.

        Output only a VALID json object that can be parsed directly by the json.loads() library in python. I will take your answer and parse it with a json parser directly, so don't wrap the result in text.

        Here is an example of the expected JSON output:
     """
    prompt += example
    payload = {
        "model": "phi3:medium",
        #"model" : "llama3:8b",
        "stream" : False,
        "messages": [
            {
            "role": "user",
            "content": prompt
            }
        ]
        }
    print("Sending input to LLM")
    response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload))
    if response.status_code == requests.codes.ok:
        try:
            content = response.json()["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content)
        except ValueError as e:
            print("Initial response was not valid JSON. Requesting correction.")
            # Prepare follow-up prompt
            follow_up_prompt = f"Your previous response was not valid JSON. Please correct it and provide a valid JSON output as per the initial request with ONLY the json document, nothing more. The error from Python json.loads() was {e.with_traceback} \n\nThe output must be: \n {example}"
            payload["messages"].append({
                "role": "assistant",
                "content": response.json()["message"]["content"].strip()
            })
            payload["messages"].append({
                "role": "user",
                "content": follow_up_prompt
            })
            
            # Resend request with follow-up
            follow_up_response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload))
            if follow_up_response.status_code == requests.codes.ok:
                try:
                    content = follow_up_response.json()["message"]["content"].strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    return json.loads(content)
                except ValueError:
                    print("Follow-up response was also not valid JSON.")
                    print(follow_up_response.json()["message"]["content"])
                    return None
            else:
                print(f"Follow-up response code not 200, {follow_up_response.status_code} body {follow_up_response.text}")
        return None
    else:
        print(f"Response code not 200, {response.status_code} body {response.text}")
    return None

def calculate_scores(data):
    highest_score = float('-inf')
    total_average_score = 0
    count = 0
    
    for db_name, scores in data.items():
        if scores is not None:
            if scores.get("highest_category_score", float('-inf')) > highest_score:
                highest_score = scores["highest_category_score"]
            # Ensure average_category_score is not None
            total_average_score += scores.get("average_category_score") or 0
            count += 1
    
    average_of_average_score = total_average_score / count if count > 0 else 0
    
    return {
        "max": highest_score,
        "avg": average_of_average_score
    }

def write_to_opensearch(data, index_name, opensearch_url, username, password):
    """
    Writes JSON data to OpenSearch with basic authentication.
    
    :param data: The JSON data to be written.
    :param index_name: The name of the OpenSearch index.
    :param opensearch_url: The URL of the OpenSearch instance.
    :param username: The username for basic authentication.
    :param password: The password for basic authentication.
    :return: Response from the OpenSearch API.
    """
    # Create the URL for the index
    url = f"{opensearch_url}/{index_name}/_doc"
    
    # Set up basic authentication
    auth = (username, password)
    
    # Set the headers
    headers = {'Content-Type': 'application/json'}
    
    # Convert the data to JSON
    json_data = json.dumps(data)
    
    # Send the request to OpenSearch
    response = requests.post(url, headers=headers, data=json_data, auth=auth, verify=False)
    
    # Check the response status
    if response.status_code == 201:
        print("Data successfully written to OpenSearch.")
    else:
        print(f"Failed to write data to OpenSearch. Status code: {response.status_code}")
        print("Response:", response.json())
    
    return response