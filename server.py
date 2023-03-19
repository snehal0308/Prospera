from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from flask_sqlalchemy import SQLAlchemy
import os
import requests    # ← new import\
import time

# 📁 server.py -----

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
) 


# auth0 routes 

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# create db for tasks  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exp.db'
dbt = SQLAlchemy(app)

	# db model 
class Exp(dbt.Model):
    id = dbt.Column(dbt.Integer, primary_key=True)
    title = dbt.Column(dbt.String(100), nullable=False)
    price = dbt.Column(dbt.Integer(), nullable=False)

    def __repr__(self):
            return f"Post('{self.title}', '{self.content}')"
with app.app_context():
        dbt.create_all()
        print('Created Database!')


@app.route("/")
def home():
    return render_template("index.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/about", methods=["GET", "POST"])
def about():
        return render_template("about.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard(): 
        return render_template("dashboard.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
        return render_template("contact.html")

@app.route("/sms", methods=['POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    msg = request.form.get('Body')

    # Create reply

    exp_list = list()
    exp_price = dbt.session.query(Exp.price).all()
    exp_title = dbt.session.query(Exp.title).all()
    exp_save = dbt.session.query(Exp.price).all()

    exp_list= (exp_title)

    budget = 0 
    total = 0 


    resp = MessagingResponse()
    if 'spent: '.lower() in msg:
        exp_title = msg.split(':')[1]
        exp_price = msg.split(',')[1]

        new_exp = Exp(title=exp_title, price=exp_price)
        dbt.session.add(new_exp)
        dbt.session.commit()

        #for j in exp_price:
         #    for n in j: 
          #       n = int(n)
           #      total = total + n 

        
        resp.message(f"Successfully added a new expenditure")

    elif '-show exp'.lower() in msg:

        for i in exp_list:
            resp.message(f"exp {i}")

    elif 'budget: '.lower() in msg: 
        budget = msg.split(':')[1]

        resp.message(f"Your montly budget set as: {budget}")

    elif '-view'.lower() in msg: 
        for j in exp_price:
            for n in j: 
                n = int(n)
                total = total + n 
        resp.message(f'Budget: {budget} \n Total expediture: {total}')

    elif '-save: '.lower() in msg: 
        save = msg.split(':')[1]

        resp.message(f'savings added: {save}')


    elif '-milestones'.lower() in msg: 
        resp.message(f'Savings milestone: 50/')

    elif '-help'.lower() in msg: 
        resp.message(f'Commands: \n \n spent: [title], [price] = To add a new expenditure \n -show exp = To show all the expenditures \n budget: [budget] = To set a monthly budget \n -view = To view your montly budget and total expenditure\n -save: [amt] - to add your savings')
        
    else:
        resp.message(f"Hii, Use -help to a list of all commands ")



    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)