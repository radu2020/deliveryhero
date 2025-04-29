import json
import pytest
from moto import mock_aws
import boto3
from decimal import Decimal
from unittest.mock import MagicMock

TABLE_VENDOR = "Vendors"
TABLE_INCENTIVE = "Incentives"


@pytest.fixture(autouse=True)
def setup_dynamodb():
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb')

        # Create tables
        vendor_table = dynamodb.create_table(
            TableName=TABLE_VENDOR,
            KeySchema=[{'AttributeName': 'vendor_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'vendor_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        incentive_table = dynamodb.create_table(
            TableName=TABLE_INCENTIVE,
            KeySchema=[{'AttributeName': 'vendor_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'vendor_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Wait for table creation
        vendor_table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_VENDOR)
        incentive_table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_INCENTIVE)

        # Insert mock data
        vendor_table.put_item(Item={
            "vendor_id": "123",
            "vendor_name": "TestVendor",
            "key_account": True,
            "region": "USA",
            "industry": "Retail",
            "contact_email": "test@vendor.com"
        })
        incentive_table.put_item(Item={
            "vendor_id": "123",
            "available_discount": Decimal("25.5"),
            "discount_type": "flat",
            "discount_expiry_date": "2025-12-31"
        })

        # Import inside the mock context
        global get_vendor_handler
        from get_vendor.app import lambda_handler as get_vendor_handler

        yield


def mock_lambda_context():
    """Mocking the Lambda context."""
    mock_context = MagicMock()
    mock_context.function_name = "test_function"
    mock_context.memory_limit_in_mb = 128
    mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
    mock_context.aws_request_id = "test-request-id"
    return mock_context


def test_get_vendor_200_success():
    # Mock event for a successful vendor fetch
    test_event = {
        "httpMethod": "GET",
        "pathParameters": {"vendor_id": "123"}
    }

    # Mock the context
    mock_context = mock_lambda_context()

    # Call the Lambda handler
    response = get_vendor_handler(test_event, mock_context)
    body = json.loads(response['body'])

    # Assertions
    assert response['statusCode'] == 200
    assert body['vendor_name'] == "TestVendor"
    assert body['available_discount'] == 25.5


def test_get_vendor_404_not_found():
    # Mock event for vendor not found
    test_event = {
        "httpMethod": "GET",
        "pathParameters": {"vendor_id": "nonexistent"}
    }
    
    # Mock the context
    mock_context = mock_lambda_context()

    # Call the Lambda handler
    response = get_vendor_handler(test_event, mock_context)
    body = json.loads(response['body'])

    # Assertions
    assert response['statusCode'] == 404
    assert "Vendor not found" in body['error']
