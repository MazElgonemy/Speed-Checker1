import os
import random
import time
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from openai import OpenAI
import json
from functools import wraps
from dotenv import load_dotenv


class Base(DeclarativeBase):
    pass

# Below gets the API key and creates OpenAI client


load_dotenv()
open_ai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=open_ai_api_key
)


matplotlib.use('Agg')

# Initialise extensions


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
bootstrap = Bootstrap5()
login_manager = LoginManager()

# Below is a decorator so that only logged-out users can access certain routes

def login_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# Application factory
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app context
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return app

app = create_app()

# Below is the AI analysis on speed data
def complete(prompt, model="gpt-3.5-turbo", temperature=1, max_tokens=700, stop=None):
    # System prompt with dictionary keys for recommendations
    system_prompt = (
        "I have some internet speed data. I am trying to analyze my internet download speed data. "
        "The units are MBPs download speed. Please provide analysis in the following format:\n\n"
        "Level of variability: (Either Very Low, Low, Moderate, High, or Very High)\n\n"
        "Standard-Deviation-Summary: (Analysis of internet speed variability based on the standard deviation compared to the range.)\n\n"
        "Average-Speed-Summary: (Analysis of quality of broadband based on the average download speed.)\n\n"
        "Recommendations: (Based on the Standard-Deviation-Summary and Average-Speed-Summary provide recommendations on how to improve internet download speed and internet download speed consistency in dictionary format.)\n\n"
        "Example prompt:\n"
        '{"Standard Deviation": 8.1, "Range": 20, "Average Speed": 15.2}\n'
        "Example response:\n"
        '{\n'
        '    "level of variability": "High",\n'
        '    "standard-deviation-summary": "The standard deviation of your internet download speed is 8.1 MBps, which indicates a high level of variability. Standard deviation measures the spread of data points around the mean; a higher value suggests that there are significant fluctuations in your download speeds. Given the range of 20 MBps, this variability means that at times your download speeds might drop significantly below the average or rise well above it, leading to an inconsistent internet experience.",\n'
        '    "average-speed-summary": "The average download speed of 15.2 MBps suggests that your broadband connection is relatively decent for general web browsing, streaming standard definition videos, and downloading files. However, for high-definition streaming, online gaming, or activities that require a stable and higher speed, this might not be optimal, especially considering the high variability. Modern internet usage often demands consistent and higher speeds, and your average speed indicates that while it is serviceable, it may not provide the best experience for more data-intensive tasks.",\n'
        '    "recommendations": {\n'
        '        "upgrade_plan": "Consider a higher-tier internet plan offering speeds in the 50-100 MBps range for a more robust performance.",\n'
        '        "optimize_network_setup": {\n'
        '            "router_placement": "Position your router centrally and away from obstructions.",\n'
        '            "update_router_firmware": "Keep your router firmware updated for improved performance.",\n'
        '            "wired_connection": "Use Ethernet cables for critical devices to reduce variability."\n'
        '        },\n'
        '        "check_network_congestion": {\n'
        '            "bandwidth_management": "Limit the number of active devices during peak times.",\n'
        '            "quality_of_service": "Enable QoS on your router to prioritize important traffic."\n'
        '        },\n'
        '        "isp_assistance": "Contact your ISP to check for line issues or equipment upgrades.",\n'
        '        "consider_alternative_isps": "If current performance is consistently poor, explore other ISPs that might offer better infrastructure and reliability."\n'
        '    }\n'
        '}'
    )

    # Make the API call and handle potential errors
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt),
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop
        )

        response_content = chat_completion.choices[0].message.content

        print(response_content)
        try:
            response_dict = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            return {"error": "Failed to decode JSON response from API"}

        return response_dict

    except Exception as e:
        print(f"Error: {e}")
        return {"error": "An error occurred while calling the API"}



# Below creates user and speeds tables


