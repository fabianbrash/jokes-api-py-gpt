from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from azure.cosmos import CosmosClient
import uuid
import configparser


# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Get CosmosDB credentials from the config file
COSMOSDB_ENDPOINT = config.get('CosmosDB', 'endpoint')
COSMOSDB_KEY = config.get('CosmosDB', 'key')
DATABASE_ID = config.get('CosmosDB', 'database_id')
CONTAINER_ID = config.get('CosmosDB', 'container_id')
USER_ID = config.get('jwt', 'user')
PWD = config.get('jwt', 'password')
JWT_SECRET_ID = config.get('jwt', 'jwt_secret_id')


app = Flask(__name__)
api = Api(app)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_ID  # Change this to a secure secret key
jwt = JWTManager(app)

# Initialize Flask app and CosmosDB client
#app = Flask(__name__)
#api = Api(app)

# Create CosmosDB client
cosmos_client = CosmosClient(COSMOSDB_ENDPOINT, COSMOSDB_KEY)
database = cosmos_client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

# API Resource for jokes
class JokeResource(Resource):
    def get(self):
        query = 'SELECT * FROM c'
        items = list(container.query_items(query, enable_cross_partition_query=True))

        jokes = []
        for item in items:
            joke = {
                'id': item['id'],
                'joke': item['joke'],
                'punchline': item['punchline'],
                'author': item['author'],
                'year': item['year']
            }
            jokes.append(joke)

        return jokes

    @jwt_required()
    def post(self):
        data = request.get_json()
        new_joke = {
            'id': str(uuid.uuid4()),
            'joke': data['joke'],
            'punchline': data['punchline'],
            'author': data['author'],
            'year': data['year']
        }
        container.create_item(body=new_joke)
        return {'message': 'Joke added successfully'}, 201

class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Check username and password (implement your own logic)

        # If credentials are valid, create and return a JWT token
        if username == USER_ID and password == PWD:
            access_token = create_access_token(identity=username)
            response_data = jsonify({'access_token': access_token})
            print("ACCESS TOKEN:", access_token)
            response_data.status_code = 200
            return (response_data)
            #return jsonify(response_data), 200
        else:
            response_data = jsonify({'msg': 'Invalid credentials'})
            print("INVALID CREDENTIALS...")
            response_data.status_code = 401
            return (response_data)
            #return jsonify(response_data), 401

api.add_resource(JokeResource, '/jokes')
api.add_resource(LoginResource, '/login')

if __name__ == '__main__':
    app.run(debug=True)