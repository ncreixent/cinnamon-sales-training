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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Store active sessions
sessions = {}

def generate_cinnamon_buyer_prompt():
    """Generate the system prompt for the Cinnamon Case buyer"""
    prompt = """
    You are roleplaying as the owner of Offshoot Intermediaries Limited, a family-run enterprise that offers drug formulations and baby food products. You will be negotiating with a salesperson (the human user) who is the owner of Mahek Masala, which has 1,000 kilograms of premium-quality cinnamon powder for sale.

    Here are your key characteristics and background information:
    - You enjoy a healthy market share in the baby food market with a reputation for prompt payments
    - Your company's image was tarnished when the government discovered a quality issue with one of your drug formulations
    - The government is issuing an ordinance mandating high-grade cinnamon in baby foods with a 10% subsidy
    - The FDA commissioner just agreed to grant you an additional 17% subsidy (total 27%) if you supply baby food to government-run children's homes (which will require 100kg of cinnamon)
    - You see this as a chance to re-establish your image and reputation with the government
    - Your alternative supplier offers cinnamon for Rs. 310/kg, but it's likely inferior quality
    - Your best estimate for high-quality cinnamon is Rs. 380/kg
    - You would be willing to pay up to Rs. 600/kg to secure this deal as you can still make a profit of Rs. 230/kg
    - The additional 17% subsidy is NOT public knowledge
    - Your goal is to get the lowest possible purchase price
    
    Follow these behavioral guidelines during negotiation:
    - Start by introducing yourself and expressing interest in the cinnamon
    - Don't reveal your maximum price (Rs. 600/kg) under any circumstances
    - Don't immediately disclose the subsidy information or government mandate
    - Be concerned about quality given your past issues with the FDA
    - Emphasize your need for all 1,000kg of premium-quality cinnamon
    - Use your alternative supplier as leverage to negotiate a better price
    - Respond to questions about your intended use with vague mentions of your baby food products
    - Only gradually reveal information as the negotiation progresses
    - Be willing to agree to a price between Rs. 310-600/kg, but try to get the lowest possible price
    - Be professional but firm in your negotiation
    
    Remember, your goal is to secure the entire 1,000kg lot at the lowest possible price to maximize your profits.
    """
    return prompt

