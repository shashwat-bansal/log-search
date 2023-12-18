import logging

import jwt
from flask import Flask, request, jsonify
import boto3
import os
import datetime
import re

from config import Config

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_PER_PAGE = 10  # Adjust this based on your requirements


def get_log_source():
    return app.config.get('LOG_SOURCE', 'local')


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=app.config['AWS_ACCESS_KEY'],
        aws_secret_access_key=app.config['AWS_SECRET_KEY'],
        region_name=app.config['AWS_REGION']
    )


def get_local_log_file_path(date, hour):
    return os.path.join(Config.LOCAL_LOG_PATH, date, f"{hour:02d}.txt")


@app.route('/search-logs', methods=['POST'])
def search_logs():
    try:
        search_keyword = request.json.get('searchKeyword')
        from_timestamp = request.json.get('from')
        to_timestamp = request.json.get('to')
        page = int(request.args.get('page', 1))

        response_data = list(search_logs_iter(search_keyword, from_timestamp, to_timestamp))

        paginated_data = paginate_data(response_data, page)

        response_metadata = {
            "responseCode": 200,
            "responseStatus": "OK",
            "errorCode": None,
            "errorMessage": None,
            "resultSize": len(response_data),
        }

        return jsonify({"metadata": response_metadata, "result": paginated_data}), 200

    except Exception as e:
        logger.error(f"Error in search_logs: {str(e)}")
        response_metadata = {
            "responseCode": 500,
            "responseStatus": "Internal Server Error",
            "errorCode": "SERVER_ERROR",
            "errorMessage": "An internal server error occurred.",
            "resultSize": 0,
        }
        return jsonify({"metadata": response_metadata, "result": []}), 500


def search_logs_iter(search_keyword, from_timestamp, to_timestamp):
    date_range = get_date_range(from_timestamp.split(' ')[0], to_timestamp.split(' ')[0])
    for date in date_range:
        for hour in range(24):
            if get_log_source() == 's3':
                file_key = f"{date}/{hour:02d}.txt"
                try:
                    obj = get_s3_client().get_object(Bucket=app.config['S3_BUCKET_NAME'], Key=file_key)
                    contents = obj['Body'].iter_lines()
                    matching_lines = (
                        line.decode('utf-8') for line in contents
                        if is_line_in_timestamp_range(line.decode('utf-8'), from_timestamp, to_timestamp)
                           and search_keyword in line.decode('utf-8')
                    )
                    yield from matching_lines
                except get_s3_client().exceptions.NoSuchKey:
                    logger.warning(f"File not found in S3: {file_key}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading file from S3 {file_key}: {str(e)}")
            elif get_log_source() == 'local':
                file_path = get_local_log_file_path(date, hour)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        contents = file.readlines()
                        matching_lines = (
                            line.strip() for line in contents
                            if is_line_in_timestamp_range(line, from_timestamp, to_timestamp)
                               and search_keyword in line
                        )
                        yield from matching_lines
                except FileNotFoundError:
                    logger.warning(f"File not found locally: {file_path}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading local file {file_path}: {str(e)}")


def is_line_in_timestamp_range(line, from_timestamp, to_timestamp):
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    match = re.match(timestamp_pattern, line)
    if match:
        log_timestamp = datetime.datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S")
        from_datetime = datetime.datetime.strptime(from_timestamp, "%Y-%m-%d %H:%M:%S")
        to_datetime = datetime.datetime.strptime(to_timestamp, "%Y-%m-%d %H:%M:%S")
        return from_datetime <= log_timestamp <= to_datetime
    return False


def paginate_data(data, page):
    start_index = (page - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    return list(data)[start_index:end_index]


def get_date_range(from_date, to_date):
    start_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
    date_range = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    return [date.strftime("%Y-%m-%d") for date in date_range]


if __name__ == "__main__":
    app.run(debug=True)
