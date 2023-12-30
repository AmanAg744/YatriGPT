from flask import Flask, request, render_template,url_for,redirect
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json
from ast import literal_eval
import speech_recognition as sr
import os
import uuid
from google.cloud import dialogflow_v2 as dialogflow
from gtts import gTTS
from playsound import playsound
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords
import requests
import re
from geopy.geocoders import Nominatim
import time



API_KEY = 'AIzaSyBnZeMv7ivrYEy4kMR7ewMoWcuabfr06Hs'
latitude_n = 13.3409
longitude_n = 74.7421

# Download NLTK data if not already downloaded
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
import nltk
nltk.download('averaged_perceptron_tagger')


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "E:\YatriGPT-main\yatrigpt-9xam-b5419913193b.json"  # Replace with your service account key path
project_id = "yatrigpt-9xam"  # Replace with your Dialogflow project ID
language_code = "en"  # Replace with your language code if different

# Replace 'command_here' with your actual command
command = 'ffmpeg -i "E:\YatriGPT-main\input.mp3" "E:\YatriGPT-main\output.wav"'

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
        audio.save(r'E:\YatriGPT-main\input.mp3')# Specify the path to save the audio file
        # Run the command in the command prompt
        os.system(command)
        audio_file = "E:\YatriGPT-main\output.wav"

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
        return redirect(url_for('chats',recorded_text=recorded_text))
    return 'No audio received.'

