import logging
from main import create_app

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
app = create_app()