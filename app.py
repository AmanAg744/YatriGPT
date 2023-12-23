from flask import Flask, request, render_template,url_for,redirect

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
        email=request.form["email"]
        password=request.form["password"]
        confirmPassword=request.form["confirmpassword"]
        print("Email is:",email)
        print("Password is:",password)
        print("Confirm Password is:",confirmPassword)
        if password!=confirmPassword:
            return "Password is not equal to Confirm Password"
        return redirect(url_for("index"))
    return "Failure"

@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST":
        email=request.form["email"]
        password=request.form["password"]
        print(email)
        print(password)
        return "Success"
    return "Failure"

if __name__ == '__main__':
    app.run(debug=True)
