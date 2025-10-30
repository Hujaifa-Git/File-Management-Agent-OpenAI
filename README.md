# File Management Agent with OpenAI

An intelligent file management agent powered by OpenAI's GPT-4 that can explore, read, analyze, and search through files in a secure directory environment. The agent provides an interactive terminal interface with real-time tool execution logging.

## Features

- 📁 **Directory Exploration**: List files with pattern matching and recursive search capabilities
- 📄 **Multi-format Support**: Automatically parse and read various file formats:
  - Text files (.txt, .md)
  - CSV files
  - JSON files
  - PDF documents
  - Word documents (.docx)
- 🔍 **Search**: Search for text or regex patterns across multiple files
- 📊 **File Analysis**: Get metadata, summarize content, and analyze multiple files simultaneously
- 🔒 **Security**: All file operations are restricted to a designated safe directory
- 🎨 **Interactive Interface**: Color-coded terminal output with real-time tool execution logs

## Security Notice

This application implements a **SAFE_BASE_DIR** mechanism for security reasons. The agent can only access files within the designated directory and its subdirectories. This prevents unauthorized access to sensitive files on your system. By default, the safe directory is set to `./sample_dir`.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hujaifa-Git/File-Management-Agent-OpenAI.git
   cd File-Management-Agent-OpenAI
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   
   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   
   Create a `.env` file in the project root:
   ```bash
   touch .env
   ```
   
   Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=<your_openai_api_key_here>
   ```

## Configuration

All configuration options are centralized in `config.py` for easy customization:

### Setting the Safe Directory

The safe directory path determines which files the agent can access. By default, it's set to `./sample_dir`:

```python
SAFE_BASE_DIR = os.path.abspath("./sample_dir")
```

You can change this to any directory you want the agent to have access to:

```python
SAFE_BASE_DIR = os.path.abspath("/path/to/your/safe/directory")
```

⚠️ **Important**: The agent will only be able to access files within this directory and its subdirectories.

### Configuring OpenAI Models

The application uses two different OpenAI models that can be configured in `config.py`:

1. **Agent Model** (default: `gpt-4o`): The main model used for understanding user queries and deciding which tools to use.
   ```python
   agent_model = "gpt-4o"
   ```

2. **Summarization Model** (default: `gpt-4o-mini`): A lighter model used for summarizing file contents when using the `read_files_iterative` tool.
   ```python
   summarization_model = "gpt-4o-mini"
   ```

You can change these to any available OpenAI model:

### Other Configuration Options

```python
ALLOWED_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.pdf', '.docx'}  # Supported file types
MAX_FILE_READ_BYTES = 20 * 1024 * 1024  # Maximum file size (20 MB)
DEFAULT_CHUNK_SIZE = 4000  # Characters per chunk for large files

max_iterations = 5  # max number of iterations for the agent to process the user's request
```

## Usage

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Interact with the agent**:
   
   The agent will display the current working directory and wait for your input. You can ask questions like:
   
   - "List all files in the directory"
   - "Show me all folders and subdirectories"
   - "What directories are in folder <folder_name>?"
   - "Show me all PDF files"
   - "Read the products.csv file"
   - "What's in the JSON file in folder <folder_name>?"
   - "Search for 'invoice' in all PDF files"
   - "Summarize all the documents in folder <folder_name>"
   - "Find all files containing the word 'sample'"

3. **Exit the application**:
   
   Type `exit`, `quit`, or `bye` to end the conversation.

## Available Tools

The agent has access to the following tools:

### 1. **list_files**
Lists files in a directory with optional pattern matching and recursive search.

### 2. **list_directories**
Lists directories and subdirectories in a directory. Can list immediate subdirectories or all subdirectories recursively.

### 3. **get_file_metadata**
Returns metadata about a specific file (size, modification time, extension).

### 4. **read_file**
Reads and auto-parses file content. Supports multiple formats with automatic detection.

### 5. **read_files_iterative**
Reads multiple files, chunks large content, and provides integrated summaries.

### 6. **search_in_files**
Searches for text or regex patterns across specified files.

## Tool Execution Logging

The application provides real-time logging of tool executions:

- 🔧 Tool calls are displayed with their arguments
- ✓ Successful executions are marked in green
- ✗ Errors are displayed in red
- All tool results are processed before generating the final response

## Project Structure

```
File-Management-Agent-OpenAI/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings (models, paths, limits)
├── src/
│   ├── tools.py           # Tool definitions and implementations
│   ├── utils.py           # Utility functions
│   └── prompts.py         # System prompts for the agent
├── sample_dir/            # Default safe directory with sample files
│   ├── A/
│   ├── C/
│   └── D/
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

## Sample Directory Contents

The project includes a sample directory with test files:

```
sample_dir/
├── A/
│   ├── B/
│   │   └── invoice_2.pdf
│   └── sample_json.json
├── C/
│   └── invoice_3.pdf
├── D/
│   ├── invoice_1.pdf
│   └── products.csv
└── markdown.md
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is correctly set in the `.env` file
2. **File Access Error**: Check that the SAFE_BASE_DIR exists and has proper permissions
3. **Module Import Error**: Make sure all dependencies are installed in the virtual environment
4. **Model Error**: Ensure you have access to the GPT-4 model on your OpenAI account

### Error Messages

The application provides colored error messages in the terminal:
- Red text indicates errors
- Yellow text shows warnings
- Green text confirms successful operations
