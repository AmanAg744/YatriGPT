from flask import Flask, request, render_template,url_for,redirect,make_response,session,jsonify
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
from geopy.exc import GeocoderInsufficientPrivileges
import pyttsx3
import threading
import google.generativeai as genai
from llama_response import llama_response
import pathlib
import google.ai.generativelanguage as glm
from PIL import Image


genai.configure(api_key="AIzaSyA5Osb5AV8cPleImeq-0hlSC5k5KNv1wCs")
model = genai.GenerativeModel('gemini-pro-vision')
API_KEY = 'AIzaSyBnZeMv7ivrYEy4kMR7ewMoWcuabfr06Hs'
latitude_n = 13.3409
longitude_n = 74.7421

header_trip_adviser=headers = {
	"X-RapidAPI-Key": "91dd5a043amsh3881eaded5bef78p16eedajsnb69201ec5d43",
	"X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
}

# Download NLTK data if not already downloaded
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
import nltk
nltk.download('averaged_perceptron_tagger')


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "E:\YatriGPT-main\yatrigpt-9xam-b5419913193b.json"  # Replace with your service account key path
project_id = "yatrigpt-9xam"  # Replace with your Dialogflow project ID
language_code = "en"  # Replace with your language code if different

# Replace the placeholder with your Atlas connection string
uri = "mongodb+srv://AnirudhAgrawal1244:Anirudh%40124@anirudhscluster.ccvhnqb.mongodb.net/"
# Set the Stable API version when creating a new client
client = MongoClient(uri, server_api=ServerApi('1'))
client_user=MongoClient(uri, server_api=ServerApi('1'))                         
app = Flask(__name__)
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
        email=str(email)
        email_without_dot=email.replace(".","")
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
            user_chats=client[email_without_dot] 
            collection_chat=user_chats["dummy_collection"]
            collection_chat.insert_one({})
            collection_chat.delete_many({})
            session["email_without_dot"]=email_without_dot
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

def find_nearby_places_info(api_key, lat, lng, keywords):
    endpoint = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "location": f"{lat},{lng}",
        "radius": 40000,  # You can adjust the radius as needed
        "keyword": ",".join(keywords)  # Joining keywords into a comma-separated string
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an error for 4XX or 5XX status codes
        results = response.json()
        
        places_info = []
        if "results" in results:
            nearby_places = results["results"][:5]  # Extracting the top 5 results
            for place in nearby_places:
                place_id = place['place_id']
                # Fetch details for each place to get the rating, image, and website
                details_params = {
                    "key": api_key,
                    "place_id": place_id,
                    "fields": "name,rating,photos,website"
                }
                details_response = requests.get(details_endpoint, params=details_params)
                details_result = details_response.json()
                if 'result' in details_result:
                    place_info = {
                        "name": details_result['result'].get('name', 'N/A'),
                        "rating": details_result['result'].get('rating', 'Not Rated'),
                        "image_url": details_result['result'].get('photos', [{}])[0].get('photo_reference', 'N/A'),
                        "website": details_result['result'].get('website', 'N/A')
                    }
                    places_info.append(place_info)

            return places_info
        else:
            return f"No {keywords[0]} found nearby."
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch data: {e}"


def get_coordinates(city):
    url = "https://api.opencagedata.com/geocode/v1/json"

    querystring = {"q": city, "key": "32a4b8c0d6b14954aebd864f60f3e754", "language": "en"}

    response = requests.get(url, params=querystring)

    data = response.json()

    if response.status_code == 200:
        # Extract latitude and longitude from the JSON response
        latitude = data['results'][0]['geometry']['lat']
        longitude = data['results'][0]['geometry']['lng']

        return latitude,longitude
        # print(f"Latitude: {latitude}, Longitude: {longitude}")
    else:
        print(f"Error: {data['status']['message']}")


def get_airport_info(destination):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchAirport"

    querystring = {"query": destination	}

    headers = header_trip_adviser

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

def get_location_id(city):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchLocation"

    querystring = {"query": city}

    headers= header_trip_adviser

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

