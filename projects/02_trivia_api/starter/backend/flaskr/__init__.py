import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category


# -------------------------------------------------------------------------------------
# db is an instance of our database that we can let interact with SQLAlchemy
# db comes from SQLAlchemy class that we had imported from the Flask SQLAlchemy library
# we use SQLAlchemy class to link to our Flask application. This links an instance of a database to a Flask app.
# -------------------------------------------------------------------------------------

db = SQLAlchemy()

# -------------------------------------------------------------------------------------
# Global variable: questions to be returned per page at a time
# -------------------------------------------------------------------------------------
QUESTIONS_PER_PAGE = 10

# -------------------------------------------------------------------------------------
# Create and configure the app
# -------------------------------------------------------------------------------------

def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

# -------------------------------------------------------------------------------------
# Cross Origin Resource Sharing (CORS) setup
# What origin from the client can access those resources (* means any origin)
# -------------------------------------------------------------------------------------

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app, resources={'/': {'origins': '*'}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''

# -------------------------------------------------------------------------------------
# Access-Control-Allow is a CORS header.
# The application tells the browser that it’s ok to receive requests from other origins: see above
# Define method that takes the response object as a parameter and add some headers to the response
# -------------------------------------------------------------------------------------


    @app.after_request
    def after_request(response):

        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response


# -------------------------------------------------------------------------------------
# We Flask paginate the results by using query parameters and request arguments
# We paginate to avoid sending huge sets of data at once — bad for speed
# We send back to the front end just the information the users need
# request.args is a Python dictionary
# off of the request object, look at the args object, and get the value of key page.
# if key does not exist, default to 1
# -------------------------------------------------------------------------------------

    def retrieve_paginated_questions (request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE # start with index zero
        end = start + QUESTIONS_PER_PAGE # ending index

        questions = [question.format() for question in selection]
        current_questions = questions[start:end] # instead of sending back all the questions, return start to end only

        return current_questions

# -------------------------------------------------------------------------------------
# GET requests endpoint for categories
# -------------------------------------------------------------------------------------

    '''
    @TODO: 
    Create an endpoint to handle GET requests 
    for all available categories.
    
    Request Parameters: None
    Returns: A JSON object 
    '''

    @app.route('/categories')
    def retrieve_all_categories():
        try:
            # frontend is expecting categories data in dict format with category id as key and type as value.
            categories = Category.query.all()
            categories_dict = {}
            for category in categories:
                categories_dict[category.id] = category.type

            response_object = {
                "success": True,
                "categories": categories_dict,
                "total_categories": len(categories) # keep pagination updated
            }

            return jsonify(response_object)

        except:
            import traceback
            traceback.print_exc()
            print(sys.exc_info())
            db.session.rollback()
            abort(500)

        finally:
            db.session.close()

# -------------------------------------------------------------------------------------
# GET requests endpoint for questions
# -------------------------------------------------------------------------------------

    '''
    @TODO: 
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 
      
    Request Parameters: An integer page number
    Returns: A JSON object
      
    
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''

    @app.route('/questions')
    def retrieve_questions():
        try:
            selection = Question.query.order_by(Question.id).all()
            questions = retrieve_paginated_questions(request, selection)

            categories = Category.query.order_by(Category.type).all()

            if len(questions) == 0:
                abort(404)
                print(len())

            response_object = {
                "success": True,
                "questions": questions,
                "total_questions": len(selection),
                "categories": {category.id: category.type for category in categories}, #list interpolation to format
                "current_category": None
            }

            return jsonify(response_object)

        except:
            import traceback
            traceback.print_exc()
            print(sys.exc_info())
            db.session.rollback()
            abort(500)

        finally:
            db.session.close()

# -----------------------------------------------------------
# DELETE question
# we want to delete just a specific question
# -----------------------------------------------------------

    '''
    @TODO: 
    Create an endpoint to DELETE question using a specific question ID. 
      
    Request Parameters: None
    Returns: A JSON object
    
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE']) # the variable question_id
    def delete_specific_question(question_id): #becomes a parameter of the method and returned as a string
        try:
            question_to_delete = Question.query.filter(Question.id == question_id).one_or_none()

            if question_to_delete is None:
                return unprocessable(422)

            question_to_delete.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = retrieve_paginated_questions(request, selection)

            db.session.delete(question_to_delete)
            db.session.commit()

            response_object = {
                "success": True,
                "deleted": question_id,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "message": f"The question with ID: {question_id} is now deleted."
            }

            return jsonify(response_object)

        except:
            import traceback
            traceback.print_exc()
            print(sys.exc_info())
            db.session.rollback()
            abort(500)

        finally:
            db.session.close()

# -----------------------------------------------------------
# Add a new question on DB - POST
# -----------------------------------------------------------

    '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.
  
  Request Parameters: None
  Returns: A JSON object

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            body = request.get_json() # get the body from the request
            # from the body we should be able to grab a question, an answer, a difficulty level and category
            # if any of them don't exist (nobody rated a question yet) we set this to None
            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_difficulty = body.get('difficulty', None)
            new_category = body.get('category', None)

            if (new_question == None) or (new_answer == None) or (new_category == None) or (new_difficulty == None):
                unprocessable(422)

            question_created = Question(
                question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)

            question_created.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = retrieve_paginated_questions(request, selection)

            # db.session.add(question_created)
            # db.session.commit()

            response_object = {
                "success": True,
                "question_created": question_created.id,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "message": f"The question: '{new_question}' is now added to Trivia"
            }

            return jsonify(response_object)


        except:
            import traceback
            traceback.print_exc()
            print(sys.exc_info())
            db.session.rollback()
            abort(500)

        finally:
            db.session.close()

# -----------------------------------------------------------
# Search a question from the DB - POST
# -----------------------------------------------------------

    '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  Request Parameters: None
  Returns: A JSON object

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        try:
            body = request.get_json()
            search_term = body.get('searchTerm', None)

            search_results = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            if len(search_results) == 0:
                abort(404)

            search_results_list = [question.format()
                                   for question in search_results]

            response_object = {
                "success": True,
                "questions": search_results_list,
                "current_category": None,
                "total_questions": len(search_results_list)
            }

            return jsonify(response_object)

        except:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            print(sys.exc_info())
            abort(500)

        finally:
            db.session.close()

# -----------------------------------------------------------
# Retrieve available questions for each category - GET
# -----------------------------------------------------------

    '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 
  
  Request Parameters: None
  Returns: A JSON object

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):

        try:
            questions = Question.query.filter(
                Question.category == str(category_id)).all()

            response_object = {
              "success": True,
              "questions": [question.format() for question in questions],
              "total_questions": len(questions),
              "category": category_id
            }

            return jsonify(response_object)

        except:
            import traceback
            traceback.print_exc()
            print(sys.exc_info())
            db.session.rollback()
            abort(500)

        finally:
            db.session.close()

# ------------------------------------------------------------------------------
# Play Quiz: returns a random question different from previous questions. - POST
# ------------------------------------------------------------------------------

    '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 
  
  Request Parameters: None
  Returns: A JSON object

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():

        try:
            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                unprocessable(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((previous_questions))).all()

            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            response_object = {
                  "success": True,
                  "question": new_question
                }

            return jsonify(response_object)

        except:
          import traceback
          traceback.print_exc()
          db.session.rollback()
          print(sys.exc_info())
          abort(500)

        finally:
          db.session.close()

    # -----------------------------------------------------------
    # Error Handlers
    # -----------------------------------------------------------

    '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''

    # Malformed request
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request."
        }), 400

    # Item not found in DB
    @app.errorhandler(404)
    def abort(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found."
        }), 404

    # Request not processable
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    # Server issue.
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error."
        }), 500

    # Method Not Allowed.
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method Not Allowed"
        }), 405

    return app
