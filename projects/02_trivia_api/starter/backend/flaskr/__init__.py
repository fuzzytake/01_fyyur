import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

db = SQLAlchemy()

# Global variable: questions to be returned per page
QUESTIONS_PER_PAGE = 10


# -------------------------------------------------------------------------------------
# Questions' pagination
# -------------------------------------------------------------------------------------

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # -------------------------------------------------------------------------------------
    # Cross Origin Resource Sharing (CORS) setup
    # -------------------------------------------------------------------------------------

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, resources={'/': {'origins': '*'}})

    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''

    # Returns the response object after adding Access-Control headers at each request

    @app.after_request
    def after_request(response):

        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # -------------------------------------------------------------------------------------
    # GET requests endpoint
    # -------------------------------------------------------------------------------------

    '''
    @TODO: 
    Create an endpoint to handle GET requests 
    for all available categories.
    
    Request Parameters: None
    Returns: A JSON object 
  '''

    @app.route('/categories')
    def retrieve_categories():
        try:
            categories = retrieve_categories()

            response_object = {
                "success": True,
                "categories": categories,
                "total_categories": len(categories)
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
            questions = retrieve_questions()

            questions_list = []

            if len(questions) == 0:
                return not_found(404)

            for question in questions:
                questions_list.append(question.format())
            questions_list

            response_object = {
                "success": True,
                "questions": questions_list,
                "total_questions": len(questions_list),
                "categories": retrieve_categories(),
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
# -----------------------------------------------------------

    '''
  @TODO: 
  Create an endpoint to DELETE question using a specific question ID. 
  
  Request Parameters: None
  Returns: A JSON object

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question_to_delete = Question.query.get(question_id)

            if question_to_delete is None:
                return not_found(404)

            db.session.delete(question_to_delete)
            db.session.commit()

            response_object = {
                "success": True,
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
            body = request.get_json()

            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_difficulty = body.get('difficulty', None)
            new_category = body.get('category', None)

            question_add = Question(
                question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)

            db.session.add(question_add)
            db.session.commit()

            response_object = {
                "success": True,
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

            if len(search_results) is 0:
                return not_found(404)

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
            category = Category.query.get(category_id)

            if category is None:
               return not_found(404)

            category = category.format()

            questions = Question.query.filter(
                Question.category == category_id).all()

            questions_in_category = [
              question.format() for question in questions]

            response_object = {
              "success": True,
              "questions": questions_in_category,
              "total_questions": len(questions_in_category),
              "category": category['type']
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
    # Play Quiz: returns a random question different from previous questions. - POST
    # -----------------------------------------------------------

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

            previous_questions = body.get['previous_questions']
            quiz_category = body.get['quiz_category']['id']


            question_query = Question.query.filter(
              Question.category == quiz_category)

            for question in previous_questions:
              question_query = question_query.filter(
                Question.id != question)

            questions_by_category = question_query.all()
            questions_list = [
              question.format() for question in questions_by_category]

            next_question = None

            questions_total = len(questions_list)

            if questions_total > 0:
              next_question = questions_list[random.randint(
                0, questions_total - 1)]

            response_object = {
              "success": True,
              "question": next_question
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
    def not_found(error):
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
            "message": "Unprocessable."
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
