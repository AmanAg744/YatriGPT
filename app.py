from flask import Flask, request, render_template,url_for,redirect
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json
from ast import literal_eval
import speech_recognition as sr
import os

# Replace 'command_here' with your actual command
command = 'ffmpeg -i "E:\YatriGPT App\input.mp3" "E:\YatriGPT App\output.wav"'

# Replace the placeholder with your Atlas connection string
uri = "mongodb+srv://AnirudhAgrawal1244:Anirudh%40124@anirudhscluster.ccvhnqb.mongodb.net/"
# Set the Stable API version when creating a new client
client = MongoClient(uri, server_api=ServerApi('1'))
                          
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup_get', methods=['POST'])
def signup_get():
    if request.method == "POST":
        username=request.form["username"]
        email=request.form["email"]
        password=request.form["password"]
        confirmPassword=request.form["confirmpassword"]
        cred_list=[[username,email,password,confirmPassword]]
        print(cred_list)
        print("Email is:",email)
        print("Password is:",password)
        print("Confirm Password is:",confirmPassword)
        db=client["YatriGPT"]
        collection=db["UserInfo"]
        query = {"email": email}
        existing_user=collection.find_one(query)
        if email=="" or password =="" or confirmPassword=="" or username=="":
            return render_template("signup_message.html",message="Fields are left empty.")
        elif existing_user:
            return render_template("signup_message.html",message=f"The user with emailid: {email} exists.")
        elif password!=confirmPassword:
            return render_template("signup_message.html",message="The password is not equal to confirm password")
        elif password==confirmPassword:
            return redirect(url_for("travel_type", cred_list=cred_list))            
        return redirect(url_for("travel_type"))
    print("Failure")
    return render_template("signup_message.html",message="Please re-enter.")

@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        email=request.form["email"]
        password=request.form["password"]
        db=client["YatriGPT"]
        collection=db["UserInfo"]
        cred_query = {"email": email,"password":password}
        cred_found=collection.find_one(cred_query)
        if email=="" or password =="":
             return render_template("index_message.html",message="Fiels are left empty")
        elif cred_found:
            print(cred_found["name"])
            user_name=cred_found["name"]
            return render_template("main.html")
        else:
            return render_template("index_message.html",message="Email or Password is not correct")
    print("failure")
    return render_template("index_message.html",message="Please re-enter")

def convert_string_to_list(string_list):
    try:
        # Using literal_eval to safely evaluate the string as a Python expression
        converted_list = literal_eval(string_list)
        if isinstance(converted_list, list):
            return converted_list
        else:
            return []
    except (ValueError, SyntaxError) as e:
        print(f"Error converting string to list: {e}")
        return []

@app.route('/travel_type')
def travel_type():
    cred_list = request.args.get("cred_list")
    print(cred_list)
    cred_list=convert_string_to_list(cred_list)
    print(type(cred_list))
    print("Name: ", cred_list[0])
    print("Email: ", cred_list[1])
    print("Password: ", cred_list[2])
    print("Confirm Password: ", cred_list[3])
    return render_template('buttons.html', cred_list=cred_list)

@app.route('/button_clicked', methods=['POST'])
def button_clicked():
    selected_types = request.form.getlist('travel_type[]')
    cred_list = request.form['cred_list']
    cred_list = convert_string_to_list(cred_list)

    username = cred_list[0]
    email = cred_list[1]
    password = cred_list[2]
    confirmPassword = cred_list[3]

    db = client["YatriGPT"]
    collection = db["UserInfo"]

    credential = {
        "name": f"{username}",
        "email": f"{email}",
        "password": f"{password}",
        "travel-type": f"{selected_types}"
    }
    result = collection.insert_one(credential)
    if result.inserted_id:
        print(f"Data inserted successfully. Inserted ID: {result.inserted_id}")
        return redirect(url_for("index"))
    else:
        return "Failed to insert data"
    
@app.route('/save_audio', methods=['POST'])
def save_audio():
    if 'audio' in request.files:
        audio = request.files['audio']
        audio.save(r'E:\YatriGPT App\input.mp3')# Specify the path to save the audio file
        # Run the command in the command prompt
        os.system(command)
        audio_file = "E:\YatriGPT App\output.wav"

        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        try:
            # Recognize speech using Google Speech Recognition
            recorded_text = recognizer.recognize_google(audio)
            print(f"Text from audio: {recorded_text}")
        except sr.UnknownValueError:
            print("Could not understand the audio")
        except sr.RequestError as e:
            print(f"Error: {e}")
        os.remove("input.mp3")
        os.remove("output.wav")
        return 'Audio file saved successfully!'
    return 'No audio received.'

if __name__ == '__main__':
    app.run(debug=True)
