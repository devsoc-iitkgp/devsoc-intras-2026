"""
Flask Backend API for MetaKGP RAG Bot
Integrates bot.py with a REST API for frontend communication
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import threading
import sys
import os

# Import the bot functions
from bot import generate_response_got, llm, vector_db, G

# Create Flask app with static folder
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for frontend communication

# Store conversation history
conversation_history = []
max_history = 50

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MetaKGP RAG Bot API',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Expects JSON: {"message": "user query"}
    Returns JSON: {"response": "bot answer", "reasoning": {...}, "verified_count": N}
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing "message" field'}), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        print(f"\n{'='*60}")
        print(f"[API] Received query: {user_message}")
        print(f"{'='*60}")
        
        # Call the bot's main function
        bot_response = generate_response_got(user_message)
        
        # Add to conversation history
        conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_message,
            'bot': bot_response
        })
        
        # Keep history size manageable
        if len(conversation_history) > max_history:
            conversation_history.pop(0)
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'timestamp': datetime.now().isoformat(),
            'message_count': len(conversation_history)
        }), 200
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        return jsonify({
            'success': True,
            'history': conversation_history[-limit:],
            'total': len(conversation_history)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({'success': True, 'message': 'History cleared'}), 200


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get bot status and metadata"""
    try:
        return jsonify({
            'success': True,
            'bot_status': 'ready',
            'vector_db_loaded': vector_db is not None,
            'graph_loaded': G.number_of_nodes() > 0,
            'conversation_count': len(conversation_history),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    """Serve the frontend"""
    return send_from_directory('static', 'index.html')


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MetaKGP RAG Bot - Flask API Server")
    print("="*60)
    print("Loading bot components...")
    print(f"Vector DB: {'✓ Loaded' if vector_db else '✗ Not loaded'}")
    print(f"Graph: {'✓ Loaded' if G.number_of_nodes() > 0 else '✗ Not loaded'}")
    print("="*60)
    print("\nStarting server on http://127.0.0.1:5000")
    print("Frontend: http://127.0.0.1:5000")
    print("API: http://127.0.0.1:5000/api")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
