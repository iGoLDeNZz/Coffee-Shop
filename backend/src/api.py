import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()


  # ------------------ 
  # MARK: Endpoints
  # ------------------ 

'''
    endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def get_short_drinks():

    return jsonify({'success': True, 'drinks': [d.short() for d in Drink.query.all()]})


'''
    endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_detailed_drinks(payload):
    
    return jsonify({'success': True, 'drinks': [d.long() for d in Drink.query.all()]})


'''
    endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(payload):

    title = request.json.get('title', None)
    recipe = request.json.get('recipe', None)

    drink_from_db = Drink.query.filter(Drink.title == title).one_or_none()

    if drink_from_db is not None:
        abort(409)
    
    if title is None or recipe is None:
        abort(400)
    
    new_drink = Drink(title=title, recipe=json.dumps(recipe))
    new_drink.insert()

    return jsonify({
    'success': True,
    'drinks': new_drink.long()
    })



'''
    endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):

    drink = Drink.query.get(drink_id)

    if drink is None:
        abort(404)

    current_drink_info = drink.long()

    recipe = request.json.get('recipe', current_drink_info['recipe'])
    drink.title = request.json.get('title', current_drink_info['title'])
    drink.recipe = json.dumps(recipe)
    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })

'''
    endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):

    drink = Drink.query.get(drink_id)

    if drink is None:
        abort(404)

    drink.delete()
    return jsonify({
        'success': True,
        'delete': drink_id
    })


  # ------------------ 
  # MARK: Error handlers
  # ------------------ 

def get_error_message(error, default_text):
    '''Returns default error text or custom error message (if not applicable)
    *Input:
        * <error> system generated error message which contains a description message
        * <string> default text to be used as error message if Error has no specific message
    *Output:
        * <string> specific error message or default text(if no specific message is given)
    '''
    try:
        # Return message contained in error, if possible
        return error['description']
    except TypeError:
        # otherwise, return given default text
        return default_text


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": get_error_message(error, "bad request")
      }), 400


'''
    error handler for AuthError
'''
@app.errorhandler(AuthError)
def unautherized(error):
    return jsonify({
                    "success": False, 
                    "error": error.status_code,
                    "message": get_error_message(error.error,"Unautherized")
                    }), error.status_code



@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": get_error_message(error,"resource not found")
                    }), 404



@app.errorhandler(409)
def conflict(error):
    return jsonify({
                    "success": False, 
                    "error": 409,
                    "message": get_error_message(error,"Resourse already exists.")
                    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": get_error_message(error,"unprocessable")
                    }), 422