def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        playsound("Say.mp3")
        audio = r.listen(source)
        print("Recognizing Now .... ")
        # recognize speech using google
        try:
            said_text=r.recognize_google(audio)
            print(said_text)
            print("Audio Recorded Successfully \n ")
            return said_text
        except Exception as e:
            print("Error :  " + str(e))
            playsound("Say2.mp3")
            speech_to_text()

def text_to_speech(text):
    engine = pyttsx3.init()

    # Getting all available voices
    voices = engine.getProperty('voices')

    # Selecting a female voice (index 1 - for example purposes)
    # Change the index or criteria to select a different female voice
    engine.setProperty('voice', voices[0].id)

    engine.say(text)
    engine.runAndWait()

def perform_text_to_speech(response_text):
    time.sleep(1)  # To allow some time for the response to be processed
    text_to_speech(response_text)

@app.route('/printText')
def printText():
    place_info=None
    session_id = str(uuid.uuid4())
    query_text=speech_to_text()
    response_text = detect_intent_text(project_id, session_id, query_text, language_code)
    keywords=[]
    keywords = extract_keywords(query_text)
    print("Keywords:", keywords)
    user_input =response_text
    match = re.search(r'from\s+(\w+)\s+to\s+(\w+)\s+on\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match1 = re.search(r'in\s+(\w+)\s+for\s+(\d{4}-\d{2}-\d{2})\s+-\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match2 = re.search(r'top\s+(\w+)\s+in\s+(\w+)',user_input, re.IGNORECASE)
    city=None
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
    elif match2 and ("restaurant" or "restaurants" in keywords):
        top_entity = match2.group(1)
        city = match2.group(2)
        print(f"Top entity: {top_entity}")
        print(f"City: {city}")
    else:
        print("Information not found.")
    if "book" in keywords:
        if "flight" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"
                querystring = {
                        "sourceAirportCode": from_place_code,
                        "destinationAirportCode": to_place_code,
                        "date": date,
                        "itineraryType": "ONE_WAY",
                        "sortOrder": "ML_BEST_VALUE",
                        "numAdults": "1",
                        "numSeniors": "0",
                        "classOfService": "ECONOMY",
                        "pageNumber": "1",
                        "currencyCode": "INR"
                    }

                headers = header_trip_adviser
                response = requests.get(url, headers=headers, params=querystring)
                logo_list=[]
                flight_name=[]
                flight_web_url=[]
                flight_price_list=[]
                details=[]
                if response.status_code == 200:
                    data = response.json()
                    if data["status"]:
                        flights = data["data"]["flights"]
                        for i in range(5):
                            display_name = flights[i]["segments"][0]["legs"][0]["marketingCarrier"]["displayName"]
                            flight_name.append(display_name)
                            image_url = flights[i]["segments"][0]["legs"][0]["marketingCarrier"]["logoUrl"]
                            logo_list.append(image_url)
                            flight_url = flights[i]["purchaseLinks"][0]["url"]
                            flight_price = flights[i]["purchaseLinks"][0]["totalPrice"]
                            flight_price_list.append(flight_price)
                            flight_web_url.append(flight_url)
                            print(f"Airline: {display_name}")
                            print(f"Flight URL: {flight_url}")
                            print(f"Logo URL: {image_url}")
                            print(f"Price: {flight_price}")
                            print("-----------")
                        for logo_url,name,ext_url,price in zip(logo_list,flight_name,flight_web_url,flight_price_list):
                            details.append({"img_url":logo_url, "name":name, "ext_url":ext_url, "rating":price})
                        speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                        email_without_dot=session["email_without_dot"]
                        user_chats=client[email_without_dot]
                        collection_name=query_text
                        session["collection_name"]=collection_name
                        collection_chats=user_chats[collection_name]
                        chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"flight"}
                        result_chats=collection_chats.insert_one(chats)
                        chats_all=collection_chats.find()
                        mychats=[chat for chat in chats_all]
                        print(mychats)
                        speech_thread.start()
                        return render_template("response.html",mychats=mychats)
                    else:
                        print("Error in API response:", data["message"])
                else:
                    print("Error in API request. Status Code:", response.status_code)
            except Exception as e:
                print("Error:",e)
        if "restaurants" or "restaurant" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"

                querystring = {"locationId": get_location_id(city)}

                headers = header_trip_adviser

                response = requests.get(url, headers=headers, params=querystring)

                if response.status_code == 200:
                    data_list = response.json().get("data", [])

                    # Sort restaurants based on rating (highest to lowest)
                    sorted_restaurants = sorted(data_list["data"], key=lambda x: x["averageRating"], reverse=True)

                    # Loop through each restaurant entry in the sorted list
                    names=[]
                    img_list=[]
                    restaurants_rating=[]
                    restaurant_urls=[]
                    details=[]
                    for i in range(5):
                        # Extract and print the details
                        name = sorted_restaurants[i]["name"]
                        names.append(name)
                        img_url = sorted_restaurants[i]["thumbnail"]["photo"]["photoSizes"][0]["url"]
                        reviewpg_url = sorted_restaurants[i]["reviewSnippets"]["reviewSnippetsList"][0]["reviewUrl"]
                        restaurant_urls.append(reviewpg_url)
                        rating = sorted_restaurants[i]["averageRating"]
                        restaurants_rating.append(rating)
                        print("Rating:", rating)
                        print("Name:", name)
                        print("Img URL:", img_url)
                        img_list.append(img_url)
                        print("Page URL:", reviewpg_url)
                        print("-" * 50)
                    for img_url,name,stars,ext_url in zip(img_list,names,restaurants_rating,restaurant_urls):
                        details.append({"img_url":img_url, "name":name, "rating":stars, "ext_url":ext_url})
                    print(details)
                    email_without_dot=session["email_without_dot"]
                    user_chats=client[email_without_dot]
                    collection_name=query_text
                    session["collection_name"]=collection_name
                    collection_chats=user_chats[collection_name]
                    chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"restaurants"}
                    result_chats=collection_chats.insert_one(chats)
                    chats_all=collection_chats.find()
                    mychats=[chat for chat in chats_all]
                    print(mychats)
                    speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                    speech_thread.start()
                    return render_template("response.html",mychats=mychats)
                else:
                    print("Error:", response.status_code)
                    print(response.text)
            except Exception as e:
                print("Error:",e)
        if "hotel" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotelsByLocation"
                latitude = loc_late
                longitude = loc_longi
                check_in = start_date
                check_out = end_date

                querystring = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "pageNumber": "1",
                    "currencyCode": "INR"
                }

                headers = header_trip_adviser

                response = requests.get(url, headers=headers, params=querystring)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    data_list = response.json().get("data", [])
                    # Sort hotels based on rating (highest to lowest)
                    sorted_hotels = sorted(data_list["data"], key=lambda x: x["bubbleRating"]["rating"], reverse=True)

                    # Loop through each hotel entry in the sorted list
                    hotel_name=[]
                    hotel_ext_url=[]
                    hotel_rating=[]
                    hotel_image=[]
                    details=[]
                    for i in range(5):
                        # Extract and print the details
                        title = sorted_hotels[i]["title"]
                        title=str(title)
                        title=title[3:]
                        hotel_name.append(title)
                        external_url = None
                        try:
                            external_url_1 = sorted_hotels[i]["commerceInfo"]
                            external_url = external_url_1["externalUrl"]
                        except:
                            if external_url is None:
                                external_url_1 = sorted_hotels[i].get("commerceInfo", {})
                                external_url = external_url_1.get("externalUrl","")

                            elif external_url is None:
                                external_url_1 = sorted_hotels[i].get("commerceInfo", {})
                                external_url = external_url_1["externalUrl"]

                            elif external_url is None:
                                external_url_1 = sorted_hotels[i]["commerceInfo"]
                                external_url = external_url_1.get("externalUrl","")
                        img_url0 = sorted_hotels[i]["cardPhotos"][0]["sizes"]["urlTemplate"]
                        img_spl = img_url0.split('?')
                        img_url = img_spl[0]
                        hotel_image.append(img_url)
                        hotel_ext_url.append(external_url)
                        rating = sorted_hotels[i]["bubbleRating"]["rating"]
                        hotel_rating.append(rating)
                        print("Title:", title)
                        print("Rating:", rating)
                        print("External URL:", external_url)

                        print("-" * 50)
                    for name,ext_url,rating,img_url in zip(hotel_name,hotel_ext_url,hotel_rating,hotel_image):
                        details.append({"name":name, "rating":rating, "ext_url":ext_url,"img_url":img_url})
                    email_without_dot=session["email_without_dot"]
                    user_chats=client[email_without_dot]
                    collection_name=query_text
                    session["collection_name"]=collection_name
                    collection_chats=user_chats[collection_name]
                    chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"hotel"}
                    result_chats=collection_chats.insert_one(chats)
                    chats_all=collection_chats.find()
                    mychats=[chat for chat in chats_all]
                    print(mychats)
                    speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                    speech_thread.start()
                    return render_template("response.html",mychats=mychats)

                else:
                    print("Error:", response.status_code)
                    print(response.text)
                    pass
            except  Exception as e:
                print("Error:",e)
    elif "nearby" in query_text:
        places_info = find_nearby_places_info(API_KEY, latitude_n, longitude_n, keywords)  # Pass 'keywords' to the function
        if isinstance(places_info, list):
            if places_info:
                response_text=f"Top 5 nearby {keywords[0]} Information:"
                print(response_text)
                p_name=[]
                p_rating=[]
                p_img=[]
                p_ext_url=[]
                details=[]
                for idx, place_info in enumerate(places_info[:5], start=1):
                    place_name = place_info['name']
                    p_name.append(place_name)
                    place_rating = place_info['rating']
                    p_rating.append(place_rating)
                    place_image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={place_info['image_url']}&key={API_KEY}"
                    p_img.append(place_image_url)
                    place_website = place_info['website']
                    if place_website=='N/A':
                        p_ext_url.append(None)
                    else:
                        p_ext_url.append(place_website)
                    print(f"{idx}. Name: {place_name}")
                    print(f"   Rating: {place_rating}")
                    print(f"   Image URL: {place_image_url}")
                    print(f"   Website: {place_website}")
                for img_url,name,ext_url,rating in zip(p_img,p_name,p_ext_url,p_rating):
                    details.append({"img_url":img_url, "name":name, "ext_url":ext_url, "rating":rating})
                speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                email_without_dot=session["email_without_dot"]
                user_chats=client[email_without_dot]
                collection_name=query_text
                session["collection_name"]=collection_name
                collection_chats=user_chats[collection_name]
                chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"nearby"}
                result_chats=collection_chats.insert_one(chats)
                chats_all=collection_chats.find()
                mychats=[chat for chat in chats_all]
                print(mychats)
                speech_thread.start()
                return render_template("response.html",mychats=mychats)
            else:
                print("No places found nearby.")
    else:
        response_text=llama_response(query_text)
        email_without_dot=session["email_without_dot"]
        user_chats=client[email_without_dot]
        collection_name=query_text
        session["collection_name"]=collection_name
        collection_chats=user_chats[collection_name]
        d_l=[]
        chats={"query_text":query_text,"response_text":response_text,"details":d_l}
        result_chats=collection_chats.insert_one(chats)
        chats_all=collection_chats.find()
        mychats=[chat for chat in chats_all]
        print(mychats)
        speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
        speech_thread.start()
        return render_template("response.html",mychats=mychats)

