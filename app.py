from flask import Flask
import os
import anthropic
import json

app = Flask(__name__)

# Get API key from environment variable
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def get_status():
    try:
        # Initialize the Anthropic client
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Try a simple operation to verify the client works
        models = client.models.list()
        
        return {
            "status": "SUCCESS",
            "message": "Anthropic client initialized successfully!",
            "details": {
                "api_key_set": bool(ANTHROPIC_API_KEY),
                "client_initialized": True,
                "models_available": len(models.data) > 0 if models else False,
                "api_key_prefix": ANTHROPIC_API_KEY[:4] + '...' if ANTHROPIC_API_KEY else None
            }
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to initialize Anthropic client: {str(e)}",
            "details": {
                "api_key_set": bool(ANTHROPIC_API_KEY),
                "api_key_prefix": ANTHROPIC_API_KEY[:4] + '...' if ANTHROPIC_API_KEY else None,
                "error": str(e)
            }
        }

@app.route('/')
def status_check():
    status_info = get_status()
    
    # HTML template directly in the Python code
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Anthropic Initialization Test</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .success {{
                color: green;
                background-color: #f0fff0;
                padding: 15px;
                border-radius: 5px;
            }}
            .error {{
                color: red;
                background-color: #fff0f0;
                padding: 15px;
                border-radius: 5px;
            }}
            pre {{
                background: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            .container {{
                margin-top: 30px;
            }}
            h1 {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Anthropic Initialization Test</h1>
            
            <div class="{status_info['status'].lower()}">
                <h2>Status: {status_info['status']}</h2>
                <p>{status_info['message']}</p>
            </div>
            
            <h3>Details:</h3>
            <pre>{json.dumps(status_info['details'], indent=2)}</pre>
            
            <h3>Environment:</h3>
            <pre>Python: {os.environ.get('PYTHON_VERSION', 'Unknown')}
Render: {os.environ.get('RENDER', 'Not detected')}</pre>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))