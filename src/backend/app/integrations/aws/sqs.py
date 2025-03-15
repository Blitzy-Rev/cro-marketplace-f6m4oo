"""
AWS SQS Integration Module

This module provides a high-level interface for interacting with Amazon Simple Queue Service (SQS).
It implements producer and consumer patterns for asynchronous message processing, supporting both 
standard and FIFO queues with configurable retry and error handling mechanisms.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Union

import boto3  # version ^1.26.0
from botocore.exceptions import ClientError  # version ^1.26.0
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type  # version ^8.2.0

from ...core.config import settings, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from ...core.logging import get_logger
from ...core.exceptions import IntegrationException
from ...constants.error_messages import INTEGRATION_ERRORS

# Initialize logger
logger = get_logger(__name__)


def send_message(
    queue_url: str,
    message_body: Dict[str, Any],
    message_attributes: Optional[Dict[str, str]] = None,
    message_group_id: Optional[str] = None,
    message_deduplication_id: Optional[str] = None,
    delay_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Send a message to an SQS queue.
    
    Args:
        queue_url: URL of the SQS queue
        message_body: Message body as a dictionary (will be converted to JSON)
        message_attributes: Optional message attributes
        message_group_id: Required for FIFO queues, specifies the group the message belongs to
        message_deduplication_id: Optional for FIFO queues, specifies the deduplication ID
        delay_seconds: Optional delay in seconds (0-900) before the message is visible
        
    Returns:
        Response from SQS containing MessageId and other metadata
        
    Raises:
        IntegrationException: If the message fails to send
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Convert message body to JSON
        message_json = json.dumps(message_body)
        
        # Prepare message parameters
        params = {
            'QueueUrl': queue_url,
            'MessageBody': message_json,
        }
        
        # Add optional parameters if provided
        if message_attributes:
            params['MessageAttributes'] = message_attributes
        
        if delay_seconds is not None:
            params['DelaySeconds'] = delay_seconds
        
        # Add FIFO queue specific parameters if provided
        if message_group_id:
            params['MessageGroupId'] = message_group_id
            
        if message_deduplication_id:
            params['MessageDeduplicationId'] = message_deduplication_id
        
        # Send message to SQS queue
        response = client.send_message(**params)
        
        logger.info(f"Message sent to queue {queue_url} with ID {response.get('MessageId')}")
        return response
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to send message to queue {queue_url}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_send_failed",
            details={"queue_url": queue_url, "error": error_message}
        )


def receive_messages(
    queue_url: str,
    max_messages: int = 10,
    wait_time_seconds: int = 20,
    attribute_names: Optional[List[str]] = None,
    message_attribute_names: Optional[List[str]] = None,
    visibility_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Receive messages from an SQS queue.
    
    Args:
        queue_url: URL of the SQS queue
        max_messages: Maximum number of messages to receive (1-10)
        wait_time_seconds: Time to wait for messages (0-20 seconds)
        attribute_names: List of message attributes to retrieve
        message_attribute_names: List of custom message attributes to retrieve
        visibility_timeout: The duration (in seconds) that the received messages are hidden
        
    Returns:
        List of messages received from the queue
        
    Raises:
        IntegrationException: If the receive operation fails
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Prepare receive message parameters
        params = {
            'QueueUrl': queue_url,
            'MaxNumberOfMessages': max_messages,
            'WaitTimeSeconds': wait_time_seconds,
        }
        
        # Add optional parameters if provided
        if attribute_names:
            params['AttributeNames'] = attribute_names
        
        if message_attribute_names:
            params['MessageAttributeNames'] = message_attribute_names
            
        if visibility_timeout:
            params['VisibilityTimeout'] = visibility_timeout
        
        # Receive messages from SQS queue
        response = client.receive_message(**params)
        
        # Extract messages from response
        messages = response.get('Messages', [])
        logger.info(f"Received {len(messages)} messages from queue {queue_url}")
        
        return messages
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to receive messages from queue {queue_url}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_receive_failed",
            details={"queue_url": queue_url, "error": error_message}
        )


def delete_message(queue_url: str, receipt_handle: str) -> Dict[str, Any]:
    """
    Delete a message from an SQS queue.
    
    Args:
        queue_url: URL of the SQS queue
        receipt_handle: Receipt handle of the message to delete
        
    Returns:
        Response from SQS confirming message deletion
        
    Raises:
        IntegrationException: If the delete operation fails
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Delete message from SQS queue
        response = client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        
        logger.info(f"Deleted message with receipt handle {receipt_handle[:20]}... from queue {queue_url}")
        return response
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to delete message from queue {queue_url}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_delete_failed",
            details={"queue_url": queue_url, "error": error_message}
        )


