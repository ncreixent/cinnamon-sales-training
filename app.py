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
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)