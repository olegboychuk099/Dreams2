from flask import Flask, jsonify, request, json, redirect
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt, decode_token, get_current_user)

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'meanloginreg'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/meanloginreg'
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

CORS(app)
REFS = {'REGISTER': '/users/register',
        'LOGIN': '/users/login',
        'DREAM': '/users/dream-register',
        'PAYMENT': '/users/payment',
        'HOME': '/users/home'}

# class InvalidUsage(Exception):
#     status_code = 400
#
#     def init(self, message, status_code=None, payload=None):
#         Exception.init(self)
#         self.message = message
#         if status_code is not None:
#             self.status_code = status_code
#         self.payload = payload
#
#     def to_dict(self):
#         rv = dict(self.payload or ())
#         rv['message'] = self.message
#         return rv
#
#
# @app.errorhandler(InvalidUsage)
# def handle_invalid_usage(error):
#     response = jsonify(error.to_dict())
#     response.status_code = error.status_code
#     return response


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


@app.route(REFS['REGISTER'], methods=['POST'])
def register():
    users = mongo.db.users
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    phone_number = request.get_json()['phone_number']
    password = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')
    wish_created = 'false'
    # created = datetime.utcnow()

    response = users.find_one({'email': email})
    if response:
        return jsonify(message="User Already Exist"), 409

    user_id = users.insert({
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone_number': phone_number,
        'password': password,
        'wish_created': wish_created
    })
    new_user = users.find_one({'_id': user_id})
    if new_user:
        json_id = JSONEncoder().encode(user_id)
        token_created = datetime.utcnow()
        access_token = create_access_token(identity={
            '_id': json_id,
            'token_created': token_created
        })

        return jsonify({
            'token' : access_token,
            'expiresIn' : token_created + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }), 201
    return jsonify(message="Some problems with adding new User"), 409


@app.route(REFS['LOGIN'], methods=['POST'])
def login():
    users = mongo.db.users
    email = request.get_json()['email']
    password = request.get_json()['password']

    response = users.find_one({'email': email})

    if response:
        if bcrypt.check_password_hash(response['password'], password):
            json_id = JSONEncoder().encode(response['_id'])
            token_created = datetime.utcnow()
            access_token = create_access_token(identity={
                '_id': json_id,
                'token_created': token_created + app.config['JWT_ACCESS_TOKEN_EXPIRES']
            })
            result = jsonify({'token': access_token}), 200
            # result = redirect(REFS['DREAM'])
        else:
            result = jsonify({"error": "Invalid username or password"}), 422
    else:
        result = jsonify({"result": "No results found"}), 422
    return result


@app.route(REFS['DREAM'], methods=['POST'])
@jwt_required
def dream_register():
    dreams = mongo.db.dreams

    title = request.get_json()['title']
    description = request.get_json()['description']
    price = request.get_json()['price']
    number_of_likes = 0
    is_active = 'false'

    user_id = get_jwt_identity()['_id']

    dream_id = dreams.insert({
        'title': title,
        'description': description,
        'price': price,
        'number_of_likes': number_of_likes,
        'is_active': is_active,
        'author': user_id
    })

    new_dream = dreams.find_one({'_id': dream_id})
    if new_dream:
        return jsonify(message="Dream added sucessfully"), 201

    return jsonify(message="Some problems with adding new Dream"), 409


if __name__ == '__main__':
    app.run(debug=True)
