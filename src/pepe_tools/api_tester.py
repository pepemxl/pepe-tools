import argparse
import sys
import json
import requests

def execute_api_test(method: str, url: str, headers_list: list, data: str):
    headers = {}
    if headers_list:
        for header in headers_list:
            if ":" in header:
                key, val = header.split(":", 1)
                headers[key.strip()] = val.strip()
            else:
                print(f"Warning: Invalid header format '{header}'. Expected 'Key: Value'")

    try:
        print(f"Sending {method} request to {url}...\n")
        response = requests.request(method, url, headers=headers, data=data)
        
        print("--- Response ---")
        print(f"Status Code: {response.status_code} {response.reason}")
        print(f"Time Elapsed: {response.elapsed.total_seconds()}s")
        print("Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        
        print("\nBody:")
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                parsed_json = response.json()
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print(response.text)
        else:
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}", file=sys.stderr)
        sys.exit(1)
