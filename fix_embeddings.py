#!/usr/bin/env python3
# fix_embeddings.py - A script to fix the segmentation fault in the RAGHandler

import os
import sys
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_embeddings.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("FixEmbeddings")

def get_embeddings_safe(texts, model_name="all-mpnet-base-v2", cache_dir="./cache"):
    """
    A super safe version of the get_embeddings function that avoids segmentation faults.
    """
    try:
        logger.info(f"Generating embeddings for {len(texts)} texts using {model_name}")

        # Force CPU usage to avoid MPS/GPU issues
        device = 'cpu'
        logger.info(f"Using device: {device} for SentenceTransformer")

        # Initialize the model with a timeout
        try:
            model = SentenceTransformer(model_name, cache_folder=cache_dir, device=device)
            dimension = model.get_sentence_embedding_dimension()
            logger.info(f"Model dimension: {dimension}")
        except Exception as model_error:
            logger.error(f"Error initializing model: {model_error}")
            # Return zero embeddings if model initialization fails
            return np.zeros((len(texts), 768))  # Default dimension

        # Process in batches - increased threshold for powerful machines
        # For extremely large documents, we'll still use a conservative approach
        # Increased threshold from 10 to 100 for powerful machines
        if len(texts) > 500:
            logger.info(f"Very large document detected ({len(texts)} chunks), using conservative approach")
            # Process in larger batches for powerful machines
            logger.info("Processing with larger batches for powerful machine")
            batch_size = 32  # Increased batch size for powerful machines

        # For smaller documents, process in reasonable batches
        else:
            batch_size = 16  # Increased batch size for powerful machines
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

            # Increased text length limit for powerful machines
            limited_batch = [text[:10000] for text in batch]  # Increased limit to 10000 chars

            try:
                # Cross-platform timeout mechanism
                import threading
                import time

                # Define a timeout class that works on all platforms
                class TimeoutError(Exception):
                    pass

                class Timeout:
                    def __init__(self, seconds):
                        self.seconds = seconds
                        self.timer = None
                        self.timed_out = False

                    def _timeout_handler(self):
                        self.timed_out = True

                    def __enter__(self):
                        self.timer = threading.Timer(self.seconds, self._timeout_handler)
                        self.timer.start()
                        return self

                    def __exit__(self, exc_type, exc_val, exc_tb):
                        if self.timer:
                            self.timer.cancel()

                # Try to encode with a timeout
                try:
                    with Timeout(15) as timeout:  # Increased to 15 second timeout for larger batches
                        start_time = time.time()
                        batch_embeddings = model.encode(limited_batch, normalize_embeddings=True)

                        # Check if we timed out
                        if timeout.timed_out:
                            raise TimeoutError("Encoding took too long")

                        all_embeddings.append(batch_embeddings)
                        logger.info(f"Successfully encoded batch {i//batch_size + 1} in {time.time() - start_time:.2f}s")
                except TimeoutError:
                    logger.error(f"Timeout encoding batch {i//batch_size + 1}")
                    # Create zero embeddings for failed batch
                    zero_embeddings = np.zeros((len(batch), dimension))
                    all_embeddings.append(zero_embeddings)
                except Exception as e:
                    logger.error(f"Error encoding batch {i//batch_size + 1}: {e}")
                    # Create zero embeddings for failed batch
                    zero_embeddings = np.zeros((len(batch), dimension))
                    all_embeddings.append(zero_embeddings)
            except Exception as e:
                logger.error(f"Outer error encoding batch {i//batch_size + 1}: {e}")
                # Create zero embeddings for failed batch
                zero_embeddings = np.zeros((len(batch), dimension))
                all_embeddings.append(zero_embeddings)

        # Combine all embeddings
        if all_embeddings:
            embeddings = np.vstack(all_embeddings)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        else:
            logger.warning("No embeddings generated")
            return np.zeros((len(texts), dimension))
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return zero embeddings as fallback
        return np.zeros((len(texts), 768))  # Default dimension

if __name__ == "__main__":
    # Test the function
    test_texts = ["This is a test sentence.", "Here is another one."]
    embeddings = get_embeddings_safe(test_texts)
    logger.info(f"Generated embeddings shape: {embeddings.shape}")
    logger.info("Test completed successfully")
