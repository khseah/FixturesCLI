import typer
import requests
import pytz
import os
import sys
import certifi
import hashlib
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

cluster_url = os.getenv("CLUSTER_URL")
cluster = MongoClient(cluster_url, tlsCAFile=certifi.where())
db = cluster["FixturesCLI"]
teams = db["FavTeams"]

class Fixture:
    def __init__(self, home, away, time):
        self.home = home
        self.away = away
        self.time = time

app = typer.Typer()

def convert_datetime(date, time, year):   #skysports display times in london time, need to convert to SGT
    i = date.find(' ')
    date = date[i+1:]
    i = date.find(' ')

    month = date[i+1:]
    month = datetime.strptime(month, "%B")
    date = date[:i-2]

    i = time.find(':')
    hour = time[:i]
    minute = time[i+1:]

    time = datetime(int(year), int(month.month), int(date), int(hour), int(minute))
    london_timezone = pytz.timezone("Europe/London")
    local_timezone = pytz.timezone("Asia/Singapore")
    london_time = london_timezone.localize(time)
    local_time = london_time.astimezone(local_timezone)
    return local_time.strftime("%A %d %B'%y %H:%M")

def compare_year(month_year, date):   #only the main header contains the year,
    month = month_year[:-5]           #thus need to check if the year has changed

    i = date.find(' ')
    date = date[i+1:]
    i = date.find(' ')
    date = date[i+1:]

    if (date == month):
        return True
    return False

def check_teamname(team):
    if (team == "paris saint germain"):   #special case
        url = "https://www.skysports.com/paris-st-germain-fixtures"
    else:
        wordcheck = team.find(' ')
    
        if (wordcheck == -1):   #team name is 1 word
            url = f"https://www.skysports.com/{team}-fixtures"
        else:   #team name is 2 words
            team1 = team[:wordcheck]
            team2 = team[wordcheck+1:]
            url = f"https://www.skysports.com/{team1}-{team2}-fixtures"

    result = requests.get(url).text
    doc = BeautifulSoup(result, "html.parser")

    try:   #check if team name is valid
        fixtures_text = doc.find(class_= "fixres__body")
        return fixtures_text
    except:
        return False

def validate(username, password):
    if (teams.count_documents({'Username':username, "Password":password}, limit = 1) == 0):   #username and password not in database
        return False
    return True

@app.command()   #decorator
def fixtures():
    team = input("Which football team's fixtures would you like to find? ")
    fixtures_text = check_teamname(team)
    if not fixtures_text:   #input team is invalid
        print("Unable to find team.")
        return
    
    date = fixtures_text.find_all(class_="fixres__header2")
    month_year = fixtures_text.find_all(class_="fixres__header1")
    match = fixtures_text.find_all(class_="fixres__item")

    j = 0
    print("")
    for i in range(3):   #only print the next 3 fixtures
        home = match[i].find(class_="matches__item-col matches__participant matches__participant--side1").find(class_="swap-text__target").string
        away = match[i].find(class_="matches__item-col matches__participant matches__participant--side2").find(class_="swap-text__target").string
        time = match[i].find(class_="matches__date").string.strip()

        if not compare_year(month_year[j].string, date[i].string):
            j += 1
        
        year = month_year[j].string[-4:]
        time = convert_datetime(date[i].string, time, year)
        index = time.find("'")
        time =  time[:index] + time[index+3:]   #dont print the year
        print(time)

        print(home + "(H)" + " vs " + away + "(A)")
        print("")

@app.command()
def initfav():
    username = input("Choose a username: ").upper()   #convert username to uppercase
    while True:
        if (teams.count_documents({"Username":username}, limit = 1) == 0):   #username not in database
            break
        else:
            username = input("That username is taken, choose another one: ")
    
    password = input("Choose a password: ")
    password = bytes(password, 'utf-8')
    sha256 = hashlib.sha256()
    sha256.update(password)

    favteams = []
    while True:
        favteam = input("Which team would you like to add to favourites? Type 'q' once you're done. ").lower()   #convert team name to lowercase to fit URL format
        if (favteam == 'q'):
            break
        elif not check_teamname(favteam):   #input team is invalid
            print("Unable to find team.")
        else:
            favteams.append(favteam)

    print("")
    for team in favteams:
        post = {"Username":username, "Password":sha256.hexdigest(), "Team":team}
        teams.insert_one(post)
        print(team.title() + " successfully added.")