class Speed(db.Model):
    __tablename__ = "speeds"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="speeds", lazy='subquery')
    speed: Mapped[float] = mapped_column(Float,nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    speeds = relationship("Speed", back_populates="user", cascade="all, delete, delete-orphan")


# Below creates the DB

with app.app_context():
    db.create_all()
    # Adds fake records
    # for _ in range(30):
    #     new_speed = Speed(
    #         user_id=4,
    #         speed=round(random.uniform(41.20, 101.50),2),
    #         date=datetime.now() - timedelta(days=random.randint(0, 300))
    #     )
    #     db.session.add(new_speed)
    # db.session.commit()


# Below is the landing page method


@app.route("/")
def home():
    return render_template("home.html")


# Below is the account page


@app.route("/account", methods=["GET"])
@login_required
def account():
    return render_template("account.html")


# Below is the analysis page


@app.route("/analyse", methods=["GET"])
@login_required
def analyse():
    speeds = Speed.query.filter_by(user_id=current_user.id).order_by(Speed.date.desc()).all()
    speeds_values = []
    for each in speeds:
        speeds_values.append(each.speed)
    df = pd.DataFrame(speeds_values, columns=['Speed Values'])
    average_speed = round(df['Speed Values'].mean(), 2)
    max_speed = round(df['Speed Values'].max(), 2)
    min_speed = round(df['Speed Values'].min(), 2)
    std = round(df['Speed Values'].std(), 2)
    return render_template("analyse.html",speeds=speeds, average_speed=average_speed, max_speed=max_speed, min_speed=min_speed, std=std)


# Below is the AI analysis page

@app.route("/analyse-ai", methods=["GET"])
@login_required
def analyse_ai():
    speeds = Speed.query.filter_by(user_id=current_user.id).order_by(Speed.date.desc()).all()
    speeds_values = []
    for each in speeds:
        speeds_values.append(each.speed)
    if len(speeds_values) < 5:
        message = "There is not enough speed data to analyse yet, please perform more speed tests."
        summary = ""
        recommendations = ""
    else:
        message = ""
        df = pd.DataFrame(speeds_values, columns=['Speed Values'])
        average_speed = round(df['Speed Values'].mean(), 2)
        max_speed = round(df['Speed Values'].max(), 2)
        min_speed = round(df['Speed Values'].min(), 2)
        std = round(df['Speed Values'].std(), 2)
        range = max_speed - min_speed
        prompt_dict = {"Standard Deviation": std, "Range": range, "Average Speed": average_speed}
        response = complete(prompt_dict)
        sd_summary = response["standard-deviation-summary"]
        avg_speed_summary = response["average-speed-summary"]
        recommendations = response["recommendations"]
    return render_template("analyse-ai.html", recommendations=recommendations,sd_summary=sd_summary, avg_speed_summary=avg_speed_summary, message=message)

# Below is the data page


@app.route("/data", methods=["GET", "POST"])
@login_required
def data():
    speeds = Speed.query.filter_by(user_id=current_user.id).order_by(Speed.date.desc()).all()
    if len(speeds) < 1:
        message = "You have no data yet - please run a speed test."
    else:
        message = ""
    return render_template("data.html",speeds=speeds, message=message)


# Below is the line chart page


@app.route("/visualise", methods=["GET", "POST"])
@login_required
def visualise():
    speeds = Speed.query.filter_by(user_id=current_user.id).order_by(Speed.date.desc()).all()

    if len(speeds) < 5:
        message = "There is not enough speed data to visualise yet, please perform more speed tests."
    else:
        message = ""

    speeds_dict = {
        'Date': [each.date.strftime('%Y-%m-%d') for each in speeds],
        'Download Speed': [each.speed for each in speeds]
    }

    df = pd.DataFrame(speeds_dict)
    df['Date'] = pd.to_datetime(df['Date'])

    # Group by two weeks and calculate average if there are more than 20 records
    if len(df) >= 20:
        df.set_index('Date', inplace=True)
        df = df.resample('2W').mean()  # '2W' denotes bi-weekly frequency
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df['Download Speed'], marker='o', linestyle='-', color='#5f9ac6')
    plt.title('Internet Download Speed Over Time', fontsize=15,pad=20)
    plt.xlabel('Date', fontsize=15,labelpad=20)
    plt.ylabel('Average Download Speed (Mbps)', fontsize=15,labelpad=20)
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig("static/images/chart.png")
    plt.close()

    return render_template("visualise.html",message=message)


# Below is for the dashboard and also passing speeds to DB

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        data = request.get_json()
        speed = float(data['speed'])
        current_time = datetime.now()
        new_speed = Speed(
            user=current_user,
            speed=speed,
            date=current_time
        )
        db.session.add(new_speed)
        db.session.commit()
    speeds = Speed.query.filter_by(user_id=current_user.id).order_by(Speed.date.desc()).all()
    if len(speeds) != 0:
        most_recent_speed = speeds[0].speed
    else:
        most_recent_speed = False
    return render_template("dashboard.html", recent_speed=most_recent_speed)


# Below is for the sign-up page

@app.route('/register', methods=["GET", "POST"])
@login_not_required
def register():
    if request.method == "POST":
        # Below searches for existing user by email
        result = db.session.execute(db.select(User).where(User.email == request.form["email"]))
        user = result.scalar()
        # Logic for if the user doesn't exist. Password is hashed, and user it added to DB. Logs in & redirects to home
        if user is None:
            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                email=request.form.get('email'),
                name=request.form.get('name'),
                password=hash_and_salted_password
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("register_success"))
        else:
            # Message for if email already exists
            flash("This email is already registered to a user. Please login.")
            return redirect(url_for("register"))
    return render_template("register.html")


# Below is for logging in


@app.route('/login', methods=["GET", "POST"])
@login_not_required
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user is None:
            flash("This email/password combination was not recognised")
        else:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash("The password is incorrect.")
    return render_template("login.html")


# Below is for changing password


@app.route('/change-password', methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        old_pass = request.form.get('old-password')
        new_pass = request.form.get('new-password')
        if check_password_hash(current_user.password, old_pass):
            hash_and_salted_password = generate_password_hash(
                new_pass,
                method='pbkdf2:sha256',
                salt_length=8)
            current_user.password = hash_and_salted_password
            db.session.commit()
            return redirect(url_for('change_password_success'))
        else:
            flash("Old password is not correct.")
    return render_template("change-password.html")


# Below logs the user out


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Below is success page for changing password


@app.route('/change-password-success')
@login_required
def change_password_success():
    return render_template("change-password-success.html")


# Below is success page for creating account


@app.route('/register-success')
@login_required
def register_success():
    return render_template("register-success.html")


# Below deletes the users account

@app.route('/delete-account')
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    logout_user()
    if user:
        db.session.delete(user)
        db.session.commit()
    return render_template("delete-account-success.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)


