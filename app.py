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

# Get API key from environment variable
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=ANTHst of your code...lement('div');
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