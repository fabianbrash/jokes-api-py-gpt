from flask import Flask, request
from flask_restful import Resource, Api
from azure.cosmos import CosmosClient
import uuid
import configparser

# Initialize Flask app and CosmosDB client
app = Flask(__name__)
api = Api(app)

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Get CosmosDB credentials from the config file
COSMOSDB_ENDPOINT = config.get('CosmosDB', 'endpoint')
COSMOSDB_KEY = config.get('CosmosDB', 'key')
DATABASE_ID = config.get('CosmosDB', 'database_id')
CONTAINER_ID = config.get('CosmosDB', 'container_id')

# Create CosmosDB client
cosmos_client = CosmosClient(COSMOSDB_ENDPOINT, COSMOSDB_KEY)
database = cosmos_client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

# API Resource for jokes
class JokesResource(Resource):
    def get(self):
        # Retrieve jokes from CosmosDB
        query = 'SELECT * FROM c'
        items = list(container.query_items(query, enable_cross_partition_query=True))

        jokes = []
        for item in items:
            joke = {
                'id': item['id'],
                'joke': item['joke'],
                'punchline': item['punchline'],  # Include 'punchline' in the response
                'author': item['author'],
                'year': item['year']
            }
            jokes.append(joke)

        return jokes

    def post(self):
        # Add new joke to CosmosDB with auto-generated ID
        data = request.get_json()
        new_joke = {
            'id': str(uuid.uuid4()),
            'joke': data['joke'],
            'punchline': data['punchline'],  # Include 'punchline' in the request
            'author': data['author'],
            'year': data['year']
        }
        container.create_item(body=new_joke)

        return {'message': 'Joke added successfully'}, 201

# Add resource to the API
api.add_resource(JokesResource, '/jokes')

if __name__ == '__main__':
    app.run(debug=True)
