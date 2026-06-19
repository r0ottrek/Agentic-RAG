import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

DATA_DIR = "data"
QDRANT_PATH = "qdrant_data"
COLLECTION = "homelab"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
GEN_MODEL = "gemini-2.5-flash"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 5