def calculate_profit_split(agreed_price):
    """Calculate the profit split between buyer and seller based on the agreed price"""
    # Seller's calculations
    seller_cost = 360  # Rs. per kg (from case)
    seller_profit_per_kg = agreed_price - seller_cost
    seller_total_profit = seller_profit_per_kg * 1000  # 1000 kg total
    
    # Buyer's calculations
    buyer_max_willing = 600  # Rs. per kg (from case)
    standard_subsidy = 0.10  # 10% subsidy
    additional_subsidy = 0.17  # Additional 17% subsidy
    total_subsidy = standard_subsidy + additional_subsidy  # 27% total
    
    # Effective cost to buyer after subsidy
    effective_cost_per_kg = agreed_price * (1 - total_subsidy)
    
    # Buyer's profit (given in case as Rs. 230 per kg at Rs. 600 purchase price)
    buyer_profit_at_max_price = 230  # Rs. per kg if bought at Rs. 600
    
    # Adjust buyer profit based on actual price
    # If paid less than Rs. 600, profit increases by the difference
    buyer_profit_per_kg = buyer_profit_at_max_price + (buyer_max_willing - agreed_price)
    buyer_total_profit = buyer_profit_per_kg * 1000  # 1000 kg total
    
    # Calculate total value created
    total_value = seller_total_profit + buyer_total_profit
    
    # Calculate % of value captured by each party
    seller_percent = (seller_total_profit / total_value) * 100
    buyer_percent = (buyer_total_profit / total_value) * 100
    
    # ZOPA Analysis
    seller_reservation_value = max(360, 381)  # From case: cost or Marex alternative
    buyer_reservation_value = 855  # From case: maximum buyer would pay to break even with 27% subsidy
    
    in_zopa = seller_reservation_value <= agreed_price <= buyer_reservation_value
    
    # Calculate distance from mid-point of ZOPA
    zopa_midpoint = (seller_reservation_value + buyer_reservation_value) / 2
    distance_from_midpoint = abs(agreed_price - zopa_midpoint)
    
    # Calculate which party got the better deal relative to the ZOPA midpoint
    if agreed_price < zopa_midpoint:
        better_deal = "Buyer"
        advantage_percent = ((zopa_midpoint - agreed_price) / (zopa_midpoint - seller_reservation_value)) * 100
    else:
        better_deal = "Seller"
        advantage_percent = ((agreed_price - zopa_midpoint) / (buyer_reservation_value - zopa_midpoint)) * 100
    
    return {
        "agreed_price": agreed_price,
        "seller": {
            "cost_per_kg": seller_cost,
            "profit_per_kg": seller_profit_per_kg,
            "total_profit": seller_total_profit,
            "percent_of_value": seller_percent,
            "reservation_value": seller_reservation_value
        },
        "buyer": {
            "gross_price_per_kg": agreed_price,
            "effective_cost_per_kg": effective_cost_per_kg,
            "subsidy_benefit_per_kg": agreed_price * total_subsidy,
            "profit_per_kg": buyer_profit_per_kg,
            "total_profit": buyer_total_profit,
            "percent_of_value": buyer_percent,
            "reservation_value": buyer_reservation_value
        },
        "zopa_analysis": {
            "in_zopa": in_zopa,
            "zopa_range": (seller_reservation_value, buyer_reservation_value),
            "zopa_midpoint": zopa_midpoint,
            "distance_from_midpoint": distance_from_midpoint,
            "better_deal": better_deal,
            "advantage_percent": advantage_percent
        },
        "total_value_created": total_value
    }

def create_profit_split_chart(debrief_data):
    """Create and display a visualization of the profit split between buyer and seller"""
    # Data preparation
    seller_profit = debrief_data["seller"]["total_profit"]
    buyer_profit = debrief_data["buyer"]["total_profit"]
    total_value = debrief_data["total_value_created"]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Value share bar
    labels = ['Seller', 'Buyer']
    values = [seller_profit, buyer_profit]
    percentages = [seller_profit/total_value*100, buyer_profit/total_value*100]
    
    x = np.arange(len(labels))
    width = 0.5
    
    rects = ax.bar(x, values, width, color=['#5DA5DA', '#FAA43A'])
    
    # Add labels and title
    ax.set_ylabel('Profit (Rs.)')
    ax.set_title('Profit Split Analysis')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    
    # Add value annotations
    for i, rect in enumerate(rects):
        height = rect.get_height()
        ax.annotate(f'Rs. {int(height):,}\n({percentages[i]:.1f}%)',
                   xy=(rect.get_x() + rect.get_width()/2, height),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom')
    
    # Add agreed price annotation
    agreed_price = debrief_data["agreed_price"]
    ax.annotate(f'Agreed Price: Rs. {agreed_price}/kg',
               xy=(0.5, 0.95),
               xycoords='figure fraction',
               ha='center',
               fontsize=12,
               bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Add ZOPA annotation
    zopa_range = debrief_data["zopa_analysis"]["zopa_range"]
    zopa_midpoint = debrief_data["zopa_analysis"]["zopa_midpoint"]
    ax.annotate(f'ZOPA Range: Rs. {zopa_range[0]} - Rs. {zopa_range[1]}\nMidpoint: Rs. {zopa_midpoint:.0f}',
               xy=(0.5, 0.87),
               xycoords='figure fraction',
               ha='center',
               fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    plt.tight_layout()
    
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
        model="claude-3-7-sonnet-20250219",
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

#if __name__ == '__main__':
   
    # Run the app
app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))