import modal

# Define the image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi",
        "uvicorn",
        "langchain>=0.2.0,<0.3.0",
        "langchain-openai>=0.1.0,<0.2.0",
        "langchain-community>=0.2.0,<0.3.0",
        "python-dotenv",
        "httpx",
        "pydantic>=2.0.0",
        "python-multipart",
        "tavily-python",
        "amadeus"
    )
    .add_local_dir(
        ".",
        remote_path="/root",
        ignore=["venv", ".git", "__pycache__", ".brain", "server.log"]
    )
)

app = modal.App("sunfar-elite-airline")

@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=600
)
@modal.asgi_app()
def run():
    # Ensure we are in the right directory for relative paths in server.py
    import os
    os.chdir("/root")
    from server import app as fastapi_app
    return fastapi_app
