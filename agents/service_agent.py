"""
Client for interacting with a generic service using a service account secret.

This module reads the ``SERVICE_API_KEY`` environment variable and exposes a
``call_service`` function to perform authenticated POST requests to arbitrary
service endpoints. It can be adapted to integrate with any HTTP-based API
that uses bearer token authentication.

Example usage::

    from agents.service_agent import call_service
    response = call_service(
        endpoint="https://example.com/api/v1/process", data={"task": "ping"}
    )
    print(response)

"""
import os
import requests
from typing import Any, Dict, Optional

# Service API key retrieved from the environment. Required for authentication.
SERVICE_API_KEY: Optional[str] = os.getenv("SERVICE_API_KEY")


def call_service(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a POST request to the specified service endpoint.

    :param endpoint: The full URL of the API endpoint to call.
    :param data: A JSON-serializable dictionary to send in the request body.
    :returns: The JSON response parsed into a dictionary.
    :raises RuntimeError: If the ``SERVICE_API_KEY`` environment variable is not set.
    :raises requests.HTTPError: If the HTTP request fails.
    """
    if not SERVICE_API_KEY:
        raise RuntimeError(
            "SERVICE_API_KEY environment variable is not set. "
            "Please configure your service API key in the .env file or environment."
        )

    headers = {
        "Authorization": f"Bearer {SERVICE_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(endpoint, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
