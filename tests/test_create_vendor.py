import json
import pytest
from unittest.mock import MagicMock
from moto import mock_aws
import boto3
from create_vendor.app import lambda_handler as create_vendor_handler


TABLE_VENDOR = "Vendors"
TABLE_INCENTIVE = "Incentives"


@pytest.fixture(autouse=True)
def setup_dynamodb():
    # Mock DynamoDB using moto
    with mock_aws():
        # Setup DynamoDB tables
        dynamodb = boto3.resource("dynamodb")
        dynamodb.create_table(
            TableName=TABLE_VENDOR,
            KeySchema=[{"AttributeName": "vendor_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "vendor_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName=TABLE_INCENTIVE,
            KeySchema=[{"AttributeName": "vendor_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "vendor_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


def mock_lambda_context():
    """Mocking the Lambda context."""
    mock_context = MagicMock()
    mock_context.function_name = "test_create_vendor_function"
    mock_context.memory_limit_in_mb = 128
    mock_context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:test_create_vendor_function"
    )
    mock_context.aws_request_id = "test-create-vendor-request-id"
    return mock_context


def test_create_vendor_201_success():
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "vendor_name": "TestCorp",
                "key_account": True,
                "region": "USA",
                "industry": "Tech",
                "contact_email": "test@example.com",
                "available_discount": 20,
                "discount_type": "percentage",
                "discount_expiry_date": "2025-12-31",
            }
        ),
    }

    # Mock the context
    mock_context = mock_lambda_context()

    # Call the Lambda handler
    response = create_vendor_handler(test_event, mock_context)
    body = json.loads(response["body"])

    # Assertions
    assert response["statusCode"] == 201
    assert isinstance(body, dict)
    assert "vendor_id" in body
    assert isinstance(body["vendor_id"], str)
    assert len(body["vendor_id"]) > 0


def test_create_vendor_400_missing_field():
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "vendor_name": "TestCorp"
                # missing required fields like key_account, etc.
            }
        ),
    }

    # Mock the context
    mock_context = mock_lambda_context()

    # Call the Lambda handler
    response = create_vendor_handler(test_event, mock_context)
    body = json.loads(response["body"])

    # Assertions
    assert response["statusCode"] == 400
    assert "Missing required field" in body["error"]
