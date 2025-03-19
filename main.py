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

# Function to get all drivers.
def get_all_drivers() -> list:
    drivers = []
    for driver in drivers_ref.stream():
        driver_data = driver.to_dict()
        driver_data['id'] = driver.id
        drivers.append(driver_data)
    return drivers

# Function to query drivers.
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

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            error_message = None 
        except ValueError as err:
           
            print(str(err))
            user_token = None 
            error_message = str(err) 

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
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    if not user_token:
        return RedirectResponse(url="/")
    
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
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    success_message = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            
            if driver_name_exists(name):
                error_message = f"Driver '{name}' already exists. Please use a different name."
                return templates.TemplateResponse('add_driver.html', {
                    'request': request,
                    'user_token': user_token,
                    'error_message': error_message,
                    'teams': get_all_teams()
                })
            
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
            
            add_driver(driver_data)
            success_message = f"Driver {name} added successfully!"
            
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    if not user_token:
        return RedirectResponse(url="/")
    
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
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
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
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    success_message = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            
            if team_name_exists(name):
                error_message = f"Team '{name}' already exists. Please use a different name."
                return templates.TemplateResponse('add_team.html', {
                    'request': request,
                    'user_token': user_token,
                    'error_message': error_message
                })
            
            team_data = {
                "name": name,
                "year_founded": year_founded,
                "total_pole_positions": total_pole_positions,
                "total_race_wins": total_race_wins,
                "total_constructor_titles": total_constructor_titles,
                "previous_season_position": previous_season_position
            }
            
            add_team(team_data)
            success_message = f"Team {name} added successfully!"
            
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
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
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    

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
    error_message = None
    user_token = None
    results = []

    id_token = request.cookies.get("token")
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    try:
        query_value = value
        if attribute in ["age", "total_pole_positions", "total_race_wins", "total_world_titles", "total_fastest_laps"]:
            query_value = int(value)
        elif attribute == "total_points_scored":
            query_value = float(value)
        
        all_drivers = []
        for driver in drivers_ref.stream():
            driver_data = driver.to_dict()
            driver_data["id"] = driver.id
            all_drivers.append(driver_data)
        
        for driver in all_drivers:
            if attribute in driver:
                driver_value = driver[attribute]
                if isinstance(driver_value, str) and attribute in ["age", "total_pole_positions", "total_race_wins", 
                                                                  "total_world_titles", "total_fastest_laps"]:
                    driver_value = int(driver_value)
                elif isinstance(driver_value, str) and attribute == "total_points_scored":
                    driver_value = float(driver_value)
                
                match_found = False
                if comparison == "lt" and driver_value < query_value:
                    match_found = True
                elif comparison == "eq" and driver_value == query_value:
                    match_found = True
                elif comparison == "gt" and driver_value > query_value:
                    match_found = True
                
                if match_found:
                    if "team_id" in driver:
                        team_doc = teams_ref.document(driver["team_id"]).get()
                        if team_doc.exists:
                            driver["team_name"] = team_doc.to_dict().get("name", "Unknown Team")
                        else:
                            driver["team_name"] = "Unknown Team"
                    else:
                        driver["team_name"] = "No Team"
                    
                    results.append(driver)
        
    except Exception as e:
        error_message = f"Error processing query: {str(e)}"
        print(f"ERROR: {error_message}")
        import traceback
        traceback.print_exc()
    
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

# Function to query teams
def query_teams(attribute: str, comparison: str, value: Any) -> list:
    all_teams = get_all_teams()
    results = []
    
    for team in all_teams:
        if attribute in team:
            if comparison == 'lt' and team[attribute] < value:
                results.append(team)
            elif comparison == 'gt' and team[attribute] > value:
                results.append(team)
            elif comparison == 'eq' and team[attribute] == value:
                results.append(team)
    
    return results

# Routes for querying teams
@app.get("/query-teams", response_class=HTMLResponse)
async def query_teams_form(request: Request):
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    attributes = [
        {"value": "year_founded", "label": "Year Founded"},
        {"value": "total_pole_positions", "label": "Total Pole Positions"},
        {"value": "total_race_wins", "label": "Total Race Wins"},
        {"value": "total_constructor_titles", "label": "Total Constructor Titles"},
        {"value": "previous_season_position", "label": "Previous Season Position"}
    ]
    
    comparisons = [
        {"value": "lt", "label": "Less than"},
        {"value": "eq", "label": "Equal to"},
        {"value": "gt", "label": "Greater than"}
    ]
    
    return templates.TemplateResponse('query_teams.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'attributes': attributes,
        'comparisons': comparisons
    })

