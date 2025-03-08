
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse 
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests



# define the app that will contain all of our routing for Fast API 
app = FastAPI()

# firebase adapter
firebase_request_adapter = requests.Request()

# define the static and templates directories
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates (directory="templates")


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