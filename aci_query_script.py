#!/usr/bin/env python3
"""
ACI API Query Script for Terraform External Data Source
Usage: Called by Terraform external data source with JSON input
"""

import json
import sys
import requests
import urllib3
from urllib.parse import urljoin
import base64
import time

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ACIQueryError(Exception):
    """Custom exception for ACI query errors"""
    pass

def authenticate_aci(apic_url, username, password, timeout=30):
    """
    Authenticate with ACI APIC and return session with token
    """
    session = requests.Session()
    session.verify = False
    session.timeout = timeout
    
    login_url = urljoin(apic_url, "/api/aaaLogin.json")
    login_payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }
    
    try:
        response = session.post(login_url, json=login_payload)
        response.raise_for_status()
        
        login_data = response.json()
        if 'imdata' in login_data and len(login_data['imdata']) > 0:
            token = login_data['imdata'][0].get('aaaLogin', {}).get('attributes', {}).get('token')
            if token:
                # Set token in session headers for future requests
                session.headers.update({'Cookie': f'APIC-cookie={token}'})
                return session
        
        raise ACIQueryError("Authentication failed - no token received")
        
    except requests.exceptions.RequestException as e:
        raise ACIQueryError(f"Authentication request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise ACIQueryError(f"Invalid JSON response during authentication: {str(e)}")

def query_aci_api(session, apic_url, api_path, params=None):
    """
    Query ACI API endpoint and return JSON response
    """
    # Ensure API path starts with /api
    if not api_path.startswith('/api'):
        if api_path.startswith('/'):
            api_path = '/api' + api_path
        else:
            api_path = '/api/' + api_path
    
    query_url = urljoin(apic_url, api_path)
    
    try:
        response = session.get(query_url, params=params)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise ACIQueryError(f"API query failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise ACIQueryError(f"Invalid JSON response from API: {str(e)}")

def main():
    """
    Main function to handle Terraform external data source input/output
    """
    try:
        # Read input from stdin (Terraform external data source)
        input_data = json.loads(sys.stdin.read())
        
        # Required parameters
        required_params = ['apic_url', 'username', 'password', 'api_path']
        for param in required_params:
            if param not in input_data:
                raise ACIQueryError(f"Missing required parameter: {param}")
        
        apic_url = input_data['apic_url'].rstrip('/')
        username = input_data['username']
        password = input_data['password']
        api_path = input_data['api_path']
        
        # Optional parameters
        timeout = int(input_data.get('timeout', 30))
        query_params = input_data.get('query_params', {})
        
        # Authenticate with ACI
        session = authenticate_aci(apic_url, username, password, timeout)
        
        # Query the API
        result = query_aci_api(session, apic_url, api_path, query_params)
        
        # Prepare output for Terraform
        # Terraform external data source expects flat string values
        output = {
            'json_data': json.dumps(result),
            'status': 'success',
            'timestamp': str(int(time.time()))
        }
        
        # Add some metadata
        if 'imdata' in result:
            output['record_count'] = str(len(result['imdata']))
        
        if 'totalCount' in result:
            output['total_count'] = str(result['totalCount'])
        
        # Output JSON for Terraform
        print(json.dumps(output))
        
    except ACIQueryError as e:
        # Output error for Terraform
        error_output = {
            'json_data': '{}',
            'status': 'error',
            'error_message': str(e),
            'timestamp': str(int(time.time()))
        }
        print(json.dumps(error_output))
        sys.exit(1)
        
    except json.JSONDecodeError as e:
        error_output = {
            'json_data': '{}',
            'status': 'error',
            'error_message': f"Invalid input JSON: {str(e)}",
            'timestamp': str(int(time.time()))
        }
        print(json.dumps(error_output))
        sys.exit(1)
        
    except Exception as e:
        error_output = {
            'json_data': '{}',
            'status': 'error',
            'error_message': f"Unexpected error: {str(e)}",
            'timestamp': str(int(time.time()))
        }
        print(json.dumps(error_output))
        sys.exit(1)

if __name__ == "__main__":
    main()
