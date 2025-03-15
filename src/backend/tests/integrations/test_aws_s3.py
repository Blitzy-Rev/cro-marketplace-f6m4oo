"""
Test module for AWS S3 integration functionality.

This module contains tests for the S3Client class and related functions,
ensuring proper handling of file uploads, downloads, and other S3 operations
with appropriate mocking of AWS services.
"""

import pytest
import unittest.mock as mock
import io
import os
import tempfile
import uuid
from botocore.exceptions import ClientError

from ...app.integrations.aws.s3 import (
    S3Client,
    upload_file,
    upload_fileobj,
    download_file,
    download_fileobj,
    get_object,
    delete_object,
    list_objects,
    generate_presigned_url,
    copy_object,
    get_object_metadata
)
from ...app.core.exceptions import IntegrationException
from ...app.constants.error_messages import INTEGRATION_ERRORS
from ...app.core.config import settings


@pytest.mark.parametrize('bucket_name', [None, 'test-bucket'])
def test_s3_client_initialization(bucket_name):
    """Test that S3Client initializes correctly with default bucket name"""
    with mock.patch('boto3.client') as mock_client:
        # Initialize client with or without bucket name
        client = S3Client(bucket_name=bucket_name)
        
        # Assert bucket name is set correctly
        expected_bucket = bucket_name if bucket_name else settings.S3_BUCKET_NAME
        assert client._bucket_name == expected_bucket
        
        # Verify boto3.client was called with correct parameters
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )


def test_upload_file_success():
    """Test successful file upload to S3"""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'test content')
        temp_file_path = temp_file.name
    
    try:
        with mock.patch('boto3.client') as mock_client:
            # Setup mock
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3
            
            # Call the function
            result = upload_file(
                file_path=temp_file_path,
                key='test/file.txt',
                bucket_name='test-bucket'
            )
            
            # Assert result and verify interactions
            assert result is True
            mock_client.assert_called_once_with(
                's3',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            mock_s3.upload_file.assert_called_once_with(
                Filename=temp_file_path,
                Bucket='test-bucket',
                Key='test/file.txt',
                ExtraArgs={}
            )
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)


def test_upload_file_failure():
    """Test file upload failure and exception handling"""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'test content')
        temp_file_path = temp_file.name
    
    try:
        with mock.patch('boto3.client') as mock_client:
            # Setup mock to raise exception
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3
            mock_s3.upload_file.side_effect = ClientError(
                {'Error': {'Code': 'TestException', 'Message': 'Test error message'}},
                'upload_file'
            )
            
            # Call the function and expect exception
            with pytest.raises(IntegrationException) as excinfo:
                upload_file(
                    file_path=temp_file_path,
                    key='test/file.txt',
                    bucket_name='test-bucket'
                )
            
            # Verify exception details
            assert INTEGRATION_ERRORS["S3_OPERATION_FAILED"] in str(excinfo.value)
            assert excinfo.value.error_code == "s3_upload_failed"
            assert "test/file.txt" in str(excinfo.value.details)
            
            # Verify client was called correctly
            mock_client.assert_called_once()
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)