@app.command()
def addfav():
    username = input("Input your username: ").upper()   #convert username to uppercase
    password = input("Input your password: ")
    password = bytes(password, 'utf-8')
    sha256 = hashlib.sha256()
    sha256.update(password)

    if not validate(username, sha256.hexdigest()):   #check credentials
        print("Invalid credentials.")
        return
    
    favteams = []
    while True:
        favteam = input("Which additional team would you like to add to favourites? Type 'q' once you're done. ").lower()   #convert team name to lowercase to fit URL format
        if (favteam == 'q'):
            break
        elif not check_teamname(favteam):   #input team is invalid
            print("Unable to find team.")
        else:
            favteams.append(favteam)

    print("")
    for team in favteams:
        post = {"Username":username, "Password":sha256.hexdigest(), "Team":team}
        teams.insert_one(post)
        print(team.title() + " successfully added.")

@app.command()
def deletefav():
    username = input("Input your username: ").upper()   #convert username to uppercase
    password = input("Input your password: ")
    password = bytes(password, 'utf-8')
    sha256 = hashlib.sha256()
    sha256.update(password)

    if not validate(username, sha256.hexdigest()):   #check credentials
        print("Invalid credentials.")
        return

    deleteteams = []
    while True:
        deleteteam = input("Which team would you like to delete from favourites? Type 'q' once you're done. ").lower()   #convert team name to lowercase to fit URL format
        if (deleteteam == 'q'):
            break
        elif (teams.count_documents({"Username":username, "Password":sha256.hexdigest(), "Team":deleteteam}, limit = 1) == 0):   #team not in database
            print(deleteteam.title() + " not found.")
        else:
            deleteteams.append(deleteteam)

    print("")
    for team in deleteteams:
        post = {"Username":username, "Password":sha256.hexdigest(), "Team":team}
        teams.delete_one(post)
        print(team.title() + " successfully deleted.")

@app.command()
def listfav():
    username = input("Input your username: ").upper()   #convert username to uppercase
    if (teams.count_documents({'Username':username}, limit = 1) == 0):   #username not in database
        print("Username not found.")
        return

    print("")
    list_teams = teams.find({"Username":username})
    for entry in list_teams:
        print(entry["Team"].title())

@app.command()
def favfixtures():
    username = input("Input your username: ").upper()   #convert username to uppercase
    if (teams.count_documents({'Username':username}, limit = 1) == 0):   #username not in database
        print("Username not found.")
        return
    
    allfixtures = []
    list_teams = teams.find({"Username":username})

    for entry in list_teams:
        fixtures_text = check_teamname(entry["Team"])
        if not fixtures_text:   #input team is invalid
            print("Unable to find " + entry["Team"].title())
            return
        
        date = fixtures_text.find_all(class_="fixres__header2")
        month_year = fixtures_text.find_all(class_="fixres__header1")
        match = fixtures_text.find_all(class_="fixres__item")

        j = 0
        for i in range(3):   #only print the next 3 fixtures
            home = match[i].find(class_="matches__item-col matches__participant matches__participant--side1").find(class_="swap-text__target").string
            away = match[i].find(class_="matches__item-col matches__participant matches__participant--side2").find(class_="swap-text__target").string
            time = match[i].find(class_="matches__date").string.strip()

            if not compare_year(month_year[j].string, date[i].string):
                j += 1
        
            year = month_year[j].string[-4:]
            time = convert_datetime(date[i].string, time, year)

            allfixtures.append(Fixture(home, away, time))
    
    allfixtures.sort(key=lambda x:datetime.strptime(x.time, "%A %d %B'%y %H:%M"))
    print("")

    for obj in allfixtures:
        time = obj.time
        index = time.find("'")
        time =  time[:index] + time[index+3:]   #dont print the year
        print(time)
        print(obj.home + "(H)" + " vs " + obj.away + "(A)")
        print("")

if __name__ == "__main__":
    app()