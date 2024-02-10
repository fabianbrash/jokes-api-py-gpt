from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from azure.cosmos import CosmosClient
from flasgger import Swagger, swag_from
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import uuid
import configparser

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Get CosmosDB credentials from the config file
DATABASE_ID = config.get('CosmosDB', 'database_id')
CONTAINER_ID = config.get('CosmosDB', 'container_id')
USER_ID = config.get('jwt', 'user')
PWD = config.get('jwt', 'password')
JWT_SECRET_ID = config.get('jwt', 'jwt_secret_id')

# Azure Key Vault Configuration
KEY_VAULT_URL = "https://wus-app-kv.vault.azure.net/"
#KEY_VAULT_CLIENT_ID = JOKE_API_CLIENT_ID

app = Flask(__name__)
api = Api(app)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_ID  # Change this to a secure secret key

# Set the expiration time for access tokens (in seconds)
# the default is 15 minutes or 900 seconds
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800  # 30 minutes
jwt = JWTManager(app)

# Swagger configuration
app.config['SWAGGER'] = {
    'title': 'Joke API',
    'uiversion': 3,
}

swagger = Swagger(app)

# Use DefaultAzureCredential
# We are using a system managed account here
credential = DefaultAzureCredential()

# Use DefaultAzureCredential with explicit client ID and client secret
# use the below if you are using a user created managed account
#credential = DefaultAzureCredential(
#    client_id=KEY_VAULT_CLIENT_ID,
#    client_secret=JOKE_API_CLIENT_SECRET
#)

# Create a Key Vault SecretClient
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

# Get secrets from Key Vault
cosmosdb_endpoint = secret_client.get_secret("wus-cosmo-endpoint").value
cosmosdb_key = secret_client.get_secret("wus-cosmo-write-key").value


# Initialize Flask app and CosmosDB client
#app = Flask(__name__)
#api = Api(app)

# Create CosmosDB client
#cosmos_client = CosmosClient(COSMOSDB_ENDPOINT, COSMOSDB_KEY)
#database = cosmos_client.get_database_client(DATABASE_ID)
#container = database.get_container_client(CONTAINER_ID)

# Create CosmosDB client
cosmos_client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
database = cosmos_client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

#Swagger Docs are here
# http(s)://{URL_OR_IP}:{PORT(OPTIONAL)}/apidocs/

# API Resource for jokes
class JokeResource(Resource):
    @swag_from('swagger_doc/get_jokes.yml')  # Reference to Swagger documentation
    def get(self):
        """Endpoint to get jokes."""
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
    @swag_from('swagger_doc/post_joke.yml')  # Reference to Swagger documentation
    def post(self):
        """Endpoint to add a new joke."""
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
    @swag_from('swagger_doc/login.yml')  # Reference to Swagger documentation
    def post(self):
        """Endpoint to obtain a JWT token by providing valid credentials."""
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