def test_upload_fileobj_success():
    """Test successful file-like object upload to S3"""
    # Create a BytesIO object for testing
    file_obj = io.BytesIO(b'test content')
    
    with mock.patch('boto3.client') as mock_client:
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Call the function
        result = upload_fileobj(
            fileobj=file_obj,
            key='test/file.txt',
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.upload_fileobj.assert_called_once_with(
            Fileobj=file_obj,
            Bucket='test-bucket',
            Key='test/file.txt',
            ExtraArgs={}
        )


def test_download_file_success():
    """Test successful file download from S3"""
    # Create a temporary file path for download destination
    temp_file_path = os.path.join(tempfile.gettempdir(), 'test_download.txt')
    
    with mock.patch('boto3.client') as mock_client:
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Call the function
        result = download_file(
            key='test/file.txt',
            file_path=temp_file_path,
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.download_file.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.txt',
            Filename=temp_file_path
        )


def test_download_fileobj_success():
    """Test successful download to file-like object from S3"""
    # Create a BytesIO object for download destination
    file_obj = io.BytesIO()
    
    with mock.patch('boto3.client') as mock_client:
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Call the function
        result = download_fileobj(
            key='test/file.txt',
            fileobj=file_obj,
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.download_fileobj.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.txt',
            Fileobj=file_obj
        )


def test_get_object_success():
    """Test successful object retrieval from S3"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock with response
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        mock_response = {
            'Body': io.BytesIO(b'test content'),
            'ContentLength': 12,
            'ContentType': 'text/plain'
        }
        mock_s3.get_object.return_value = mock_response
        
        # Call the function
        result = get_object(
            key='test/file.txt',
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result == mock_response
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.txt'
        )


def test_delete_object_success():
    """Test successful object deletion from S3"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Call the function
        result = delete_object(
            key='test/file.txt',
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.txt'
        )


def test_list_objects_success():
    """Test successful listing of objects in S3 bucket"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock with response
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        mock_response = {
            'Contents': [
                {'Key': 'test/file1.txt'},
                {'Key': 'test/file2.txt'},
                {'Key': 'test/file3.txt'}
            ]
        }
        mock_s3.list_objects_v2.return_value = mock_response
        
        # Call the function
        result = list_objects(
            prefix='test/',
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result == ['test/file1.txt', 'test/file2.txt', 'test/file3.txt']
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.list_objects_v2.assert_called_once_with(
            Bucket='test-bucket',
            Prefix='test/'
        )


def test_generate_presigned_url_success():
    """Test successful generation of presigned URL"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock with response
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        mock_url = 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        mock_s3.generate_presigned_url.return_value = mock_url
        
        # Call the function
        result = generate_presigned_url(
            key='test/file.txt',
            bucket_name='test-bucket',
            operation='get_object',
            expiration=3600
        )
        
        # Assert result and verify interactions
        assert result == mock_url
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.generate_presigned_url.assert_called_once_with(
            ClientMethod='get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'test/file.txt'},
            ExpiresIn=3600
        )


def test_copy_object_success():
    """Test successful object copy within S3"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Call the function
        result = copy_object(
            source_key='test/source.txt',
            destination_key='test/destination.txt',
            source_bucket='source-bucket',
            destination_bucket='destination-bucket'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.copy_object.assert_called_once_with(
            CopySource={'Bucket': 'source-bucket', 'Key': 'test/source.txt'},
            Bucket='destination-bucket',
            Key='test/destination.txt'
        )


def test_get_object_metadata_success():
    """Test successful retrieval of object metadata"""
    with mock.patch('boto3.client') as mock_client:
        # Setup mock with response
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        mock_metadata = {
            'ContentLength': 12,
            'ContentType': 'text/plain',
            'Metadata': {'custom-key': 'custom-value'}
        }
        mock_s3.head_object.return_value = mock_metadata
        
        # Call the function
        result = get_object_metadata(
            key='test/file.txt',
            bucket_name='test-bucket'
        )
        
        # Assert result and verify interactions
        assert result == mock_metadata
        mock_client.assert_called_once_with(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        mock_s3.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test/file.txt'
        )


def test_s3client_upload_success():
    """Test successful upload using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.upload_fileobj') as mock_upload:
        # Setup mock
        mock_upload.return_value = True
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        content = b'test content'
        result = client.upload(
            content=content,
            key='test/file.txt',
            content_type='text/plain',
            metadata={'custom-key': 'custom-value'}
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_upload.assert_called_once()
        args, kwargs = mock_upload.call_args
        
        # Verify fileobj parameter contains our content
        assert 'fileobj' in kwargs
        assert isinstance(kwargs['fileobj'], io.BytesIO)
        
        # Verify other parameters
        assert kwargs['key'] == 'test/file.txt'
        assert kwargs['bucket_name'] == 'test-bucket'
        assert kwargs['extra_args']['ContentType'] == 'text/plain'
        assert kwargs['extra_args']['Metadata'] == {'custom-key': 'custom-value'}


def test_s3client_download_success():
    """Test successful download using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.download_fileobj') as mock_download:
        # Setup mock to write data to the BytesIO object
        def write_to_fileobj(*args, **kwargs):
            fileobj = kwargs['fileobj']
            fileobj.write(b'test content')
            return True
        
        mock_download.side_effect = write_to_fileobj
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.download(key='test/file.txt')
        
        # Assert result and verify interactions
        assert result == b'test content'
        mock_download.assert_called_once()
        args, kwargs = mock_download.call_args
        
        # Verify parameters
        assert kwargs['key'] == 'test/file.txt'
        assert kwargs['bucket_name'] == 'test-bucket'
        assert isinstance(kwargs['fileobj'], io.BytesIO)


def test_s3client_delete_success():
    """Test successful deletion using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.delete_object') as mock_delete:
        # Setup mock
        mock_delete.return_value = True
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.delete(key='test/file.txt')
        
        # Assert result and verify interactions
        assert result is True
        mock_delete.assert_called_once_with(
            key='test/file.txt',
            bucket_name='test-bucket'
        )


def test_s3client_list_success():
    """Test successful listing using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.list_objects') as mock_list:
        # Setup mock
        mock_list.return_value = ['test/file1.txt', 'test/file2.txt']
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.list(prefix='test/')
        
        # Assert result and verify interactions
        assert result == ['test/file1.txt', 'test/file2.txt']
        mock_list.assert_called_once_with(
            prefix='test/',
            bucket_name='test-bucket'
        )


def test_s3client_get_presigned_url_success():
    """Test successful presigned URL generation using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.generate_presigned_url') as mock_url:
        # Setup mock
        mock_url.return_value = 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.get_presigned_url(
            key='test/file.txt',
            operation='get_object',
            expiration=3600
        )
        
        # Assert result and verify interactions
        assert result == 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        mock_url.assert_called_once_with(
            key='test/file.txt',
            bucket_name='test-bucket',
            operation='get_object',
            expiration=3600,
            params=None
        )


def test_s3client_get_download_url_success():
    """Test successful download URL generation using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.generate_presigned_url') as mock_url:
        # Setup mock
        mock_url.return_value = 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.get_download_url(key='test/file.txt', expiration=3600)
        
        # Assert result and verify interactions
        assert result == 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        mock_url.assert_called_once_with(
            key='test/file.txt',
            bucket_name='test-bucket',
            operation='get_object',
            expiration=3600,
            params=None
        )


def test_s3client_get_upload_url_success():
    """Test successful upload URL generation using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.generate_presigned_url') as mock_url:
        # Setup mock
        mock_url.return_value = 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.get_upload_url(
            key='test/file.txt',
            content_type='text/plain',
            expiration=3600
        )
        
        # Assert result and verify interactions
        assert result == 'https://test-bucket.s3.amazonaws.com/test/file.txt?signature=abc123'
        mock_url.assert_called_once_with(
            key='test/file.txt',
            bucket_name='test-bucket',
            operation='put_object',
            expiration=3600,
            params={'ContentType': 'text/plain'}
        )


def test_s3client_copy_success():
    """Test successful object copy using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.copy_object') as mock_copy:
        # Setup mock
        mock_copy.return_value = True
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.copy(
            source_key='test/source.txt',
            destination_key='test/destination.txt'
        )
        
        # Assert result and verify interactions
        assert result is True
        mock_copy.assert_called_once_with(
            source_key='test/source.txt',
            destination_key='test/destination.txt',
            source_bucket='test-bucket',
            destination_bucket='test-bucket'
        )


def test_s3client_get_metadata_success():
    """Test successful metadata retrieval using S3Client class"""
    with mock.patch('boto3.client'), mock.patch('...app.integrations.aws.s3.get_object_metadata') as mock_metadata:
        # Setup mock
        mock_metadata.return_value = {
            'ContentLength': 12,
            'ContentType': 'text/plain',
            'Metadata': {'custom-key': 'custom-value'}
        }
        
        # Initialize client
        client = S3Client(bucket_name='test-bucket')
        
        # Call the method
        result = client.get_metadata(key='test/file.txt')
        
        # Assert result and verify interactions
        assert result == {
            'ContentLength': 12,
            'ContentType': 'text/plain',
            'Metadata': {'custom-key': 'custom-value'}
        }
        mock_metadata.assert_called_once_with(
            key='test/file.txt',
            bucket_name='test-bucket'
        )


def test_s3client_generate_key():
    """Test key generation with folder and filename"""
    with mock.patch('uuid.uuid4') as mock_uuid:
        # Setup mock
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Initialize client
        client = S3Client()
        
        # Call the method
        result = client.generate_key(
            folder='documents',
            filename='test.pdf'
        )
        
        # Assert result format
        assert result == 'documents/12345678-1234-5678-1234-567812345678.pdf'