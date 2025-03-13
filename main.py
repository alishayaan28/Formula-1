from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from typing import Dict, Any
import os

# define the app that will contain all of our routing for Fast API 
app = FastAPI()

# firebase adapter
firebase_request_adapter = requests.Request()

# define the static and templates directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

# Initialize Firestore client
db = firestore.Client()

# References to Firestore collections
drivers_ref = db.collection('drivers')
teams_ref = db.collection('teams')

# Driver model
class Driver:
    def __init__(
        self,
        name: str,
        age: int,
        total_pole_positions: int,
        total_race_wins: int,
        total_points_scored: float,
        total_world_titles: int,
        total_fastest_laps: int,
        team_id: str 
    ):
        self.name = name
        self.age = age
        self.total_pole_positions = total_pole_positions
        self.total_race_wins = total_race_wins
        self.total_points_scored = total_points_scored
        self.total_world_titles = total_world_titles
        self.total_fastest_laps = total_fastest_laps
        self.team_id = team_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "total_pole_positions": self.total_pole_positions,
            "total_race_wins": self.total_race_wins,
            "total_points_scored": self.total_points_scored,
            "total_world_titles": self.total_world_titles,
            "total_fastest_laps": self.total_fastest_laps,
            "team_id": self.team_id
        }

# Team model
class Team:
    def __init__(
        self,
        name: str,
        year_founded: int,
        total_pole_positions: int,
        total_race_wins: int,
        total_constructor_titles: int,
        previous_season_position: int
    ):
        self.name = name
        self.year_founded = year_founded
        self.total_pole_positions = total_pole_positions
        self.total_race_wins = total_race_wins
        self.total_constructor_titles = total_constructor_titles
        self.previous_season_position = previous_season_position
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "year_founded": self.year_founded,
            "total_pole_positions": self.total_pole_positions,
            "total_race_wins": self.total_race_wins,
            "total_constructor_titles": self.total_constructor_titles,
            "previous_season_position": self.previous_season_position
        }

# Function to add a driver
def add_driver(driver_data: Dict[str, Any]) -> str:
    doc_ref = drivers_ref.document()
    doc_ref.set(driver_data)
    return doc_ref.id

# Function to add a team
def add_team(team_data: Dict[str, Any]) -> str:
    doc_ref = teams_ref.document()
    doc_ref.set(team_data)
    return doc_ref.id

# Function to get all teams
def get_all_teams() -> list:
    teams = []
    for team in teams_ref.stream():
        team_data = team.to_dict()
        team_data['id'] = team.id
        teams.append(team_data)
    return teams

# Function to get all drivers
def get_all_drivers() -> list:
    drivers = []
    for driver in drivers_ref.stream():
        driver_data = driver.to_dict()
        driver_data['id'] = driver.id
        drivers.append(driver_data)
    return drivers

# Function to query drivers
def query_drivers(attribute: str, comparison: str, value: Any) -> list:
    all_drivers = get_all_drivers()
    results = []
    
    for driver in all_drivers:
        
        if attribute in driver:
            if comparison == 'lt' and driver[attribute] < value:
                results.append(driver)
            elif comparison == 'gt' and driver[attribute] > value:
                results.append(driver)
            elif comparison == 'eq' and driver[attribute] == value:
                results.append(driver)
    
    return results

# Function to check if a team name already exists
def team_name_exists(name: str) -> bool:
    teams = get_all_teams()
    for team in teams:
        if team.get('name', '').lower() == name.lower():
            return True
    return False

# Function to check if a driver name already exists
def driver_name_exists(name: str) -> bool:
    drivers = get_all_drivers()
    for driver in drivers:
        if driver.get('name', '').lower() == name.lower():
            return True
    return False

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            error_message = None  # No error if verification succeeds
        except ValueError as err:
            # Log the error message to the console for debugging
            print(str(err))
            user_token = None  # Ensure user_token is always defined
            error_message = str(err)  # Store the error message

    # Always return a response, even if there's no token
    return templates.TemplateResponse('main.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message
    })

# Route for logout
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(key="token")
    return response

# Routes for adding drivers
@app.get("/add-driver", response_class=HTMLResponse)
async def add_driver_page(request: Request):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    
    # Get all teams for dropdown selection
    teams = get_all_teams()
    
    return templates.TemplateResponse('add_driver.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'teams': teams
    })

@app.post("/add-driver", response_class=HTMLResponse)
async def create_driver(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    total_pole_positions: int = Form(...),
    total_race_wins: int = Form(...),
    total_points_scored: float = Form(...),
    total_world_titles: int = Form(...),
    total_fastest_laps: int = Form(...),
    team_id: str = Form(...)
):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    success_message = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            
            # Check if driver name already exists
            if driver_name_exists(name):
                error_message = f"Driver '{name}' already exists. Please use a different name."
                return templates.TemplateResponse('add_driver.html', {
                    'request': request,
                    'user_token': user_token,
                    'error_message': error_message,
                    'teams': get_all_teams()
                })
            
            # Create driver data dictionary
            driver_data = {
                "name": name,
                "age": age,
                "total_pole_positions": total_pole_positions,
                "total_race_wins": total_race_wins,
                "total_points_scored": total_points_scored,
                "total_world_titles": total_world_titles,
                "total_fastest_laps": total_fastest_laps,
                "team_id": team_id
            }
            
            # Add driver to Firestore
            add_driver(driver_data)
            success_message = f"Driver {name} added successfully!"
            
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    
    # Get all teams for dropdown selection
    teams = get_all_teams()
    
    return templates.TemplateResponse('add_driver.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'success_message': success_message,
        'teams': teams
    })

