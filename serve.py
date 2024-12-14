import uvicorn
import writer.serve
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
import importlib.util
import os

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
edit_app = writer.serve.get_asgi_app(".", "edit")

# Mount the apps on different sub-paths
app_hub.mount("/run", run_app)
app_hub.mount("/edit", edit_app)

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
@app_hub.get("/")
async def home_page():
    return Response("""
    <h1>Welcome to the Application Hub</h1>
    <p>Navigate to the desired mode:</p>
    <ul>
        <li><a href="/run">Run Mode</a></li>
        <li><a href="/edit">Edit Mode</a></li>
        <li><a href="/components/chatbot.svg">Static Example: Chatbot SVG</a></li>
    </ul>
    """)

# Start the Uvicorn server
if __name__ == "__main__":
    uvicorn.run(
        app_hub,
        host="0.0.0.0",
        port=8080,  # Specify your desired port
        log_level="warning",
        ws_max_size=writer.serve.MAX_WEBSOCKET_MESSAGE_SIZE
    )
