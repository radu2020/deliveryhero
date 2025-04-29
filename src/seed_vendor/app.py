import boto3
import uuid
import random
import datetime
from aws_lambda_powertools import Logger

# Initialize AWS Lambda Powertools components
logger = Logger()

# Setup DynamoDB
dynamodb = boto3.resource("dynamodb")
vendors_table = dynamodb.Table("Vendors")
incentives_table = dynamodb.Table("Incentives")

# Predefined list of sample company names, regions, industries for random generation
COMPANY_NAMES = [
    "TechCorp",
    "Innovative Solutions",
    "Global Ventures",
    "NextGen Solutions",
    "BusinessCo",
]
COUNTRIES = ["USA", "Canada", "UK", "Germany", "France"]
INDUSTRIES = ["Technology", "Healthcare", "Finance", "Retail", "Education"]
EMAIL_DOMAINS = [
    "example.com",
    "techcorp.com",
    "innovations.com",
    "ventures.com",
    "nextgen.com",
]


def random_discount_type():
    return random.choice(["percentage", "flat"])


def random_company_name():
    return random.choice(COMPANY_NAMES)


def random_country():
    return random.choice(COUNTRIES)


def random_industry():
    return random.choice(INDUSTRIES)


def random_email():
    return f"{random_string(10)}@{random.choice(EMAIL_DOMAINS)}"


def random_string(length=10):
    return "".join(
        random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=length)
    )


def create_vendor_record():
    return {
        "vendor_id": str(uuid.uuid4()),
        "vendor_name": random_company_name(),
        "key_account": random.choice([True, False]),
        "region": random_country(),
        "industry": random_industry(),
        "contact_email": random_email(),
    }


def create_incentive_record(vendor_id):
    return {
        "vendor_id": vendor_id,
        "available_discount": int(round(random.uniform(5, 30), 0)),
        "discount_type": random_discount_type(),
        "discount_expiry_date": random_date_in_future(),
    }


def random_date_in_future():
    # Random date between today and the next 1 year
    today = random.randint(1, 365)
    future_date = (datetime.datetime.now() + datetime.timedelta(days=today)).date()
    return future_date.isoformat()


def seed_data(count):
    vendors = []
    incentives = []

    for _ in range(count):
        vendor = create_vendor_record()
        vendors.append(vendor)
        incentives.append(create_incentive_record(vendor["vendor_id"]))

    with vendors_table.batch_writer(overwrite_by_pkeys=["vendor_id"]) as batch:
        for vendor in vendors:
            batch.put_item(Item=vendor)

    with incentives_table.batch_writer(overwrite_by_pkeys=["vendor_id"]) as batch:
        for incentive in incentives:
            batch.put_item(Item=incentive)

    logger.info(f"Seeded {count} vendors and incentives.")


@logger.inject_lambda_context  # Ensure Lambda context is always in the logs
def lambda_handler(event, context):
    count = event.get("count", 100)  # Default to 100 if not provided
    logger.info(f"Starting seeding with {count} records...")

    try:
        seed_data(count)
        return {"statusCode": 200, "body": f"Seeded {count} records successfully."}

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return {"statusCode": 500, "body": f"Error seeding data: {str(e)}"}
