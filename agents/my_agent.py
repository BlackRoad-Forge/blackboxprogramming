"""
Client for interacting with an additional API using a secondary API key.

This module reads the ``MY_API_KEY`` environment variable and exposes a
``call_my_service`` function to send GET requests to an API endpoint. The
headers include the key for bearer authentication. This can be extended to
support other HTTP methods or query parameter handling as needed.

Example usage::

    from agents.my_agent import call_my_service
    result = call_my_service("https://example.com/api/status", params={"id": 42})
    print(result)

"""
import os
import requests
from typing import Any, Dict, Optional

# Secondary API key for authentication.
MY_API_KEY: Optional[str] = os.getenv("MY_API_KEY")


def call_my_service(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send a GET request to the given endpoint using the configured API key.

    :param endpoint: The full URL of the API endpoint to call.
    :param params: Optional dictionary of query parameters.
    :returns: The JSON response parsed into a dictionary.
    :raises RuntimeError: If the ``MY_API_KEY`` environment variable is not set.
    :raises requests.HTTPError: If the HTTP request fails.
    """
    if not MY_API_KEY:
        raise RuntimeError(
            "MY_API_KEY environment variable is not set. "
            "Please configure your API key in the .env file or environment."
        )

    headers = {
        "Authorization": f"Bearer {MY_API_KEY}",
    }

    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