def create_queue(
    queue_name: str,
    attributes: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, str]] = None,
    fifo_queue: Optional[bool] = False
) -> str:
    """
    Create a new SQS queue.
    
    Args:
        queue_name: Name of the queue to create
        attributes: Queue attributes
        tags: Tags to apply to the queue
        fifo_queue: Whether to create a FIFO queue
        
    Returns:
        URL of the created queue
        
    Raises:
        IntegrationException: If the queue creation fails
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Initialize queue attributes
        queue_attributes = {}
        
        # Configure FIFO queue if requested
        if fifo_queue:
            queue_attributes['FifoQueue'] = 'true'
            # Ensure queue name ends with .fifo
            if not queue_name.endswith('.fifo'):
                queue_name = f"{queue_name}.fifo"
        
        # Add provided attributes
        if attributes:
            queue_attributes.update(attributes)
        
        # Create queue
        if queue_attributes:
            response = client.create_queue(
                QueueName=queue_name,
                Attributes=queue_attributes
            )
        else:
            response = client.create_queue(
                QueueName=queue_name
            )
        
        queue_url = response['QueueUrl']
        
        # Add tags if provided
        if tags:
            client.tag_queue(
                QueueUrl=queue_url,
                Tags=tags
            )
        
        logger.info(f"Created queue {queue_name} with URL {queue_url}")
        return queue_url
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to create queue {queue_name}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_create_failed",
            details={"queue_name": queue_name, "error": error_message}
        )


def get_queue_url(queue_name: str) -> str:
    """
    Get the URL of an existing SQS queue.
    
    Args:
        queue_name: Name of the queue
        
    Returns:
        URL of the queue
        
    Raises:
        IntegrationException: If the queue URL retrieval fails
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Get queue URL
        response = client.get_queue_url(
            QueueName=queue_name
        )
        
        queue_url = response['QueueUrl']
        logger.info(f"Retrieved URL for queue {queue_name}: {queue_url}")
        return queue_url
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to get URL for queue {queue_name}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_get_url_failed",
            details={"queue_name": queue_name, "error": error_message}
        )


def purge_queue(queue_url: str) -> Dict[str, Any]:
    """
    Purge all messages from an SQS queue.
    
    Args:
        queue_url: URL of the SQS queue
        
    Returns:
        Response from SQS confirming queue purge
        
    Raises:
        IntegrationException: If the purge operation fails
    """
    try:
        # Create SQS client
        client = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Purge queue
        response = client.purge_queue(
            QueueUrl=queue_url
        )
        
        logger.info(f"Purged all messages from queue {queue_url}")
        return response
    
    except ClientError as e:
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Failed to purge queue {queue_url}: {error_message}")
        raise IntegrationException(
            message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
            service_name="AWS SQS",
            error_code="sqs_purge_failed",
            details={"queue_url": queue_url, "error": error_message}
        )


