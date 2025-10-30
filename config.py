import os

ALLOWED_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.pdf', '.docx'}
MAX_FILE_READ_BYTES = 20 * 1024 * 1024  # 20 MB max file limit
DEFAULT_CHUNK_SIZE = 4000  # approx chars per chunk for chunking
SAFE_BASE_DIR = os.path.abspath("./sample_dir")   # restrict to a sample directory for safety

max_iteration = 5  # max number of iterations for the agent to process the user's request

agent_model = "gpt-4o"
summarization_model = "gpt-4o-mini"