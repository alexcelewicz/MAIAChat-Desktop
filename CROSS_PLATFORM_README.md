# Cross-Platform Installation and Usage Guide

This guide provides instructions for installing and running the application on different platforms (Windows, macOS, and Linux).

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

### Step 1: Get the Code

Either clone the repository or download and extract the ZIP file:

```bash
git clone https://github.com/voycel/Multi_Agents_Python_Desktop_app.git
cd Multi_Agents_Python_Desktop_app
```

### Step 2: Install Dependencies

We've provided a cross-platform installation script that will install all required dependencies:

#### On Windows:
```
python install_dependencies.py
```

#### On macOS/Linux:
```
python3 install_dependencies.py
```

This script will:
- Install all required Python packages
- Download necessary NLTK data
- Set up platform-specific configurations

### Step 3: Run the Application

To run the application with our enhanced error handling and cross-platform fixes:

#### On Windows:
```
python start_app.py
```

#### On macOS/Linux:
```
python3 start_app.py
```

## Troubleshooting

### Common Issues

#### 1. Installation Errors

If you encounter errors during installation, check the `install_dependencies.log` file for details.

#### 2. NLTK Data Download Issues

If NLTK data fails to download automatically, you can manually download it:

```python
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('wordnet')
```

#### 3. Application Crashes

If the application crashes despite our fixes:

1. Make sure you're running the application using `start_app.py` and not `main.py`
2. Check the log files (`start_app.log`, `fix_embeddings.log`, etc.) for error messages
3. Try running with a smaller document or fewer documents

#### 4. Platform-Specific Issues

##### Windows:
- If you get "DLL load failed" errors, try installing the Visual C++ Redistributable
- For PyQt6 issues, ensure you have the latest graphics drivers

##### macOS:
- If you get "SSL certificate" errors, you may need to install certificates for Python
- For M1/M2 Macs, ensure you're using Python 3.9+ with native ARM support

##### Linux:
- Ensure you have the required system libraries for PyQt6 (e.g., `sudo apt-get install python3-pyqt6`)
- For GPU support, ensure you have the appropriate CUDA libraries installed

## Advanced Configuration

### Using GPU Acceleration

By default, our fix disables GPU acceleration to ensure cross-platform compatibility. If you want to enable GPU acceleration:

1. Edit `fix_embeddings.py` and change `device = 'cpu'` to:
   - For NVIDIA GPUs: `device = 'cuda'` 
   - For Apple Silicon: `device = 'mps'`

2. Note that enabling GPU acceleration may cause crashes on some systems, especially with large documents.

### Customizing Chunk Size

If you're experiencing memory issues with large documents, you can adjust the chunk size:

1. Edit `rag_handler.py` and change the `chunk_size` parameter in the `RAGHandler` initialization.
2. Smaller values (e.g., 300) will use less memory but may reduce retrieval quality.

## Support

If you encounter any issues not covered in this guide, please:

1. Check the log files for error messages
2. Open an issue on the GitHub repository with detailed information about your system and the error
3. Include the relevant log files with your issue report
