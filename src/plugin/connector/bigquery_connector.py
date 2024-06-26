import logging
import google.oauth2.service_account
import pandas_gbq
from googleapiclient.discovery import build

from spaceone.core.connector import BaseConnector
from plugin.error import *

_LOGGER = logging.getLogger('spaceone')

REQUIRED_SECRET_KEYS = ["project_id", "private_key", "token_uri", "client_email"]


class BigqueryConnector(BaseConnector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = None
        self.credentials = None
        self.google_client = None

    def create_session(self, options: dict, secret_data: dict, schema: str):
        self._check_secret_data(secret_data)
        self.project_id = secret_data['project_id']

        self.credentials = google.oauth2.service_account.Credentials.from_service_account_info(secret_data)
        self.google_client = build('bigquery', 'v2', credentials=self.credentials)

    def list_tables(self, billing_export_project_id, dataset_id, **query):
        table_list = []

        query.update({'projectId': billing_export_project_id,
                      'datasetId': dataset_id})

        request = self.google_client.tables().list(**query)
        while request is not None:
            response = request.execute()
            for table in response.get('tables', []):
                table_list.append(table)
            request = self.google_client.tables().list_next(previous_request=request, previous_response=response)

        return table_list

    def read_df_from_bigquery(self, query):
        return pandas_gbq.read_gbq(query, project_id=self.project_id, credentials=self.credentials)

    @staticmethod
    def _check_secret_data(secret_data):
        missing_keys = [key for key in REQUIRED_SECRET_KEYS if key not in secret_data]
        if missing_keys:
            for key in missing_keys:
                raise ERROR_REQUIRED_PARAMETER(key=f"secret_data.{key}")
