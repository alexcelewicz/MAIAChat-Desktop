#!/usr/bin/env python3
# test_nltk.py - Test NLTK initialization and tokenization

import os
import sys
import nltk
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NLTK-Test")

def test_nltk_resources():
    """Test NLTK resource initialization and tokenization."""
    try:
        # Create a local directory for NLTK data
        nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        nltk.data.path.append(nltk_data_dir)
        
        # List of required NLTK resources
        required_packages = ['punkt', 'punkt_tab', 'averaged_perceptron_tagger', 'stopwords', 'wordnet']
        
        for package in required_packages:
            try:
                # Check if the resource exists
                if package == 'punkt_tab':
                    try:
                        nltk.data.find('tokenizers/punkt_tab/english/')
                        logger.info(f"NLTK package already exists: {package}")
                    except LookupError:
                        logger.info(f"Downloading NLTK package: {package}")
                        nltk.download(package, download_dir=nltk_data_dir, quiet=False)
                elif package == 'punkt':
                    nltk.data.find(f'tokenizers/{package}')
                    logger.info(f"NLTK package already exists: {package}")
                else:
                    nltk.data.find(f'corpora/{package}')
                    logger.info(f"NLTK package already exists: {package}")
            except LookupError:
                # Download the resource if it doesn't exist
                try:
                    logger.info(f"Downloading NLTK package: {package}")
                    nltk.download(package, download_dir=nltk_data_dir, quiet=False)
                except Exception as e:
                    logger.warning(f"Failed to download {package}: {str(e)}")
        
        # Test tokenization
        test_text = "This is a test sentence. Here is another one. And a third!"
        
        # Test with sent_tokenize
        try:
            from nltk.tokenize import sent_tokenize
            tokens = sent_tokenize(test_text)
            logger.info(f"Tokenization successful with sent_tokenize: {tokens}")
        except Exception as e:
            logger.error(f"Tokenization failed with sent_tokenize: {str(e)}")
            
        # Test with PunktSentenceTokenizer
        try:
            from nltk.tokenize.punkt import PunktSentenceTokenizer
            tokenizer = PunktSentenceTokenizer()
            tokens = tokenizer.tokenize(test_text)
            logger.info(f"Tokenization successful with PunktSentenceTokenizer: {tokens}")
        except Exception as e:
            logger.error(f"Tokenization failed with PunktSentenceTokenizer: {str(e)}")
            
        logger.info("NLTK resources test completed")
    except Exception as e:
        logger.error(f"Error testing NLTK resources: {str(e)}")

if __name__ == "__main__":
    test_nltk_resources()