@app.route('/mic2_response',methods=['POST','GET'])
def mic2_response():
    place_info=None
    session_id = str(uuid.uuid4())
    if request.method == "POST":
        query_text=request.form["query_text"]
    else:
        query_text=speech_to_text()
    response_text = detect_intent_text(project_id, session_id, query_text, language_code)
    keywords=[]
    keywords = extract_keywords(query_text)
    print("Keywords:", keywords)
    user_input =response_text
    match = re.search(r'from\s+(\w+)\s+to\s+(\w+)\s+on\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match1 = re.search(r'in\s+(\w+)\s+for\s+(\d{4}-\d{2}-\d{2})\s+-\s+(\d{4}-\d{2}-\d{2})', user_input, re.IGNORECASE)
    match2 = re.search(r'top\s+(\w+)\s+in\s+(\w+)',user_input, re.IGNORECASE)
    city=None
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
    elif match2 and ("restaurant" or "restaurants" in keywords):
        top_entity = match2.group(1)
        city = match2.group(2)
        print(f"Top entity: {top_entity}")
        print(f"City: {city}")
    else:
        print("Information not found.")
    if "book" in keywords:
        if "flight" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"
                querystring = {
                        "sourceAirportCode": from_place_code,
                        "destinationAirportCode": to_place_code,
                        "date": date,
                        "itineraryType": "ONE_WAY",
                        "sortOrder": "ML_BEST_VALUE",
                        "numAdults": "1",
                        "numSeniors": "0",
                        "classOfService": "ECONOMY",
                        "pageNumber": "1",
                        "currencyCode": "INR"
                    }

                headers = header_trip_adviser
                response = requests.get(url, headers=headers, params=querystring)
                logo_list=[]
                flight_name=[]
                flight_web_url=[]
                flight_price_list=[]
                details=[]
                if response.status_code == 200:
                    data = response.json()
                    if data["status"]:
                        flights = data["data"]["flights"]
                        for i in range(5):
                            display_name = flights[i]["segments"][0]["legs"][0]["marketingCarrier"]["displayName"]
                            flight_name.append(display_name)
                            image_url = flights[i]["segments"][0]["legs"][0]["marketingCarrier"]["logoUrl"]
                            logo_list.append(image_url)
                            flight_url = flights[i]["purchaseLinks"][0]["url"]
                            flight_price = flights[i]["purchaseLinks"][0]["totalPrice"]
                            flight_price_list.append(flight_price)
                            flight_web_url.append(flight_url)
                            print(f"Airline: {display_name}")
                            print(f"Flight URL: {flight_url}")
                            print(f"Logo URL: {image_url}")
                            print(f"Price: {flight_price}")
                            print("-----------")
                        for logo_url,name,ext_url,price in zip(logo_list,flight_name,flight_web_url,flight_price_list):
                            details.append({"img_url":logo_url, "name":name, "ext_url":ext_url, "rating":price})
                        speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                        email_without_dot=session["email_without_dot"]
                        user_chats=client[email_without_dot]
                        collection_name=session["collection_name"]
                        collection_chats=user_chats[collection_name]
                        chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"flight"}
                        result_chats=collection_chats.insert_one(chats)
                        chats_all=collection_chats.find()
                        mychats=[chat for chat in chats_all]
                        print(mychats)
                        speech_thread.start()
                        return render_template("response.html",mychats=mychats)
                    else:
                        print("Error in API response:", data["message"])
                else:
                    print("Error in API request. Status Code:", response.status_code)
            except Exception as e:
                print("Error:",e)
        if "restaurants" or "restaurant" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"

                querystring = {"locationId": get_location_id(city)}

                headers = header_trip_adviser

                response = requests.get(url, headers=headers, params=querystring)

                if response.status_code == 200:
                    data_list = response.json().get("data", [])

                    # Sort restaurants based on rating (highest to lowest)
                    sorted_restaurants = sorted(data_list["data"], key=lambda x: x["averageRating"], reverse=True)

                    # Loop through each restaurant entry in the sorted list
                    names=[]
                    img_list=[]
                    restaurants_rating=[]
                    restaurant_urls=[]
                    details=[]
                    for i in range(5):
                        # Extract and print the details
                        name = sorted_restaurants[i]["name"]
                        names.append(name)
                        img_url = sorted_restaurants[i]["thumbnail"]["photo"]["photoSizes"][0]["url"]
                        reviewpg_url = sorted_restaurants[i]["reviewSnippets"]["reviewSnippetsList"][0]["reviewUrl"]
                        restaurant_urls.append(reviewpg_url)
                        rating = sorted_restaurants[i]["averageRating"]
                        restaurants_rating.append(rating)
                        print("Rating:", rating)
                        print("Name:", name)
                        print("Img URL:", img_url)
                        img_list.append(img_url)
                        print("Page URL:", reviewpg_url)
                        print("-" * 50)
                    for img_url,name,stars,ext_url in zip(img_list,names,restaurants_rating,restaurant_urls):
                        details.append({"img_url":img_url, "name":name, "rating":stars, "ext_url":ext_url})
                    print(details)
                    email_without_dot=session["email_without_dot"]
                    user_chats=client[email_without_dot]
                    collection_name=session["collection_name"]
                    collection_chats=user_chats[collection_name]
                    chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"restaurant"}
                    result_chats=collection_chats.insert_one(chats)
                    chats_all=collection_chats.find()
                    mychats=[chat for chat in chats_all]
                    print(mychats)
                    speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                    speech_thread.start()
                    return render_template("response.html",mychats=mychats)
                else:
                    print("Error:", response.status_code)
                    print(response.text)
            except Exception as e:
                print("Error:",e)
        if "hotel" in keywords:
            try:
                url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotelsByLocation"
                latitude = loc_late
                longitude = loc_longi
                check_in = start_date
                check_out = end_date

                querystring = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "pageNumber": "1",
                    "currencyCode": "INR"
                }

                headers = header_trip_adviser

                response = requests.get(url, headers=headers, params=querystring)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    data_list = response.json().get("data", [])
                    # Sort hotels based on rating (highest to lowest)
                    sorted_hotels = sorted(data_list["data"], key=lambda x: x["bubbleRating"]["rating"], reverse=True)

                    # Loop through each hotel entry in the sorted list
                    hotel_name=[]
                    hotel_ext_url=[]
                    hotel_rating=[]
                    hotel_image=[]
                    details=[]
                    for i in range(5):
                        # Extract and print the details
                        title = sorted_hotels[i]["title"]
                        title=str(title)
                        title=title[3:]
                        hotel_name.append(title)
                        external_url = None
                        try:
                            external_url_1 = sorted_hotels[i]["commerceInfo"]
                            external_url = external_url_1["externalUrl"]
                        except:
                            if external_url is None:
                                external_url_1 = sorted_hotels[i].get("commerceInfo", {})
                                external_url = external_url_1.get("externalUrl","")

                            elif external_url is None:
                                external_url_1 = sorted_hotels[i].get("commerceInfo", {})
                                external_url = external_url_1["externalUrl"]

                            elif external_url is None:
                                external_url_1 = sorted_hotels[i]["commerceInfo"]
                                external_url = external_url_1.get("externalUrl","")
                        img_url0 = sorted_hotels[i]["cardPhotos"][0]["sizes"]["urlTemplate"]
                        img_spl = img_url0.split('?')
                        img_url = img_spl[0]
                        hotel_image.append(img_url)
                        hotel_ext_url.append(external_url)
                        rating = sorted_hotels[i]["bubbleRating"]["rating"]
                        hotel_rating.append(rating)
                        print("Title:", title)
                        print("Rating:", rating)
                        print("External URL:", external_url)

                        print("-" * 50)
                    for name,ext_url,rating,img_url in zip(hotel_name,hotel_ext_url,hotel_rating,hotel_image):
                        details.append({"name":name, "rating":rating, "ext_url":ext_url,"img_url":img_url})
                    email_without_dot=session["email_without_dot"]
                    user_chats=client[email_without_dot]
                    collection_name=session["collection_name"]
                    collection_chats=user_chats[collection_name]
                    chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"hotel"}
                    result_chats=collection_chats.insert_one(chats)
                    chats_all=collection_chats.find()
                    mychats=[chat for chat in chats_all]
                    print(mychats)
                    speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                    speech_thread.start()
                    return render_template("response.html",mychats=mychats)

                else:
                    print("Error:", response.status_code)
                    print(response.text)
            except  Exception as e:
                print("Error:",e)
    elif "nearby" in query_text:
        places_info = find_nearby_places_info(API_KEY, latitude_n, longitude_n, keywords)  # Pass 'keywords' to the function
        if isinstance(places_info, list):
            if places_info:
                response_text=f"Top 5 nearby {keywords[0]} Information:"
                print(response_text)
                p_name=[]
                p_rating=[]
                p_img=[]
                p_ext_url=[]
                details=[]
                for idx, place_info in enumerate(places_info[:5], start=1):
                    place_name = place_info['name']
                    p_name.append(place_name)
                    place_rating = place_info['rating']
                    p_rating.append(place_rating)
                    place_image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={place_info['image_url']}&key={API_KEY}"
                    p_img.append(place_image_url)
                    place_website = place_info['website']
                    if place_website=='N/A':
                        p_ext_url.append(None)
                    else:
                        p_ext_url.append(place_website)
                    print(f"{idx}. Name: {place_name}")
                    print(f"   Rating: {place_rating}")
                    print(f"   Image URL: {place_image_url}")
                    print(f"   Website: {place_website}")
                for img_url,name,ext_url,rating in zip(p_img,p_name,p_ext_url,p_rating):
                    details.append({"img_url":img_url, "name":name, "ext_url":ext_url, "rating":rating})
                speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
                email_without_dot=session["email_without_dot"]
                user_chats=client[email_without_dot]
                collection_name=session["collection_name"]
                session["collection_name"]=collection_name
                collection_chats=user_chats[collection_name]
                chats={"query_text":query_text,"response_text":response_text,"details":details,"type":"nearby"}
                result_chats=collection_chats.insert_one(chats)
                chats_all=collection_chats.find()
                mychats=[chat for chat in chats_all]
                print(mychats)
                speech_thread.start()
                return render_template("response.html",mychats=mychats)
            else:
                print("No places found nearby.")
    else:
        response_text=llama_response(query_text)
        email_without_dot=session["email_without_dot"]
        user_chats=client[email_without_dot]
        collection_name=session["collection_name"]
        collection_chats=user_chats[collection_name]
        d_l=[]
        chats={"query_text":query_text,"response_text":response_text,"details":d_l}
        result_chats=collection_chats.insert_one(chats)
        chats_all=collection_chats.find()
        mychats=[chat for chat in chats_all]
        print(mychats)
        speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
        speech_thread.start()
        return render_template("response.html",mychats=mychats)

