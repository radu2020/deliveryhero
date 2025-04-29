import boto3
import json
import uuid
from aws_lambda_powertools import Logger, Metrics, Tracer

# Initialize Lambda Powertools
logger = Logger()
metrics = Metrics()
tracer = Tracer()

# Set up DynamoDB resources
dynamodb = boto3.resource('dynamodb')
vendors_table = dynamodb.Table('Vendors')
incentives_table = dynamodb.Table('Incentives')

# Lambda handler with tracing and logging
@tracer.capture_lambda_handler
@logger.inject_lambda_context  # Adds Lambda context to logs automatically
def lambda_handler(event, context):
    try:
        # Log incoming event for tracking
        logger.info("Received event", extra={"event": event})

        # Check if the HTTP method is OPTIONS (preflight request)
        if event['httpMethod'] == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    "Access-Control-Allow-Origin": "http://localhost:8000",
                    'Access-Control-Allow-Headers': 'Content-Type, x-api-key',
                }
            }

        # Parse the request body
        body = json.loads(event['body'])
        
        vendor_id = str(uuid.uuid4())

        # Log generated vendor ID for tracking
        logger.info(f"Generated vendor_id: {vendor_id}")

        # Prepare data for DynamoDB
        vendor_data = {
            'vendor_id': vendor_id,
            'vendor_name': body['vendor_name'],
            'key_account': body['key_account'],
            'region': body.get('region'),
            'industry': body.get('industry'),
            'contact_email': body.get('contact_email')
        }

        incentive_data = {
            'vendor_id': vendor_id,
            'available_discount': body['available_discount'],
            'discount_type': body.get('discount_type'),
            'discount_expiry_date': body.get('discount_expiry_date')
        }

        # Insert data into DynamoDB
        vendors_table.put_item(Item=vendor_data)
        incentives_table.put_item(Item=incentive_data)

        # Log success
        logger.info("Successfully added vendor and incentive data.")

        # Track the successful operation
        metrics.add_metric(name="VendorIncentiveCreated", unit="Count", value=1)

        # Return success response
        return {
            'statusCode': 201,
            'body': json.dumps({'vendor_id': vendor_id}),
            'headers': {
                "Access-Control-Allow-Origin": "http://localhost:8000",
                "Access-Control-Allow-Headers": "Content-Type, x-api-key"
            },
        }

    except KeyError as e:
        # Handle missing fields in input
        logger.error(f"Missing field: {str(e)}", exc_info=True)
        metrics.add_metric(name="VendorIncentiveCreationFailed", unit="Count", value=1)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Missing required field: {str(e)}"}),
        }

    except Exception as e:
        # Catch other unexpected errors
        logger.error(f"Error: {str(e)}", exc_info=True)
        metrics.add_metric(name="VendorIncentiveCreationFailed", unit="Count", value=1)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error', 'message': str(e)}),
        }