class SQSClient:
    """Client for interacting with AWS SQS queues."""
    
    def __init__(
        self,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """
        Initialize the SQS client with AWS credentials.
        
        Args:
            region_name: AWS region name (defaults to settings.AWS_REGION)
            aws_access_key_id: AWS access key ID (defaults to settings.AWS_ACCESS_KEY_ID)
            aws_secret_access_key: AWS secret access key (defaults to settings.AWS_SECRET_ACCESS_KEY)
        """
        self.region_name = region_name or AWS_REGION
        self.aws_access_key_id = aws_access_key_id or AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or AWS_SECRET_ACCESS_KEY
        
        # Initialize boto3 SQS client
        self._client = boto3.client(
            'sqs',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
    
    def send_message(
        self,
        queue_url: str,
        message_body: Dict[str, Any],
        message_attributes: Optional[Dict[str, str]] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
        delay_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            message_body: Message body as a dictionary (will be converted to JSON)
            message_attributes: Optional message attributes
            message_group_id: Required for FIFO queues, specifies the group the message belongs to
            message_deduplication_id: Optional for FIFO queues, specifies the deduplication ID
            delay_seconds: Optional delay in seconds (0-900) before the message is visible
            
        Returns:
            Response from SQS containing MessageId and other metadata
            
        Raises:
            IntegrationException: If the message fails to send
        """
        try:
            # Convert message body to JSON
            message_json = json.dumps(message_body)
            
            # Prepare message parameters
            params = {
                'QueueUrl': queue_url,
                'MessageBody': message_json,
            }
            
            # Add optional parameters if provided
            if message_attributes:
                params['MessageAttributes'] = message_attributes
            
            if delay_seconds is not None:
                params['DelaySeconds'] = delay_seconds
            
            # Add FIFO queue specific parameters if provided
            if message_group_id:
                params['MessageGroupId'] = message_group_id
                
            if message_deduplication_id:
                params['MessageDeduplicationId'] = message_deduplication_id
            
            # Send message to SQS queue
            response = self._client.send_message(**params)
            
            logger.info(f"Message sent to queue {queue_url} with ID {response.get('MessageId')}")
            return response
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to send message to queue {queue_url}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_send_failed",
                details={"queue_url": queue_url, "error": error_message}
            )
    
    def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        attribute_names: Optional[List[str]] = None,
        message_attribute_names: Optional[List[str]] = None,
        visibility_timeout: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            max_messages: Maximum number of messages to receive (1-10)
            wait_time_seconds: Time to wait for messages (0-20 seconds)
            attribute_names: List of message attributes to retrieve
            message_attribute_names: List of custom message attributes to retrieve
            visibility_timeout: The duration (in seconds) that the received messages are hidden
            
        Returns:
            List of messages received from the queue
            
        Raises:
            IntegrationException: If the receive operation fails
        """
        try:
            # Prepare receive message parameters
            params = {
                'QueueUrl': queue_url,
                'MaxNumberOfMessages': max_messages,
                'WaitTimeSeconds': wait_time_seconds,
            }
            
            # Add optional parameters if provided
            if attribute_names:
                params['AttributeNames'] = attribute_names
            
            if message_attribute_names:
                params['MessageAttributeNames'] = message_attribute_names
                
            if visibility_timeout:
                params['VisibilityTimeout'] = visibility_timeout
            
            # Receive messages from SQS queue
            response = self._client.receive_message(**params)
            
            # Extract messages from response
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages from queue {queue_url}")
            
            return messages
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to receive messages from queue {queue_url}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_receive_failed",
                details={"queue_url": queue_url, "error": error_message}
            )
    
    def delete_message(self, queue_url: str, receipt_handle: str) -> Dict[str, Any]:
        """
        Delete a message from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            Response from SQS confirming message deletion
            
        Raises:
            IntegrationException: If the delete operation fails
        """
        try:
            # Delete message from SQS queue
            response = self._client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info(f"Deleted message with receipt handle {receipt_handle[:20]}... from queue {queue_url}")
            return response
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to delete message from queue {queue_url}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_delete_failed",
                details={"queue_url": queue_url, "error": error_message}
            )
    
    def create_queue(
        self,
        queue_name: str,
        attributes: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        fifo_queue: Optional[bool] = False
    ) -> str:
        """
        Create a new SQS queue.
        
        Args:
            queue_name: Name of the queue to create
            attributes: Queue attributes
            tags: Tags to apply to the queue
            fifo_queue: Whether to create a FIFO queue
            
        Returns:
            URL of the created queue
            
        Raises:
            IntegrationException: If the queue creation fails
        """
        try:
            # Initialize queue attributes
            queue_attributes = {}
            
            # Configure FIFO queue if requested
            if fifo_queue:
                queue_attributes['FifoQueue'] = 'true'
                # Ensure queue name ends with .fifo
                if not queue_name.endswith('.fifo'):
                    queue_name = f"{queue_name}.fifo"
            
            # Add provided attributes
            if attributes:
                queue_attributes.update(attributes)
            
            # Create queue
            if queue_attributes:
                response = self._client.create_queue(
                    QueueName=queue_name,
                    Attributes=queue_attributes
                )
            else:
                response = self._client.create_queue(
                    QueueName=queue_name
                )
            
            queue_url = response['QueueUrl']
            
            # Add tags if provided
            if tags:
                self._client.tag_queue(
                    QueueUrl=queue_url,
                    Tags=tags
                )
            
            logger.info(f"Created queue {queue_name} with URL {queue_url}")
            return queue_url
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to create queue {queue_name}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_create_failed",
                details={"queue_name": queue_name, "error": error_message}
            )
    
    def get_queue_url(self, queue_name: str) -> str:
        """
        Get the URL of an existing SQS queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            URL of the queue
            
        Raises:
            IntegrationException: If the queue URL retrieval fails
        """
        try:
            # Get queue URL
            response = self._client.get_queue_url(
                QueueName=queue_name
            )
            
            queue_url = response['QueueUrl']
            logger.info(f"Retrieved URL for queue {queue_name}: {queue_url}")
            return queue_url
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to get URL for queue {queue_name}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_get_url_failed",
                details={"queue_name": queue_name, "error": error_message}
            )
    
    def purge_queue(self, queue_url: str) -> Dict[str, Any]:
        """
        Purge all messages from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            
        Returns:
            Response from SQS confirming queue purge
            
        Raises:
            IntegrationException: If the purge operation fails
        """
        try:
            # Purge queue
            response = self._client.purge_queue(
                QueueUrl=queue_url
            )
            
            logger.info(f"Purged all messages from queue {queue_url}")
            return response
        
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to purge queue {queue_url}: {error_message}")
            raise IntegrationException(
                message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                service_name="AWS SQS",
                error_code="sqs_purge_failed",
                details={"queue_url": queue_url, "error": error_message}
            )
    
    def process_messages(
        self,
        queue_url: str,
        callback: Callable[[Dict[str, Any]], bool],
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        auto_delete: bool = True
    ) -> int:
        """
        Process messages from a queue with a callback function.
        
        Args:
            queue_url: URL of the SQS queue
            callback: Function to process each message, should return True for success
            max_messages: Maximum number of messages to receive in each batch
            wait_time_seconds: Time to wait for messages
            auto_delete: Whether to automatically delete messages after successful processing
            
        Returns:
            Number of successfully processed messages
            
        Raises:
            IntegrationException: If the receive operation fails
        """
        # Receive messages from the queue
        messages = self.receive_messages(
            queue_url=queue_url,
            max_messages=max_messages,
            wait_time_seconds=wait_time_seconds
        )
        
        # Initialize counter for processed messages
        processed_count = 0
        
        # Process each message
        for message in messages:
            receipt_handle = message['ReceiptHandle']
            try:
                # Parse message body (assumes JSON)
                body = json.loads(message['Body'])
                
                # Process message with callback
                success = callback(body)
                
                # Delete message if processing was successful and auto_delete is enabled
                if success and auto_delete:
                    self.delete_message(queue_url, receipt_handle)
                
                # Increment counter if processing was successful
                if success:
                    processed_count += 1
            
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                # Don't increment counter for failed messages
        
        return processed_count