def detect_intent_text(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    return response.query_result.fulfillment_text

def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    pos_tags = pos_tag(words)
    entities = [word for word, pos in pos_tags if (pos == 'NNP' or pos == 'CD' or pos.startswith('N')) and word.lower() not in stop_words]
    return entities

def find_nearby_beaches(api_key, lat, lng,keywords):
    endpoint = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": api_key,
        "location": f"{lat},{lng}",
        "radius": 4000,  # You can adjust the radius as needed
        "keyword": keywords
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        results = response.json()
        if "results" in results:
            nearby_beaches = results["results"][:5]  # Extracting the top 5 results
            return nearby_beaches
        else:
            return "No beach found nearby."
    else:
        return "Failed to fetch data."

def get_airport_info(destination):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchAirport"

    querystring = {"query": destination	}

    headers = {
	"X-RapidAPI-Key": "b767d8456bmshce1a06fcb713dc3p184fa3jsn4d8515f2c503",
	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
}

    
    
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") and data.get("data"):
            airports = data["data"]
            for airport in airports:
                airport_code = airport.get("airportCode")
                return airport_code
        else:
            print("No airport information found.")
    else:
        print(f"Error: {response.status_code}")


def get_coordinates(city):
    try:
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.geocode(city)

        if location:
            latitude = location.latitude
            longitude = location.longitude
            print(f"Coordinates of {city}: Latitude = {latitude}, Longitude = {longitude}")
            return latitude, longitude
        else:
            print("Coordinates not found for the city.")
    except GeocoderInsufficientPrivileges as e:
        print(f"Error: {e}")
        # Handle 403 error, maybe add a delay and retry
        time.sleep(1)
        get_coordinates(city)

def get_location_id(city):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchLocation"

    querystring = {"query": city}

    headers = {
	"X-RapidAPI-Key": "b767d8456bmshce1a06fcb713dc3p184fa3jsn4d8515f2c503",
	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == True and data.get("message") == "Success":
            location_id = data.get("data", [])[0].get("locationId")
            return location_id
        else:
            print("Error in API response:", data)
    else:
        print("Error in API request. Status code:", response.status_code)


@app.route('/chats')
def chats():
    session_id = str(uuid.uuid4())
    query_text = request.args.get("recorded_text")
    response_text = detect_intent_text(project_id, session_id, query_text, language_code)
    # Extract keywords from the response text
    keywords=[]
    keywords = extract_keywords(query_text)
    print("Keywords:", keywords)
    
    # Rest of the code remains unchanged
    user_input =response_text
    match = re.search(r'from\s+(\w+)\s+to\s+(\w+)\s+on\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match1 = re.search(r'in\s+(\w+)\s+for\s+(\d{4}-\d{2}-\d{2})\s+-\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match2 = re.search(r'top\s+(\w+)\s+in\s+(\w+)',user_input, re.IGNORECASE)

    if match:
        from_place = match.group(1)  # Extracting 'from' location
        to_place = match.group(2)    # Extracting 'to' location
        date = match.group(3)        # Extracting date
        from_place_code=str(get_airport_info(from_place))
        to_place_code=str(get_airport_info(to_place))
        print(f"From: {from_place}")
        print(f"To: {to_place}")
        print(f"Date: {date}")
        print("from-code:",from_place_code)
        print("to-code:",to_place_code)
    elif match1:
        location = match1.group(1)       # Extracting the location
        start_date = match1.group(2)     # Extracting the start date
        end_date = match1.group(3)       # Extracting the end date
        city_coordinates=get_coordinates(location)
        loc_late=city_coordinates[0]
        loc_longi=city_coordinates[1]
        print(loc_late)
        print(loc_longi)
        print(f"Location: {location}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
    elif match2:
        top_entity = match2.group(1)
        city = match2.group(2)
        print(f"Top entity: {top_entity}")
        print(f"City: {city}")
    else:
        print("Information not found.")
    response_printed = False
    for keyword in keywords:
        if 'nearby' in query_text:
            print(f"List of top 5 nearby {keywords[0]}")
            beaches = find_nearby_beaches(API_KEY, latitude_n, longitude_n,keywords)
            if beaches != "Failed to fetch data." and beaches != "No beach found nearby.":
                for idx, beach in enumerate(beaches, start=1):
                    print(f"{idx}. {beach['name']}")
                break
            else:
                print(beaches) 
                break
        elif keyword=='flight' and not response_printed:
            print("Response from Dialogflow:", response_text)
            response_printed=True
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"
                date = '2024-01-04'
                querystring = {
                        "sourceAirportCode":from_place_code,
                        "destinationAirportCode":to_place_code,
                        "date": date,
                        "itineraryType": "ONE_WAY",
                        "sortOrder": "ML_BEST_VALUE",
                        "numAdults": "1",
                        "numSeniors": "0",
                        "classOfService": "ECONOMY",
                        "pageNumber": "1",
                        "currencyCode": "INR"
                    }

                headers = {
                	"X-RapidAPI-Key": "b767d8456bmshce1a06fcb713dc3p184fa3jsn4d8515f2c503",
                	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
                }

                response = requests.get(url, headers=headers, params=querystring)

                if response.status_code == 200:
                    data = response.json()
                    if data["status"]:
                        flights = data["data"]["flights"]
                        for flight in flights:
                            display_name = flight["segments"][0]["legs"][0]["marketingCarrier"]["displayName"]
                            logo_url = flight["segments"][0]["legs"][0]["marketingCarrier"]["logoUrl"]
                            flight_url = flight["purchaseLinks"][0]["url"]
                            print(f"Airline: {display_name}")
                            print(f"Flight URL: {flight_url}")
                            print(f"Logo URL: {logo_url}")
                            print("-----------")
                        break
                    else:
                        #front-end alert(exception handled):
                        print("Either of the details does not exist please speak again.")
                        break
                else:
                    print("Error in API request. Status Code:", response.status_code)
            except:
                continue
        elif keyword=='hotel' and not response_printed:
            print("Response from Dialogflow:", response_text)
            response_printed=True
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotelsByLocation"

                # Take user input for latitude, longitude, check-in, and check-out dates
                latitude = str(loc_late)
                longitude = str(loc_longi)
                check_in = str(start_date)
                check_out = str(end_date)

                querystring = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "pageNumber": "1",
                    "currencyCode": "INR"
                }

                headers = {
                	"X-RapidAPI-Key": "b767d8456bmshce1a06fcb713dc3p184fa3jsn4d8515f2c503",
                	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
                }


                response = requests.get(url, headers=headers, params=querystring)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    data_list = response.json().get("data", [])

                    # Sort hotels based on rating (highest to lowest)
                    sorted_hotels = sorted(data_list["data"], key=lambda x: x["bubbleRating"]["rating"], reverse=True)

                    # Loop through each hotel entry in the sorted list
                    for hotel in sorted_hotels:
                        # Extract and print the details
                        title = hotel["title"]
                        external_url = hotel["commerceInfo"]["externalUrl"]
                        rating = hotel["bubbleRating"]["rating"]
                        print("Title:", title)
                        print("Rating:", rating)
                        print("External URL:", external_url)

                        print("-" * 50)
                    break

                else:
                    print("Error:", response.status_code)
                    print(response.text)
                    break
            except:
                continue
        elif keyword=='restaurants'or'restaurant' and not response_printed:
            print("Response from Dialogflow:", response_text)
            response_printed=True
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"

                querystring = {"locationId": str(get_location_id(city))}

                headers = {
                	"X-RapidAPI-Key": "b767d8456bmshce1a06fcb713dc3p184fa3jsn4d8515f2c503",
                	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
                }

                response = requests.get(url, headers=headers, params=querystring)

                if response.status_code == 200:
                    data_list = response.json().get("data", [])

                    # Sort restaurants based on rating (highest to lowest)
                    sorted_restaurants = sorted(data_list["data"], key=lambda x: x["averageRating"], reverse=True)

                    # Loop through each restaurant entry in the sorted list
                    for restaurant in sorted_restaurants:
                        # Extract and print the details
                        name = restaurant["name"]
                        img_url = restaurant["thumbnail"]["photo"]["photoSizes"][0]["url"]
                        reviewpg_url = restaurant["reviewSnippets"]["reviewSnippetsList"][0]["reviewUrl"]
                        rating = restaurant["averageRating"]
                        print("Rating:", rating)
                        print("Name:", name)
                        print("Img URL:", img_url)
                        print("Page URL:", reviewpg_url)
                        print("-" * 50)
                    break
                else:
                    print("Error:", response.status_code)
                    print(response.text)
                    break
            except:
                continue
        else:
           if not response_printed:
            print("Response from Dialogflow:", response_text)
            response_printed=True
           continue
    # beaches = find_nearby_beaches(API_KEY, latitude, longitude, keywords)
    # if isinstance(beaches, list):
    #     if beaches:
    #         # Sort beaches by rating in descending order
    #         beaches_sorted = sorted(beaches, key=lambda x: x.get('rating', 0) if x.get('rating') != 'Not Rated' else 0, reverse=True)

    #         print(f"Top 5 nearby {keywords[0]} (Descending Order by Rating):")
    #         for idx, beach in enumerate(beaches_sorted[:5], start=1):
    #             beach_name = beach['name']
    #             beach_rating = beach.get('rating', 'Not Rated')
    #             print(f"{idx}. {beach_name} - Rating: {beach_rating}")
    #     else:
    #         print("No beaches found nearby.")
    # else:
    #   print(beaches)
    print(query_text)
    return query_text

if __name__ == '__main__':
    app.run(debug=True)
