from flask import Flask, render_template, request, jsonify, session, url_for, redirect, send_file, make_response
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import os
import google.generativeai as genai

app = Flask(__name__)

app.config["SECRET_KEY"] = "1241f366ecf2af7cbf180a0bab94fbdea617358a"

client = MongoClient("mongodb://localhost:27017")
db = client["user_details"]
collection = db["details"]

genai.configure(api_key="Enter Your API Key Here")
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

@app.route('/')
def index():
    if 'email' in session:
        return render_template('logout.html')
    else:
        return render_template('index.html')

@app.route('/register')
def register():
    return render_template("Register.html")

@app.route('/registersubmit', methods=['POST'])
def registersubmit():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = db.user_details.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'User already exists. Please sign in.'})

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        db.user_details.insert_one({'email': email, 'password': password_hash.decode('utf-8')})
        return jsonify({'success': 'User registered successfully.'})

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/loginsubmit', methods=['POST'])
def loginsubmit():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = db.user_details.find_one({'email': email})
        if existing_user and bcrypt.checkpw(password.encode('utf-8'), existing_user['password'].encode('utf-8')):
            session['email'] = email
            print(session['email'])
            return jsonify({'success': 'Signed in successfully.'})
        else:
            return jsonify({'error': 'Invalid email or password. Please try again.'})

@app.route('/chatbot')
def chatbot():
    return render_template("chat.html")

@app.route('/get', methods=['POST'])
def get_response():
    msg = request.get_json().get('msg')
    print(msg)
    response = chat.send_message(msg, stream=True)
    response_text = ""
    for chunk in response:
        response_text += f"{chunk.text}\n"
    return jsonify(response=response_text)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('email', None)
    return redirect(url_for('index'))

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    data = request.get_json()
    msg = data.get('msg')
    bot_response = data.get('response')
    print(f"User message: {msg}")
    print(f"Bot response: {bot_response}")
    
    conversation_id = ObjectId()
    email = session['email']
    db.conversations.insert_one({
        'id': str(conversation_id),
        'email': email,
        'messages': [
            {'sender': 'user', 'content': msg},
            {'sender': 'bot', 'content': bot_response}
        ]
    })
    
    return jsonify({'success': 'Conversation saved successfully.'})

if __name__ == '__main__':
    app.run()
