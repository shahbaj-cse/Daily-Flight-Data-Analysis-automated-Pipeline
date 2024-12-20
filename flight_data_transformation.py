import json
import boto3
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta

# Initialize S3 client
s3 = boto3.client('s3')

# Configuration
SOURCE_BUCKET = "flights-buckets"
DESTINATION_BUCKET = "processed-flights-buckets"

def lambda_handler(event, context):
    try:
        # Fetch current date for fetching today's data
        current_date = datetime.now().strftime("%Y-%m-%d")
        source_key = f"flights_data/date={current_date}/data.json"
        destination_key = f"processed_flights_data/date={current_date}/processed_data.csv"

        # Fetch data from S3
        response = s3.get_object(Bucket=SOURCE_BUCKET, Key=source_key)
        raw_data = response['Body'].read().decode('utf-8')
        flights_data = json.loads(raw_data)

        # Transform the data into a structured format
        
        df = pd.DataFrame(columns = ['flight_date', 'departure_airport', 'departure_iata', 'departure_delay','departure_scheduled', \
                             'departure_actual', 'arrival_airport', 'arrival_iata', 'arrival_delay', 'arrival_scheduled', 'arrival_actual',\
                             'flight_number', 'flight_iata'])
                             
        
        for i in flights_data:
            
            flight_date = i['flight_date']
            departure_airport = i['departure']['airport']
            departure_iata = i['departure']['iata']
            departure_delay = i['departure']['delay']
            departure_scheduled = i['departure']['scheduled']
            departure_actual = i['departure']['actual']
            
            arrival_airport = i['arrival']['airport']
            arrival_iata = i['arrival']['iata']
            arrival_delay = i['arrival']['delay']
            arrival_scheduled = i['arrival']['scheduled']
            arrival_actual = i['arrival']['actual']
            
            flight_number = i['flight']['number']
            flight_iata = i['flight']['iata']

            
            new_row = pd.DataFrame({
            'flight_date' : [flight_date],
            'departure_airport' : [departure_airport],
            'departure_iata' : [departure_iata],
            'departure_delay' : [departure_delay],
            'departure_scheduled' : [departure_scheduled],
            'departure_actual' : [departure_actual],
            
            'arrival_airport' : [arrival_airport],
            'arrival_iata' : [arrival_iata],
            'arrival_delay' : [arrival_delay],
            'arrival_scheduled' : [arrival_scheduled],
            'arrival_actual' : [arrival_actual],
            
            'flight_number' : [flight_number],
            'flight_iata' : [flight_iata]
            })
    
            df = pd.concat([df, new_row], ignore_index=True)   
            
        # data transformation
        
        # Convert columns to numeric first, handle NaNs, and then convert to int
        df['departure_delay'] = pd.to_numeric(df['departure_delay'], errors='coerce').fillna(0).astype(int)
        df['arrival_delay'] = pd.to_numeric(df['arrival_delay'], errors='coerce').fillna(0).astype(int)

        
        df['flight_date'] = pd.to_datetime(df['flight_date'])
        df['departure_scheduled'] = pd.to_datetime(df['departure_scheduled'])
        df['arrival_scheduled'] = pd.to_datetime(df['arrival_scheduled'])
        
        df['departure_actual'] = pd.to_datetime(df['departure_actual'])
        df['arrival_actual'] = pd.to_datetime(df['arrival_actual'])
        
        df['flight_number'] = df['flight_number'].fillna(0).astype(int)
        
        
        df['year'] = df['flight_date'].dt.year
        df['month'] = df['flight_date'].dt.month
        df['day'] = df['flight_date'].dt.day

        
        # Convert DataFrame to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        
        # Upload the processed data to the destination S3 bucket
        s3.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=destination_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )

        
        return {
            'statusCode': 200,
            'body': f"Processed data for {current_date} successfully uploaded to {destination_key}"
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
