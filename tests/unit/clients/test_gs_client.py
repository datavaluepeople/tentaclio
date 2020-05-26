"""Test of the GS Client."""
import io

import pytest
import mock

from google.cloud import exceptions as google_exceptions

from tentaclio.clients import gs_client, exceptions


@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,hostname,path",
    [
        ("gs://bucket/prefix", "bucket", "prefix"),
        ("gs://:@gs", None, ""),
        ("gs://public_key:private_key@gs", None, ""),
        ("gs://:@bucket", "bucket", ""),
        ("gs://:@bucket/prefix", "bucket", "prefix"),
    ],
)
def test_parsing_gs_url(m_connect, m_init, url, hostname, path):
    """Test the parsing of the gs url."""
    client = gs_client.GSClient(url)

    assert client.key_name == path
    assert client.bucket == hostname
    # These will be checked in the init_creds test
    assert client.project is None
    assert client.creds is None


@mock.patch("tentaclio.clients.GSClient._get_default_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,project,creds,d_project,d_creds",
    [
        ("gs://bucket/prefix", None, None, None, None),
        ("gs://bucket/prefix", "project", None, None, None),
        ("gs://bucket/prefix", "project", None, "d_project", None),
        ("gs://bucket/prefix", None, "creds", None, "d_creds"),
        ("gs://bucket/prefix", None, None, None, "d_creds"),
    ],
)
def test_init_creds_error(
    m_connect,
    m_default,
    url,
    project,
    creds,
    d_project,
    d_creds
):
    """Test _init_creds function throws erors."""
    m_default.return_value = (d_creds, d_project)
    with pytest.raises(exceptions.GSError):
        gs_client.GSClient(url, project=project, creds=creds)

    m_default.assert_called_once()


@mock.patch("tentaclio.clients.GSClient._get_default_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,project,creds,d_project,d_creds",
    [
        ("gs://bucket/prefix", "set_project", "set_creds", "not_project", "not_creds"),
        ("gs://bucket/prefix", "set_project", None, "not_project", "set_creds"),
        ("gs://bucket/prefix", None, None, "set_project", "set_creds"),
    ],
)
def test_init_creds(
    m_connect,
    m_default,
    url,
    project,
    creds,
    d_project,
    d_creds
):
    """Test _init_creds function sets correct values."""
    m_default.return_value = (d_creds, d_project)
    gs_client.GSClient(url, project=project, creds=creds)
    m_default.assert_called_once()
    gs_client.project = "set_project"
    gs_client.creds = "set_creds"


@mock.patch("tentaclio.clients.GSClient._get")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://:@gs", None, None),
        ("gs://:@gs", "bucket", None),
        ("gs://:@bucket", None, None)
    ],
)
def test_get_invalid_path(m_connect, m_init, m_get, url, bucket, key):
    """Test get for with invalid paths."""
    with gs_client.GSClient(url) as client:
        with pytest.raises(exceptions.GSError):
            client.get(io.StringIO(), bucket_name=bucket, key_name=key)

    m_get.assert_not_called()


@mock.patch("tentaclio.clients.GSClient._get")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://:@bucket/not_found", "bucket", "not_found")
    ],
)
def test_get_not_found(m_connect, m_init, m_get, url, bucket, key):
    """That when the connection raises a NotFound an GSError is thrown."""
    m_get.side_effect = google_exceptions.NotFound("not found")
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        with pytest.raises(exceptions.GSError):
            client.get(stream, bucket_name=bucket, key_name=key)

    m_get.assert_called_once_with(stream, bucket, key)


@mock.patch("tentaclio.clients.GSClient._get")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://bucket/prefix", "bucket", "prefix"),
    ]
)
def test_get(m_connect, m_init, m_get, url, bucket, key):
    """Test get valid."""
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        client.get(stream, bucket_name=bucket, key_name=key)

    m_get.assert_called_once_with(stream, bucket, key)


@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://bucket/prefix", "bucket", "prefix"),
    ]
)
def test_helper_get(m_connect, m_init, url, bucket, key):
    """Test helper get is correctly called."""
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        client._get(stream, bucket_name=bucket, key_name=key)

    m_connect.return_value.bucket.assert_called_once_with(bucket)


@mock.patch("tentaclio.clients.GSClient._put")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://:@gs", None, None),
        ("gs://:@gs", "bucket", None),
        ("gs://:@bucket", None, None)
    ],
)
def test_put_invalid_path(m_connect, m_init, m_put, url, bucket, key):
    """Test put for with invalid paths."""
    with gs_client.GSClient(url) as client:
        with pytest.raises(exceptions.GSError):
            client.put(io.StringIO(), bucket_name=bucket, key_name=key)

    m_put.assert_not_called()


@mock.patch("tentaclio.clients.GSClient._put")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://:@bucket/not_found", "bucket", "not_found")
    ],
)
def test_put_not_found(m_connect, m_init, m_put, url, bucket, key):
    """That when the connection raises a NotFound an GSError is thrown."""
    m_put.side_effect = google_exceptions.NotFound("not found")
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        with pytest.raises(exceptions.GSError):
            client.put(stream, bucket_name=bucket, key_name=key)

    m_put.assert_called_once_with(stream, bucket, key)


@mock.patch("tentaclio.clients.GSClient._put")
@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://bucket/prefix", "bucket", "prefix"),
    ]
)
def test_put(m_connect, m_init, m_put, url, bucket, key):
    """Test put valid."""
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        client.put(stream, bucket_name=bucket, key_name=key)

    m_put.assert_called_once_with(stream, bucket, key)


@mock.patch("tentaclio.clients.GSClient._init_creds")
@mock.patch("tentaclio.clients.GSClient._connect")
@pytest.mark.parametrize(
    "url,bucket,key", [
        ("gs://bucket/prefix", "bucket", "prefix"),
    ]
)
def test_helper_put(m_connect, m_init, url, bucket, key):
    """Test put valid."""
    stream = io.StringIO()
    with gs_client.GSClient(url) as client:
        client._put(stream, bucket_name=bucket, key_name=key)

    m_connect.return_value.bucket.assert_called_once_with(bucket)