class SQSProducer:
    """Producer for sending messages to SQS queues with retry capabilities."""
    
    def __init__(
        self,
        queue_url: str,
        is_fifo_queue: Optional[bool] = False,
        client: Optional[SQSClient] = None
    ):
        """
        Initialize the SQS producer.
        
        Args:
            queue_url: URL of the SQS queue
            is_fifo_queue: Whether the queue is a FIFO queue
            client: Optional pre-configured SQSClient
        """
        self.queue_url = queue_url
        self.is_fifo_queue = is_fifo_queue
        self.client = client or SQSClient()
    
    def send(
        self,
        message_body: Dict[str, Any],
        message_attributes: Optional[Dict[str, str]] = None,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
        delay_seconds: Optional[int] = None,
        max_retries: Optional[int] = 3
    ) -> Dict[str, Any]:
        """
        Send a message to the queue with retry logic.
        
        Args:
            message_body: Message body as a dictionary
            message_attributes: Optional message attributes
            message_group_id: Message group ID for FIFO queues
            message_deduplication_id: Message deduplication ID for FIFO queues
            delay_seconds: Delay in seconds before the message is visible
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response from SQS containing MessageId and other metadata
            
        Raises:
            IntegrationException: If the message fails to send after retries
        """
        # For FIFO queues, ensure message_group_id is provided
        if self.is_fifo_queue and not message_group_id:
            message_group_id = "default"
        
        # For FIFO queues, generate a deduplication ID if not provided
        if self.is_fifo_queue and not message_deduplication_id:
            message_deduplication_id = str(uuid.uuid4())
        
        # Create retry decorator with exponential backoff
        retry_decorator = retry(
            retry=retry_if_exception_type(IntegrationException),
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10)
        )
        
        # Apply retry decorator to send_message
        @retry_decorator
        def send_with_retry():
            return self.client.send_message(
                queue_url=self.queue_url,
                message_body=message_body,
                message_attributes=message_attributes,
                message_group_id=message_group_id,
                message_deduplication_id=message_deduplication_id,
                delay_seconds=delay_seconds
            )
        
        # Send message with retry logic
        return send_with_retry()
    
    def send_batch(
        self,
        messages: List[Dict[str, Any]],
        message_group_id: Optional[str] = None,
        max_retries: Optional[int] = 3
    ) -> List[Dict[str, Any]]:
        """
        Send multiple messages to the queue in a batch.
        
        Args:
            messages: List of message bodies as dictionaries
            message_group_id: Message group ID for FIFO queues
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of successful message responses
            
        Raises:
            IntegrationException: If the batch send operation fails after retries
        """
        successful_sends = []
        
        # SQS can process up to 10 messages in a batch
        batch_size = 10
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            
            # Prepare batch entries
            entries = []
            for idx, msg in enumerate(batch):
                entry_id = str(idx)
                entry = {
                    'Id': entry_id,
                    'MessageBody': json.dumps(msg)
                }
                
                # For FIFO queues, add required attributes
                if self.is_fifo_queue:
                    entry['MessageGroupId'] = message_group_id or "default"
                    entry['MessageDeduplicationId'] = str(uuid.uuid4())
                
                entries.append(entry)
            
            # Create retry decorator
            retry_decorator = retry(
                retry=retry_if_exception_type(Exception),
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=2, max=10)
            )
            
            # Send batch with retry logic
            @retry_decorator
            def send_batch_with_retry():
                try:
                    response = self.client._client.send_message_batch(
                        QueueUrl=self.queue_url,
                        Entries=entries
                    )
                    
                    # Process successful sends
                    for success in response.get('Successful', []):
                        batch_idx = int(success['Id'])
                        if batch_idx < len(batch):
                            original_msg = batch[batch_idx]
                            successful_sends.append({
                                'MessageId': success['MessageId'],
                                'Body': original_msg
                            })
                    
                    # Log any failed sends
                    for failure in response.get('Failed', []):
                        logger.error(f"Failed to send message {failure['Id']}: {failure.get('Message')}")
                    
                    return response
                
                except ClientError as e:
                    error_message = e.response.get('Error', {}).get('Message', str(e))
                    logger.error(f"Batch send failed: {error_message}")
                    raise IntegrationException(
                        message=INTEGRATION_ERRORS["SQS_OPERATION_FAILED"],
                        service_name="AWS SQS",
                        error_code="sqs_batch_send_failed",
                        details={"queue_url": self.queue_url, "error": error_message}
                    )
            
            # Send the batch
            send_batch_with_retry()
        
        return successful_sends