@app.post("/query-teams", response_class=HTMLResponse)
async def process_query_teams(
    request: Request,
    attribute: str = Form(...),
    comparison: str = Form(...),
    value: str = Form(...)
):
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    results = []

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    if attribute in ["year_founded", "total_pole_positions", "total_race_wins", 
                     "total_constructor_titles", "previous_season_position"]:
        query_value = int(value)
    else:
        query_value = value
    
    all_teams = []
    for team in teams_ref.stream():
        team_data = team.to_dict()
        team_data["id"] = team.id
        all_teams.append(team_data)
    
    for team in all_teams:
        if attribute in team:
            if comparison == "lt" and team[attribute] < query_value:
                results.append(team)
            elif comparison == "eq" and team[attribute] == query_value:
                results.append(team)
            elif comparison == "gt" and team[attribute] > query_value:
                results.append(team)
    
    attributes = [
        {"value": "year_founded", "label": "Year Founded"},
        {"value": "total_pole_positions", "label": "Total Pole Positions"},
        {"value": "total_race_wins", "label": "Total Race Wins"},
        {"value": "total_constructor_titles", "label": "Total Constructor Titles"},
        {"value": "previous_season_position", "label": "Previous Season Position"}
    ]
    
    comparisons = [
        {"value": "lt", "label": "Less than"},
        {"value": "eq", "label": "Equal to"},
        {"value": "gt", "label": "Greater than"}
    ]
    
    return templates.TemplateResponse('query_teams.html', {
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

# Route for driver details
@app.get("/driver/{driver_id}", response_class=HTMLResponse)
async def driver_details(request: Request, driver_id: str):
    error_message = None
    user_token = None
    driver = None
    team = None

    id_token = request.cookies.get("token")
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    try:
        driver_doc = drivers_ref.document(driver_id).get()
        if driver_doc.exists:
            driver = driver_doc.to_dict()
            driver['id'] = driver_id
            
            if 'team_id' in driver and driver['team_id']:
                team_doc = teams_ref.document(driver['team_id']).get()
                if team_doc.exists:
                    team = team_doc.to_dict()
                    team['id'] = driver['team_id']
        else:
            error_message = "Driver not found"
    except Exception as e:
        error_message = f"Error retrieving driver details: {str(e)}"
    
    return templates.TemplateResponse('driver_details.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'driver': driver,
        'team': team
    })

# Route for team details
@app.get("/team/{team_id}", response_class=HTMLResponse)
async def team_details(request: Request, team_id: str):
    error_message = None
    user_token = None
    team = None
    drivers = []

    id_token = request.cookies.get("token")
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    try:
        team_doc = teams_ref.document(team_id).get()
        if team_doc.exists:
            team = team_doc.to_dict()
            team['id'] = team_id
            
            drivers_query = drivers_ref.where('team_id', '==', team_id).stream()
            for driver_doc in drivers_query:
                driver_data = driver_doc.to_dict()
                driver_data['id'] = driver_doc.id
                drivers.append(driver_data)
        else:
            error_message = "Team not found"
    except Exception as e:
        error_message = f"Error retrieving team details: {str(e)}"
    
    return templates.TemplateResponse('team_details.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'team': team,
        'drivers': drivers
    })

# Routes for editing drivers
@app.get("/edit-driver/{driver_id}", response_class=HTMLResponse)
async def edit_driver_page(request: Request, driver_id: str):
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    driver = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    if not user_token:
        return RedirectResponse(url="/")
    
    try:
        driver_doc = drivers_ref.document(driver_id).get()
        if driver_doc.exists:
            driver = driver_doc.to_dict()
            driver['id'] = driver_id
        else:
            error_message = "Driver not found"
    except Exception as e:
        error_message = f"Error retrieving driver details: {str(e)}"
    
    teams = get_all_teams()
    
    return templates.TemplateResponse('edit_driver.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'driver': driver,
        'teams': teams
    })

@app.post("/edit-driver/{driver_id}", response_class=HTMLResponse)
async def update_driver(
    request: Request,
    driver_id: str,
    name: str = Form(...),
    age: int = Form(...),
    total_pole_positions: int = Form(...),
    total_race_wins: int = Form(...),
    total_points_scored: float = Form(...),
    total_world_titles: int = Form(...),
    total_fastest_laps: int = Form(...),
    team_id: str = Form(...)
):
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None
    success_message = None
    driver = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
            print(str(err))
            error_message = str(err)
    
    if not user_token:
        return RedirectResponse(url="/")
    
    try:
        driver_doc = drivers_ref.document(driver_id).get()
        if not driver_doc.exists:
            error_message = "Driver not found"
        else:
            driver = driver_doc.to_dict()
            driver['id'] = driver_id
            
            if name != driver.get('name', '') and driver_name_exists(name):
                error_message = f"Driver '{name}' already exists. Please use a different name."
            else:
                updated_driver_data = {
                    "name": name,
                    "age": age,
                    "total_pole_positions": total_pole_positions,
                    "total_race_wins": total_race_wins,
                    "total_points_scored": total_points_scored,
                    "total_world_titles": total_world_titles,
                    "total_fastest_laps": total_fastest_laps,
                    "team_id": team_id
                }
                
                drivers_ref.document(driver_id).update(updated_driver_data)
                success_message = f"Driver {name} updated successfully!"
                
                driver.update(updated_driver_data)
    except Exception as e:
        error_message = f"Error updating driver: {str(e)}"
    
    teams = get_all_teams()
    
    return templates.TemplateResponse('edit_driver.html', {
        'request': request,
        'user_token': user_token,
        'error_message': error_message,
        'success_message': success_message,
        'driver': driver,
        'teams': teams
    })