from flask import Flask, render_template, request, jsonify
import os
import json
import anthropic
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

app = Flask(__name__)

# Get API key from environment variable or set it directly
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Store active sessions
sessions = {}

# Functions from your notebook (reuse all your functions here)
def generate_cinnamon_buyer_prompt():
    # Same as in your notebook
    prompt = """
    You are roleplaying as the owner of Offshoot Intermediaries Limited...
    """
    return prompt

def calculate_profit_split(agreed_price):
    # Same as in your notebook
    # ...

def create_profit_split_chart(debrief_data):
    # Modified to return base64 image for web
    # Data preparation
    seller_profit = debrief_data["seller"]["total_profit"]
    buyer_profit = debrief_data["buyer"]["total_profit"]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Rest same as notebook
    # ...
    
    # Convert plot to base64 image
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return img_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    # Create new session
    import uuid
    session_id = str(uuid.uuid4())
    
    # Initial message
    initial_message = "Hello, I'm the owner of Offshoot Intermediaries Limited. I understand you have a 1,000-kilogram lot of premium-quality cinnamon powder available. I'm interested in discussing a potential purchase."
    
    # Store session
    sessions[session_id] = {
        'conversation': [{"role": "assistant", "content": initial_message}]
    }
    
    return jsonify({
        'session_id': session_id,
        'message': initial_message
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    # Add message to conversation
    sessions[session_id]['conversation'].append({"role": "user", "content": message})
    
    # Get system prompt
    system_prompt = generate_cinnamon_buyer_prompt()
    
    # Call Claude API
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=system_prompt,
        messages=sessions[session_id]['conversation']
    )
    
    # Get response
    buyer_response = response.content[0].text
    
    # Add to conversation
    sessions[session_id]['conversation'].append({"role": "assistant", "content": buyer_response})
    
    return jsonify({
        'message': buyer_response
    })

@app.route('/api/debrief', methods=['POST'])
def debrief():
    data = request.json
    agreed_price = float(data.get('price', 0))
    
    if agreed_price <= 0:
        return jsonify({'error': 'Invalid price'}), 400
    
    # Generate debrief
    debrief_data = calculate_profit_split(agreed_price)
    chart_image = create_profit_split_chart(debrief_data)
    
    # Return debrief data
    return jsonify({
        'debrief': debrief_data,
        'chart': chart_image
    })

if __name__ == '__main__':
    # Make sure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Create index.html if it doesn't exist
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Cinnamon Case Sales Training</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        #chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 5px;
        }
        .buyer {
            background-color: #f1f1f1;
            margin-right: 30%;
        }
        .seller {
            background-color: #d1e7ff;
            margin-left: 30%;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center mb-4">Cinnamon Case Sales Training</h1>
        
        <div id="intro-container">
            <div class="card mb-4">
                <div class="card-header">
                    <h2 class="h5 mb-0">Sales Negotiation Simulation</h2>
                </div>
                <div class="card-body">
                    <p>You are the seller (Mahek Masala) with 1,000 kg of premium-quality cinnamon.</p>
                    <p>Your cost is Rs. 360 per kg. Anything above this is profit.</p>
                    <p>The AI will play the buyer (Offshoot Intermediaries Limited).</p>
                    <button id="start-btn" class="btn btn-primary">Start Negotiation</button>
                </div>
            </div>
        </div>
        
        <div id="negotiation-container" style="display: none;">
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between">
                    <h2 class="h5 mb-0">Negotiation</h2>
                    <button id="conclude-btn" class="btn btn-success btn-sm">Conclude Deal</button>
                </div>
                <div class="card-body">
                    <div id="chat-container"></div>
                    <div class="input-group">
                        <input type="text" id="message-input" class="form-control" placeholder="Type your message...">
                        <button id="send-btn" class="btn btn-primary">Send</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="conclusion-container" style="display: none;">
            <div class="card mb-4">
                <div class="card-header">
                    <h2 class="h5 mb-0">Conclude Deal</h2>
                </div>
                <div class="card-body">
                    <p>Enter the agreed price per kilogram:</p>
                    <div class="input-group mb-3">
                        <span class="input-group-text">Rs.</span>
                        <input type="number" id="price-input" class="form-control" placeholder="Price">
                        <button id="analyze-btn" class="btn btn-primary">Analyze</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="debrief-container" style="display: none;">
            <div class="card mb-4">
                <div class="card-header">
                    <h2 class="h5 mb-0">Negotiation Debrief</h2>
                </div>
                <div class="card-body">
                    <h3 class="h6">Profit Split</h3>
                    <div class="text-center mb-4">
                        <img id="profit-chart" class="img-fluid" alt="Profit Split Chart">
                    </div>
                    
                    <h3 class="h6">Deal Summary</h3>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p><strong>Agreed Price:</strong> <span id="agreed-price"></span> per kg</p>
                            <p><strong>Total Transaction Value:</strong> <span id="transaction-value"></span></p>
                            <p><strong>Total Value Created:</strong> <span id="total-value"></span></p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Seller Profit:</strong> <span id="seller-profit"></span></p>
                            <p><strong>Buyer Profit:</strong> <span id="buyer-profit"></span></p>
                            <p><strong>Advantage To:</strong> <span id="advantage"></span></p>
                        </div>
                    </div>
                    
                    <h3 class="h6">ZOPA Analysis</h3>
                    <p>The Zone of Possible Agreement ranges from Rs. <span id="zopa-min"></span> to Rs. <span id="zopa-max"></span>, with a midpoint of Rs. <span id="zopa-mid"></span>.</p>
                    
                    <div class="mt-4">
                        <button id="restart-btn" class="btn btn-primary">Start New Negotiation</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let sessionId = null;
        
        // Start negotiation
        document.getElementById('start-btn').addEventListener('click', async function() {
            try {
                const response = await fetch('/api/start_session', {
                    method: 'POST'
                });
                const data = await response.json();
                sessionId = data.session_id;
                
                // Show negotiation container
                document.getElementById('intro-container').style.display = 'none';
                document.getElementById('negotiation-container').style.display = 'block';
                
                // Add initial message
                addMessage(data.message, 'buyer');
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to start negotiation.');
            }
        });
        
        // Send message
        document.getElementById('send-btn').addEventListener('click', sendMessage);
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Conclude deal
        document.getElementById('conclude-btn').addEventListener('click', function() {
            document.getElementById('negotiation-container').style.display = 'none';
            document.getElementById('conclusion-container').style.display = 'block';
        });
        
        // Analyze deal
        document.getElementById('analyze-btn').addEventListener('click', async function() {
            const price = document.getElementById('price-input').value;
            
            if (!price || price <= 0) {
                alert('Please enter a valid price.');
                return;
            }
            
            try {
                const response = await fetch('/api/debrief', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ price: price })
                });
                
                const data = await response.json();
                
                // Display debrief
                document.getElementById('conclusion-container').style.display = 'none';
                document.getElementById('debrief-container').style.display = 'block';
                
                // Set chart
                document.getElementById('profit-chart').src = 'data:image/png;base64,' + data.chart;
                
                // Fill in data
                document.getElementById('agreed-price').textContent = 'Rs. ' + price;
                document.getElementById('transaction-value').textContent = 'Rs. ' + numberWithCommas(price * 1000);
                document.getElementById('total-value').textContent = 'Rs. ' + numberWithCommas(Math.round(data.debrief.total_value_created));
                document.getElementById('seller-profit').textContent = 'Rs. ' + numberWithCommas(Math.round(data.debrief.seller.total_profit));
                document.getElementById('buyer-profit').textContent = 'Rs. ' + numberWithCommas(Math.round(data.debrief.buyer.total_profit));
                document.getElementById('advantage').textContent = data.debrief.zopa_analysis.better_deal;
                document.getElementById('zopa-min').textContent = data.debrief.zopa_analysis.zopa_range[0];
                document.getElementById('zopa-max').textContent = data.debrief.zopa_analysis.zopa_range[1];
                document.getElementById('zopa-mid').textContent = Math.round(data.debrief.zopa_analysis.zopa_midpoint);
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to analyze deal.');
            }
        });
        
        // Restart
        document.getElementById('restart-btn').addEventListener('click', function() {
            sessionId = null;
            document.getElementById('debrief-container').style.display = 'none';
            document.getElementById('intro-container').style.display = 'block';
            document.getElementById('chat-container').innerHTML = '';
            document.getElementById('message-input').value = '';
        });
        
        // Helper functions
        async function sendMessage() {
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'seller');
            
            // Clear input
            messageInput.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                // Add buyer response
                addMessage(data.message, 'buyer');
            } catch (error) {
                console.error('Error:', error);
                addMessage('Failed to get response. Please try again.', 'buyer');
            }
        }
        
        function addMessage(message, role) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', role);
            messageDiv.textContent = message;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function numberWithCommas(x) {
            return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
    </script>
</body>
</html>
            ''')
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))