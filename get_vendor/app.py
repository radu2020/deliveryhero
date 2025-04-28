import boto3
import json
from decimal import Decimal
from aws_lambda_powertools import Logger, Metrics, Tracer

# Initialize AWS Lambda Powertools
logger = Logger()
metrics = Metrics()
tracer = Tracer()

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
vendors_table = dynamodb.Table('Vendors')
incentives_table = dynamodb.Table('Incentives')

# Custom JSON Encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Lambda handler with tracing and logging
@tracer.capture_lambda_handler
@logger.inject_lambda_context  # Automatically adds Lambda context to logs
def lambda_handler(event, context):
    vendor_id = event['pathParameters']['vendor_id']

    logger.info(f"Fetching vendor and incentive data for vendor_id: {vendor_id}")

    try:
        # Get vendor and incentive from DynamoDB
        vendor = vendors_table.get_item(Key={'vendor_id': vendor_id}).get('Item')
        incentive = incentives_table.get_item(Key={'vendor_id': vendor_id}).get('Item')

        # If vendor not found, return 404
        if not vendor:
            logger.error(f"Vendor with vendor_id {vendor_id} not found")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Vendor not found'}),
            }

        # Merge the vendor and incentive data
        result = {**vendor, **(incentive or {})}

        # Log the result of the successful fetch
        logger.info(f"Successfully fetched data for vendor_id {vendor_id}")

        # Emit success metric
        metrics.add_metric(name="VendorFetchSuccess", unit="Count", value=1)

        # Return the result, converting Decimal to float using custom encoder
        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder),
            'headers': {
                "Access-Control-Allow-Origin": "http://localhost:8000",
                "Access-Control-Allow-Headers": "Content-Type, x-api-key"
            },
        }


    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        metrics.add_metric(name="VendorFetchFailed", unit="Count", value=1)

        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error', 'message': str(e)}),
        }
