from flask import Flask, request, render_template,url_for,redirect
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


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
        print("Email is:",email)
        print("Password is:",password)
        print("Confirm Password is:",confirmPassword)
        db=client["YatriGPT"]
        collection=db["UserInfo"]
        query = {"email": email}
        existing_user=collection.find_one(query)
        if email=="" or password =="" or confirmPassword=="" or username=="":
            return "fields are left empty"
        elif existing_user:
            return f"The user with emailid:{email} exists"
        elif password==confirmPassword:
            db=client["YatriGPT"]
            collection=db["UserInfo"]
            credential={"name":f"{username}","email":f"{email}","password":f"{password}"}
            result=collection.insert_one(credential)
            if result.inserted_id:
                print(f"Data inserted successfully. Inserted ID: {result.inserted_id}")
            else:
                print("Failed to inser data")            
        return redirect(url_for("index"))
    return "Failure"

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
            return "fields are left empty"
        elif cred_found:
            print(cred_found["name"])
            user_name=cred_found["name"]
            return f"Welcome {user_name}"
        else:
            return "user not found please signup"
    return "Failure"

if __name__ == '__main__':
    app.run(debug=True)