class SQSConsumer:
    """Consumer for receiving and processing messages from SQS queues."""
    
    def __init__(
        self,
        queue_url: str,
        max_messages: Optional[int] = 10,
        wait_time_seconds: Optional[int] = 20,
        visibility_timeout: Optional[int] = 30,
        client: Optional[SQSClient] = None
    ):
        """
        Initialize the SQS consumer.
        
        Args:
            queue_url: URL of the SQS queue
            max_messages: Maximum number of messages to receive in each batch
            wait_time_seconds: Time to wait for messages (0-20 seconds)
            visibility_timeout: The duration that the received messages are hidden
            client: Optional pre-configured SQSClient
        """
        self.queue_url = queue_url
        self.max_messages = max_messages
        self.wait_time_seconds = wait_time_seconds
        self.visibility_timeout = visibility_timeout
        self.client = client or SQSClient()
    
    def receive(
        self,
        attribute_names: Optional[List[str]] = None,
        message_attribute_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from the queue.
        
        Args:
            attribute_names: List of message attributes to retrieve
            message_attribute_names: List of custom message attributes to retrieve
            
        Returns:
            List of messages received from the queue
            
        Raises:
            IntegrationException: If the receive operation fails
        """
        return self.client.receive_messages(
            queue_url=self.queue_url,
            max_messages=self.max_messages,
            wait_time_seconds=self.wait_time_seconds,
            attribute_names=attribute_names,
            message_attribute_names=message_attribute_names,
            visibility_timeout=str(self.visibility_timeout)
        )
    
    def delete(self, receipt_handle: str) -> Dict[str, Any]:
        """
        Delete a message from the queue.
        
        Args:
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            Response from SQS confirming message deletion
            
        Raises:
            IntegrationException: If the delete operation fails
        """
        return self.client.delete_message(
            queue_url=self.queue_url,
            receipt_handle=receipt_handle
        )
    
    def process(
        self,
        callback: Callable[[Dict[str, Any]], bool],
        auto_delete: bool = True
    ) -> int:
        """
        Process messages from the queue with a callback function.
        
        Args:
            callback: Function to process each message, should return True for success
            auto_delete: Whether to automatically delete messages after successful processing
            
        Returns:
            Number of successfully processed messages
            
        Raises:
            IntegrationException: If the receive operation fails
        """
        return self.client.process_messages(
            queue_url=self.queue_url,
            callback=callback,
            max_messages=self.max_messages,
            wait_time_seconds=self.wait_time_seconds,
            auto_delete=auto_delete
        )
    
    def poll(
        self,
        callback: Callable[[Dict[str, Any]], bool],
        auto_delete: bool = True,
        polling_interval: Optional[int] = 0,
        max_polls: Optional[int] = None
    ) -> int:
        """
        Continuously poll the queue for messages and process them.
        
        Args:
            callback: Function to process each message, should return True for success
            auto_delete: Whether to automatically delete messages after successful processing
            polling_interval: Seconds to wait between polls if no messages are received
            max_polls: Maximum number of polling iterations (None for infinite)
            
        Returns:
            Total number of messages processed
            
        Raises:
            IntegrationException: If the receive operation fails
        """
        import time
        
        total_processed = 0
        poll_count = 0
        
        # Poll the queue until max_polls is reached (if specified)
        while max_polls is None or poll_count < max_polls:
            # Process messages from the queue
            processed = self.process(callback, auto_delete)
            total_processed += processed
            
            # If no messages were received, wait before polling again
            if processed == 0 and polling_interval > 0:
                time.sleep(polling_interval)
            
            # Increment poll counter
            poll_count += 1
        
        return total_processed