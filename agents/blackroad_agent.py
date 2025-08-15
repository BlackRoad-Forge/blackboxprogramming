"""
Client for interacting with the Blackroad coding portal.

This module reads the ``BLACKROAD_HOST`` and ``BLACKROAD_HOST_FINGERPRINT`` environment variables and exposes functions to call the portal's API. The fingerprint variable is provided for informational purposes; SSL/SSH verification is out of scope for this simple HTTP client.
"""

import os
from typing import Any, Dict, Optional
import requests

# Retrieve host and fingerprint from environment variables
BLACKROAD_HOST: Optional[str] = os.getenv("BLACKROAD_HOST")
BLACKROAD_HOST_FINGERPRINT: Optional[str] = os.getenv("BLACKROAD_HOST_FINGERPRINT")


def call_blackroad_api(path: str, params: Optional[Dict[str, Any]] = None, method: str = "GET") -> Dict[str, Any]:
    """
    Send a request to the Blackroad coding portal API using the given HTTP method.

    :param path: Endpoint path, starting with a slash.
    :param params: Optional parameters to include in the request. For GET requests, these are used as query parameters; for POST requests, they are sent as JSON.
    :param method: HTTP method, either "GET" or "POST".
    :returns: The JSON response parsed into a Python dictionary.
    :raises RuntimeError: If the ``BLACKROAD_HOST`` environment variable is not set.
    :raises requests.HTTPError: If the HTTP request fails.
    """
    if not BLACKROAD_HOST:
        raise RuntimeError("BLACKROAD_HOST environment variable is not set.")

    # Construct the full URL using the host and path
    url = f"http://{BLACKROAD_HOST}{path}"

    # Perform the HTTP request based on the method
    if method.upper() == "GET":
        response = requests.get(url, params=params, timeout=30)
    else:
        response = requests.post(url, json=params, timeout=30)

    # Raise an exception if the response status is not successful
    response.raise_for_status()

    # Return the parsed JSON response
    return response.json()
