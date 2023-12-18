This Flask application provides a RESTful API for searching log lines based on search criteria.

### Prerequisites

- Python 3.x
- Flask (install via `pip install Flask`)
- (Optional) Boto3 for AWS S3 integration (install via `pip install boto3`)


1. Clone the repository
2. Install dependencies:
   `pip install -r requirements.txt`

   
# Usage
Endpoints
- Log Search:
  - URL: /search-logs
  - Method: POST
  - Content-Type: application/json
  - Request Body:
    `{
      "searchKeyword": "keyword",
      "from": "2023-01-01 00:00:00",
      "to": "2023-01-01 23:59:59"
    }`
  - Response body:
    `{
     "result": [
       "2023-01-01 00:05:10 - Log entry 1",
       "2023-01-01 00:15:25 - Log entry 2",
       "2023-01-01 00:30:45 - Log entry 3"
     ],
     "metadata": {
      "responseCode": 200,
      "responseStatus": "OK",
      "errorCode": None,
      "errorMessage": None,
      "resultSize": 3,
     }
   }`

# Start the Flask application
python run.py

# Sample curl:
- curl -X POST -H "Content-Type: application/json" -d '{"searchKeyword": "Log", "from": "2023-11-01 00:00:00", "to": "2023-11-30 00:00:00"}' http://127.0.0.1:5000/search-logs
- curl -X POST -H "Content-Type: application/json" -d '{"searchKeyword": "Log", "from": "2023-11-25 00:30:00", "to": "2023-11-26 00:15:00"}' http://127.0.0.1:5000/search-logs


