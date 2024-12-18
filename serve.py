import uvicorn
import writer.serve
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
import importlib.util
import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status
import secrets


security = HTTPBasic()

# Environment-based credentials
USERNAME = os.getenv("LOGIN", "admin")
PASSWORD = os.getenv("PASSWORD", "password")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Validates the provided username and password.
    """
    is_valid_username = secrets.compare_digest(credentials.username, USERNAME)
    is_valid_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username



# Function to dynamically locate the writer static components directory
def get_writer_static_path():
    # Locate the writer package
    writer_spec = importlib.util.find_spec("writer")
    if not writer_spec or not writer_spec.submodule_search_locations:
        raise RuntimeError("Unable to locate the 'writer' package. Make sure it is installed.")
    
    # Resolve the static components directory
    writer_package_path = writer_spec.submodule_search_locations[0]
    static_components_path = os.path.join(writer_package_path, "static", "components")
    
    # Verify the directory exists
    if not os.path.isdir(static_components_path):
        raise RuntimeError(f"'components' directory not found in {static_components_path}")
    
    return static_components_path

# Root ASGI app to serve as the hub
app_hub = FastAPI(lifespan=writer.serve.lifespan)

# Create two ASGI apps for the same app_path but with different modes
run_app = writer.serve.get_asgi_app(".", "run")
edit_app = writer.serve.get_asgi_app(".", "edit", enable_remote_edit=True, enable_server_setup=True)

# Mount the apps on different sub-paths
app_hub.mount("/run", run_app)
app_hub.mount("/edit", edit_app)
app_hub.mount("/static", StaticFiles(directory="static"), name="static")


# Dynamically locate and mount the Writer static components directory
try:
    components_path = get_writer_static_path()
    app_hub.mount(
        "/components",
        StaticFiles(directory=components_path),
        name="components"
    )
except RuntimeError as e:
    print(f"Error: {e}")

# Root path for navigation
@app_hub.get("/", dependencies=[Depends(authenticate)])
async def home_page():
    """
    Minimalist homepage with just the two cards for navigation.
    """
    return Response("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Writer Demo Application</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #fff;
                color: #000;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
            }
            header {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                padding: 20px;
                background-color: #fff;
            }
            header img {
                height: 50px;
            }
            .container {
                display: flex;
                gap: 20px;
                justify-content: center;
                width: 100%;
                max-width: 800px;
            }
            .card {
                background: #fff;
                border: 1px solid #000;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                transition: transform 0.2s, box-shadow 0.2s;
                cursor: pointer;
                width: 200px;
            }
            .card:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            }
            .card h3 {
                margin: 0;
                font-size: 1.1rem;
                color: #000;
            }
            .card p {
                font-size: 0.9rem;
                color: #555;
                margin-top: 10px;
            }
            a {
                text-decoration: none;
                color: inherit;
            }
        </style>
    </head>
    <body>
        <header>
            <img src="/static/writer_logo.png" alt="Writer Logo">
        </header>
        <div class="container">
            <div class="card">
                <a href="/run" target="_blank">
                    <h3>Run Mode</h3>
                    <p>Test applications in production mode.</p>
                </a>
            </div>
            <div class="card">
                <a href="/edit" target="_blank">
                    <h3>Edit Mode</h3>
                    <p>Develop and edit your workflows.</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """, media_type="text/html")

# Start the Uvicorn server
if __name__ == "__main__":
    # Dynamically select port based on environment
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")  # Use "localhost" for local development if needed
    
    uvicorn.run(
        app_hub,
        host=host,
        port=port,
        log_level="warning",
        ws_max_size=writer.serve.MAX_WEBSOCKET_MESSAGE_SIZE
    )