from flask import Flask, request
import json
import mysql.connector 
from mysql.connector import Error
import os
 

from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sys
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
 
def connect():
    connection = mysql.connector.connect( 
    host="us-cdbr-east-06.cleardb.net", 
    database = "heroku_64af5abe51f278a",
    user="bea146b7617654", 
    password="bd39b28a" 
    )
    cursor = connection.cursor()
    return connection, cursor

def disconnect(connection, cursor):
    cursor.close()
    connection.close()
    return

# mySql_Create_Table_Query = """CREATE TABLE Players ( 
#                             Id int(11) NOT NULL,
#                             Name varchar(250) NOT NULL)"""


# result = cursor.execute(mySql_Create_Table_Query)

add_player = ("INSERT INTO Players "
                "VALUES (%s, %s)")


app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    args = request.args
    print(args)
    return args["num1"] + args["num2"]


@app.route("/add", methods=["POST"])
def add():
    try:
        data = request.form
        print(data)

        connection, cursor = connect()

        player_data = ( str(data["Id"]), data["Name"])
        cursor.execute(add_player, player_data)
        connection.commit()
        disconnect(connection, cursor)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    except Exception as e:
        return str(e)


@app.route("/get", methods=["GET"])
def get():
    try:
        query = "SELECT * FROM Players"
        connection, cursor = connect()

        print(cursor)
        cursor.execute(query)
        res_json = {}
        for (id, name) in cursor:
            print(id, name)
            res_json[id] = name
        
        print(res_json)
        if res_json == {}:
            print("didn't find the entry in db")
        disconnect(connection, cursor)
        return json.dumps(res_json)
    except Exception as e:
        print(e)
        return str(e)
    

@app.route("/get_all", methods=["GET"])
def get_all():
    try:
        query = "SELECT * FROM levels"
        connection, cursor = connect()

        print(cursor)
        cursor.execute(query)
        res_json = []
        for (name, level, company) in cursor:
            print(name, level, company)
            res_json.append(
                {
                    "name": name,
                    "level": level,
                    "company": company
                }
            )
        
        print(res_json)
        disconnect(connection, cursor)
        return json.dumps(res_json)
    except Exception as e:
        print(e)
        return str(e)


@app.route("/get_level", methods = ["GET"])
def get_level():
    try:
        args = request.args
        query = f'SELECT level FROM levels WHERE name = \'{args["name"]}\' AND company = \'{args["company"]}\''

        connection, cursor = connect() 
        
        cursor.execute(query)
        res_json = {}
        for (level) in cursor:
            print(f"level[0] = {level[0]}")
            res_json["level"] = level[0]

        if res_json == {}:
            print("didn't find anything")
            # add value zero to the db
            query = f"INSERT INTO levels VALUES (\'{args['name']}\', 0, \'{args['company']}\')"
            cursor.execute(query)
            connection.commit()
            res_json["level"] = 0
            disconnect(connection, cursor)
            return json.dumps(res_json)

        print(res_json)
        disconnect(connection, cursor)
        return json.dumps(res_json)

    except Exception as e:
        print(e)
        return str(e)

@app.route("/levelup", methods = ["GET"])
def levelup():
    try:
        player_id, company = request.args["name"], request.args["company"]
        # get current level
        query = f'SELECT level FROM levels WHERE name = \'{player_id}\' AND company = \'{company}\''
        connection, cursor = connect() 
        cursor.execute(query)
        for (level) in cursor:
            print(f"level[0] = {level[0]}")
            current_level = level[0]

        query = f"UPDATE levels SET level = {current_level + 1} WHERE name = \'{player_id}\' AND company = \'{company}\'"
        cursor.execute(query)
        connection.commit()
        res_json = {"level": current_level+1}
        print(res_json)
        disconnect(connection, cursor)
        return json.dumps(res_json)
    except Exception as e:
        print(e)
        return str(e)

@app.route("/check_quest", methods = ["GET"])
def check_quest():
    try:
        args = request.args
        player_id, uniq, hashtag = args["name"], args['uniq'], args['hashtag']

        if (get_inst_image(uniq, hashtag)):
            tag_to_cl_map = {
                "starbucks": 0,
                "mcdonalds": 2
            }
            res = brand_predictor("keras1_model.h5", tag_to_cl_map[hashtag]) # 0 = starbucks, 1 = others, 2 = mcdonalds
            if res:
                # get current level
                query = f'SELECT level FROM levels WHERE name = \'{player_id}\' AND company = \'{hashtag}\''
                connection, cursor = connect() 
                cursor.execute(query)
                for (level) in cursor:
                    print(f"level[0] = {level[0]}")
                    current_level = level[0]

                query = f"UPDATE levels SET level = {current_level + 1} WHERE name = \'{player_id}\' AND company = \'{hashtag}\'"
                cursor.execute(query)
                connection.commit()

                return {"message": f"Congratulations! You earned new Level {current_level + 1}"}
            else:
                return {"message": "Your image didn't satisfy the quest"}
        else: 
            return {"message": "Didn't find your post with hashtags"}


    except Exception as e:
        print(e)
        return str(e)

def brand_predictor(Model_path, cafe_num):
  # Load the model
  model = load_model(Model_path)

  data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
  # Replace this with the path to your image
  image = Image.open('input.jpeg')
  size = (224, 224)
  image = ImageOps.fit(image, size, Image.ANTIALIAS)

  #turn the image into a numpy array
  image_array = np.asarray(image)
  # Normalize the image
  normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
  # Load the image into the array
  data[0] = normalized_image_array

  # run the inference
  prediction = model.predict(data)
  prediction = prediction[0]
  if(prediction[0] > prediction[1] and prediction[0] > prediction[2]):
    result = 0
  elif(prediction[1] > prediction[0] and prediction[1] > prediction[2]):
    result = 1
  elif(prediction[2] > prediction[1] and prediction[2] > prediction[1]):
    result = 2
  print(prediction)
  return result == cafe_num

def get_inst_image(uniq, hashtag):

    chrome_options = Options()

    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_options.add_argument("--no-sandbox") # linux only
    # chrome_options.headless = True

    driver = webdriver.Chrome(executable_path=os.environ.get("CHROME_DRIVER_PATH"), chrome_options=chrome_options)

    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(f"https://www.instagram.com/explore/tags/{uniq}/")

    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()
    div = soup.find("div", {"class": "_aagv"})
    if div == None:
        return False
    img = div.find("img")


    link = img["src"]
    text = img["alt"]

    found_tags = [tag.strip() for tag in text[text.find('#')+1:].split('#')]
    brand_tag_included = False

    for tag in found_tags:
        if tag == hashtag:
            brand_tag_included = True

    if not brand_tag_included:
        return False
    print("Start to save image")
    re = requests.get(link)
    with open("input.jpeg", 'wb') as file: #save hello.png to download folder
        file.write(re.content)
        file.close()
    print("Finished to save image")
    return True