import json
import requests
import boto3
from datetime import datetime

# Initialize S3 client
s3 = boto3.client('s3')

# Configuration
BUCKET_NAME = "flights-buckets"
API_URL = "https://api.aviationstack.com/v1/flights"
ACCESS_KEY = "25048d22a4850c738ff4a7bb06ad6e89"  # Your access key

def lambda_handler(event, context):
    try:
        # Fetch current date for partitioning
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Initialize pagination parameters
        limit = 100  # Number of results per request
        offset = 0   # Starting point for pagination
        all_flights = []  # List to store all flights data
        max_records = 500  # Max number of records we want to fetch

        # Loop to fetch data until we reach 500 records
        while len(all_flights) < max_records:
            # Construct the API URL with pagination
            url = f"{API_URL}?access_key={ACCESS_KEY}&limit={limit}&offset={offset}"

            # Make the API request
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"API call failed with status code {response.status_code}")

            # Parse the JSON response
            data = response.json()
            flights = data.get('data', [])

            if not flights:
                break  # Exit if no more data is available

            # Add the flights data to the list
            all_flights.extend(flights)

            # If we already have 500 records, stop fetching more
            if len(all_flights) >= max_records:
                all_flights = all_flights[:max_records]  # Limit to 500 records
                break

            # Update the offset for the next batch
            offset += limit

       

        # Prepare the S3 key with today's date
        s3_key = f"flights_data/date={current_date}/data.json"

        # Upload the flight data to S3 as a single JSON object
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(all_flights),  # Uploading data as a JSON object
            ContentType='application/json'
        )

        return {
            'statusCode': 200,
            'body': f"Data for {current_date} successfully uploaded to {s3_key}"
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