# Routes for adding teams
@app.get("/add-team", response_class=HTMLResponse)
async def add_team_page(request: Request):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse('add_team.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message
    })

@app.post("/add-team", response_class=HTMLResponse)
async def create_team(
    request: Request,
    name: str = Form(...),
    year_founded: int = Form(...),
    total_pole_positions: int = Form(...),
    total_race_wins: int = Form(...),
    total_constructor_titles: int = Form(...),
    previous_season_position: int = Form(...)
):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    success_message = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            
            # Check if team name already exists
            if team_name_exists(name):
                error_message = f"Team '{name}' already exists. Please use a different name."
                return templates.TemplateResponse('add_team.html', {
                    'request': request,
                    'user_token': user_token,
                    'error_message': error_message
                })
            
            # Create team data dictionary
            team_data = {
                "name": name,
                "year_founded": year_founded,
                "total_pole_positions": total_pole_positions,
                "total_race_wins": total_race_wins,
                "total_constructor_titles": total_constructor_titles,
                "previous_season_position": previous_season_position
            }
            
            # Add team to Firestore
            add_team(team_data)
            success_message = f"Team {name} added successfully!"
            
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    
    return templates.TemplateResponse('add_team.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'success_message': success_message
    })

# Routes for querying drivers
@app.get("/query-drivers", response_class=HTMLResponse)
async def query_drivers_form(request: Request):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    

    attributes = [
        {"value": "age", "label": "Age"},
        {"value": "total_pole_positions", "label": "Total Pole Positions"},
        {"value": "total_race_wins", "label": "Total Race Wins"},
        {"value": "total_points_scored", "label": "Total Points Scored"},
        {"value": "total_world_titles", "label": "Total World Titles"},
        {"value": "total_fastest_laps", "label": "Total Fastest Laps"}
    ]
    
    comparisons = [
        {"value": "lt", "label": "Less than"},
        {"value": "eq", "label": "Equal to"},
        {"value": "gt", "label": "Greater than"}
    ]
    
    return templates.TemplateResponse('query.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'attributes': attributes,
        'comparisons': comparisons
    })

@app.post("/query-drivers", response_class=HTMLResponse)
async def process_query_drivers(
    request: Request,
    attribute: str = Form(...),
    comparison: str = Form(...),
    value: str = Form(...)
):
    # Retrieve the token from cookies
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    results = []

    # If we have an ID token, verify it against Firebase.
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            
            
            if attribute in ["age", "total_pole_positions", "total_race_wins", "total_world_titles", "total_fastest_laps"]:
                query_value = int(value)
            elif attribute == "total_points_scored":
                query_value = float(value)
            else:
                query_value = value
            
           
            all_drivers = []
            for driver in drivers_ref.stream():
                driver_data = driver.to_dict()
                driver_data["id"] = driver.id
                all_drivers.append(driver_data)
            
            # Apply filter based on comparison
            for driver in all_drivers:
                if attribute in driver:
                    if comparison == "lt" and driver[attribute] < query_value:
                        results.append(driver)
                    elif comparison == "eq" and driver[attribute] == query_value:
                        results.append(driver)
                    elif comparison == "gt" and driver[attribute] > query_value:
                        results.append(driver)
            
            # Get team info for each driver in results
            for driver in results:
                if "team_id" in driver:
                    team_doc = teams_ref.document(driver["team_id"]).get()
                    if team_doc.exists:
                        driver["team_name"] = team_doc.to_dict().get("name", "Unknown Team")
                    else:
                        driver["team_name"] = "Unknown Team"
            
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    # If not logged in, redirect to home
    if not user_token:
        return RedirectResponse(url="/")
    
    
    attributes = [
        {"value": "age", "label": "Age"},
        {"value": "total_pole_positions", "label": "Total Pole Positions"},
        {"value": "total_race_wins", "label": "Total Race Wins"},
        {"value": "total_points_scored", "label": "Total Points Scored"},
        {"value": "total_world_titles", "label": "Total World Titles"},
        {"value": "total_fastest_laps", "label": "Total Fastest Laps"}
    ]
    
    comparisons = [
        {"value": "lt", "label": "Less than"},
        {"value": "eq", "label": "Equal to"},
        {"value": "gt", "label": "Greater than"}
    ]
    
    return templates.TemplateResponse('query.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'attributes': attributes,
        'comparisons': comparisons,
        'results': results,
        'query': {
            'attribute': attribute,
            'comparison': comparison,
            'value': value
        }
    })