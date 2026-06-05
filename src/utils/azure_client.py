"""
azure_client.py
Shared helper functions for connecting to Azure services.
All scripts import from here instead of writing their own connection code.
"""

import os
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

load_dotenv()  # Reads values from your .env file into environment variables


def get_adls_client() -> DataLakeServiceClient:
    """
    Create and return a DataLake client using credentials from the .env file.

    In production, replace ClientSecretCredential with DefaultAzureCredential
    so the code uses Managed Identity instead of hardcoded service principal keys.
    For local development, ClientSecretCredential is fine.
    """
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
    account_key = os.getenv("AZURE_STORAGE_KEY")
    account_url = f"https://{account_name}.dfs.core.windows.net"

    return DataLakeServiceClient(account_url=account_url, credential=account_key)


def get_container_client(container_name: str):
    """Return a client for a specific container (bronze, silver, or gold)"""
    client = get_adls_client()
    return client.get_file_system_client(container_name)
