import azure.functions as func
import json
import logging

app = func.FunctionApp()




@app.route(route='chat', auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """Egyszerű chat API - üzeneteket fogad és válaszol"""

    logging.info('Chat request received')

    try:
        req_body = req.get_json()
        user_message = req_body.get('message', '')

        logging.info(f'User message: {user_message}')

        # Bot egyszerű válasza
        bot_reply = f'Echo: {user_message} (Szia! Ez a Fresh Teams Bot!)'

        response_data = {
            'success': True,
            'message': user_message,
            'reply': bot_reply,
            'timestamp': str(__import__('datetime').datetime.now())
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype='application/json'
        )

    except ValueError as e:
        return func.HttpResponse(
            json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
            status_code=400
        )
    except Exception as e:
        logging.error(f'Error: {str(e)}')
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500
        )

@app.route(route='health', auth_level=func.AuthLevel.ANONYMOUS, methods=['GET'])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({'status': 'healthy', 'service': 'Fresh Teams Bot'}),
        status_code=200,
        mimetype='application/json'
    )