def save_image_with_unique_id(file):
    # Generate a unique ID
    unique_id = str(uuid.uuid4())

    # Get the file extension from the uploaded file
    _, file_extension = os.path.splitext(file.filename)

    # Create a new file name with the unique ID and original file extension
    new_file_name = f"{unique_id}{file_extension}"

    # Save the image with the new file name in the uploads folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
    file.save(file_path)
    file_path_single_slash = file_path.replace('\\\\', '\\')

    print(f"Image saved with unique ID: {unique_id}")
    print(file_path_single_slash)
    return file_path_single_slash

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        image = request.files['photo']
        text = request.form['text']
        img_url=[]
        details=[]
        # Save the uploaded image
        new_image_path=save_image_with_unique_id(image)
        new_image_path = new_image_path.replace('\\\\', '\\')
        print("New path:",new_image_path)
        img_url.append(new_image_path)
        print("Saved")
        response = model.generate_content(
            glm.Content(
                parts = [
                    glm.Part(text=text),
                    glm.Part(
                        inline_data=glm.Blob(
                            mime_type='image/jpeg',
                            data=pathlib.Path(new_image_path).read_bytes()
                        )
                    ),
                ],
            ),
            stream=False)
        response_text=response.text
        print(response_text)
        for image_url in zip(img_url):
                    details.append({"img_url":image_url})
        email_without_dot=session["email_without_dot"]
        user_chats=client[email_without_dot]
        collection_name=session["collection_name"]
        collection_chats=user_chats[collection_name]
        chats={"query_text":text,"response_text":response_text,"details":details,"type":"image"}
        result_chats=collection_chats.insert_one(chats)
        img_id=result_chats.inserted_id
        chats_all=collection_chats.find()
        mychats=[chat for chat in chats_all]
        print(mychats)
        speech_thread = threading.Thread(target=perform_text_to_speech, args=(response_text,))
        speech_thread.start()
        print(text)
    return render_template("response.html",mychats=mychats)

if __name__ == '__main__':
    app.secret_key = 'your_secret_key_here'

    app.run(debug=True)
