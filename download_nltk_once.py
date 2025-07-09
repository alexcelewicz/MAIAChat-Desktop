#!/usr/bin/env python3
# download_nltk_once.py - A script to download NLTK resources once and create a flag file

import os
import sys
import nltk
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nltk_download.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("NLTKDownload")

def download_nltk_resources():
    """Download NLTK resources to a local directory and create a flag file."""
    try:
        # Create a local directory for NLTK data
        nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Add the directory to NLTK's search path
        nltk.data.path.append(nltk_data_dir)
        
        # Check for flag file indicating resources are already downloaded
        flag_file = os.path.join(nltk_data_dir, 'nltk_download_complete.flag')
        if os.path.exists(flag_file):
            logger.info("NLTK resources already downloaded (flag file exists)")
            return True
        
        logger.info("Downloading NLTK resources to local directory...")
        
        # List of required NLTK resources
        required_packages = ['punkt', 'punkt_tab', 'averaged_perceptron_tagger', 'stopwords', 'wordnet']
        
        all_success = True
        for package in required_packages:
            try:
                # Check if the resource already exists
                try:
                    if package == 'punkt_tab':
                        nltk.data.find('tokenizers/punkt_tab/english/')
                        logger.info(f"NLTK package already exists: {package}")
                    elif package == 'punkt':
                        nltk.data.find(f'tokenizers/{package}')
                        logger.info(f"NLTK package already exists: {package}")
                    else:
                        nltk.data.find(f'corpora/{package}')
                        logger.info(f"NLTK package already exists: {package}")
                except LookupError:
                    # Download the resource if it doesn't exist
                    logger.info(f"Downloading NLTK package: {package}")
                    nltk.download(package, download_dir=nltk_data_dir, quiet=False)
                    logger.info(f"Successfully downloaded NLTK package: {package}")
            except Exception as e:
                logger.warning(f"Failed to download {package}: {str(e)}")
                all_success = False
        
        # Test if tokenization works
        try:
            from nltk.tokenize import sent_tokenize
            test_text = "This is a test sentence. Here is another one."
            tokens = sent_tokenize(test_text)
            logger.info(f"Tokenization test successful: {tokens}")
        except Exception as e:
            logger.warning(f"Tokenization test failed: {str(e)}")
            all_success = False
        
        if all_success:
            # Create flag file to indicate successful download
            with open(flag_file, 'w') as f:
                f.write(f"NLTK resources downloaded successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("Created flag file to indicate successful download")
        
        logger.info("NLTK resources initialization completed")
        return all_success
    except Exception as e:
        logger.error(f"Error initializing NLTK resources: {str(e)}")
        return False

if __name__ == "__main__":
    # Download NLTK resources
    if not download_nltk_resources():
        logger.error("Failed to download NLTK resources")
        sys.exit(1)
    
    logger.info("NLTK resources downloaded successfully")
    sys.exit(0)
