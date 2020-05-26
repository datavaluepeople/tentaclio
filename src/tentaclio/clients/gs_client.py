"""GS Stream client."""
from typing import Optional, Union, Tuple, cast

from google.auth import credentials, default
from google.cloud import storage, exceptions as google_exceptions

from tentaclio import urls, protocols

from . import base_client, decorators, exceptions


__all__ = ["GSClient"]


class GSClient(base_client.BaseClient["GSClient"]):
    """GS client.

    Ref: https://googleapis.dev/python/storage/latest/index.html
    """

    allowed_schemes = ["gs"]

    conn: storage.Client
    project: Optional[str] = None
    creds: Optional[credentials.Credentials] = None
    bucket: Optional[str]
    key_name: Optional[str]

    def __init__(
        self,
        url: Union[urls.URL, str],
        project: Optional[str] = None,
        creds: Optional[credentials.Credentials] = None
    ) -> None:
        """Create a new GS client.

        The client is created based on a URL of the form
        gs://bucket/key.
        Authenticated with environment variables:
        https://googleapis.dev/python/google-api-core/latest/auth.html

        Arguments:
            :url: URL of dataset
            :project: project for the storage client. If not set the default for the environment
                will be used. See storage client docs.
            :creds: credentials for the storage client. If not set the default for the environment
                will be used. See storage client docs.
        """
        super().__init__(url)

        self._init_creds(project, creds)
        self.bucket = self.url.hostname or None
        self.key_name = self.url.path[1:] if self.url.path != "" else ""

        if self.bucket == "gs":
            self.bucket = None

    def _connect(self) -> storage.Client:
        return storage.Client(credentials=self.creds, project=self.project)

    def close(self) -> None:
        """Close the connection.

        This is fake. GS doesn't allow to close gs connections.
        """
        # gs doesn't have close method
        if self.closed:
            raise ValueError("Trying to close a closed client")
        self.closed = True

    # Stream methods:

    @decorators.check_conn
    def get(
        self, writer: protocols.ByteWriter, bucket_name: str = None, key_name: str = None
    ) -> None:
        """Download the contents from gs and write them in the provided writer.

        Arguments:
            :bucket_name: If not provided in the url at construction time.
            :key_name: If not provided in the url at construction time.
        """
        gs_bucket, gs_key = self._fetch_bucket_and_key(bucket_name, key_name)

        try:
            self._get(writer, gs_bucket, gs_key)
        except google_exceptions.NotFound:
            raise exceptions.GSError("Unable to fetch the remote file")

    @decorators.check_conn
    def put(
        self, reader: protocols.ByteReader, bucket_name: str = None, key_name: str = None
    ) -> None:
        """Up the contents to gs.

        Arguments:
            :bucket_name: If not provided in the url at construction time.
            :key_name: If not provided in the url at construction time.
        """
        gs_bucket, gs_key = self._fetch_bucket_and_key(bucket_name, key_name)

        try:
            self._put(reader, gs_bucket, gs_key)
        except google_exceptions.NotFound:
            raise exceptions.GSError("Unable to fetch the remote file")

    # Helpers:

    def _get_default_creds(self) -> Tuple[credentials.Credentials, Optional[str]]:
        """Get the default creds.

        Wrapper for the default function so it can be mocked.
        Unable to mock the default function thus added a wrapper.
        """
        return default()

    def _init_creds(
        self,
        project: Optional[str] = None,
        creds: Optional[credentials.Credentials] = None
    ) -> None:
        default_creds, default_project = self._get_default_creds()
        self.creds = creds or default_creds
        self.project = project or default_project

        if self.project is None:
            raise exceptions.GSError("Must have a project set to use gs.")

        if self.creds is None:
            raise exceptions.GSError("Must have credentials to use gs.")

    def _fetch_bucket_and_key(self, bucket: Optional[str], key: Optional[str]) -> Tuple[str, str]:
        bucket_name = bucket or self.bucket
        if bucket_name is None:
            raise exceptions.GSError("Missing remote bucket")

        key_name = key or self.key_name
        if key_name == "":
            raise exceptions.GSError("Missing remote key")

        return bucket_name, cast(str, key_name)

    def _get_blob(self, bucket_name: str, key_name: str) -> storage.Bucket:
        """Get the bucket client."""
        bucket = self.conn.bucket(bucket_name)
        return bucket.blob(key_name)

    def _get(
        self, writer: protocols.ByteWriter, bucket_name: str, key_name: str
    ) -> None:
        """Download file on the client."""
        blob = self._get_blob(bucket_name, key_name)
        blob.download_to_file(writer)

    def _put(
        self, reader: protocols.ByteReader, bucket_name: str, key_name: str
    ) -> None:
        """Upload on the client."""
        blob = self._get_blob(bucket_name, key_name)
        blob.upload_from_file(reader)
