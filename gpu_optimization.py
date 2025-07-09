#!/usr/bin/env python3
"""
GPU Optimization Script for Python Agents
This script helps optimize GPU usage for better RAG performance.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GPUOptimization")

def check_gpu_availability():
    """Check GPU availability and capabilities."""
    try:
        import torch
        logger.info("=== GPU Availability Check ===")
        
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        logger.info(f"CUDA Available: {cuda_available}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            logger.info(f"CUDA Device Count: {device_count}")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                device_capability = torch.cuda.get_device_capability(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # GB
                logger.info(f"Device {i}: {device_name}")
                logger.info(f"  - Compute Capability: {device_capability}")
                logger.info(f"  - Total Memory: {memory_total:.1f} GB")
        
        # Check for Apple Silicon (M1/M2)
        mps_available = False
        try:
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                mps_available = True
                logger.info("Apple Silicon (MPS) Available: True")
                logger.info("Device: Apple Silicon GPU")
            else:
                logger.info("Apple Silicon (MPS) Available: False")
        except:
            logger.info("Apple Silicon (MPS) Available: False")
        
        # Check for AMD ROCm (for AMD GPUs)
        rocm_available = False
        try:
            if hasattr(torch.version, 'hip') and torch.version.hip:
                rocm_available = True
                logger.info("AMD ROCm Available: True")
                logger.info("Device: AMD GPU with ROCm support")
            else:
                logger.info("AMD ROCm Available: False")
        except:
            logger.info("AMD ROCm Available: False")
        
        # Check for OpenCL (for integrated graphics)
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            if platforms:
                logger.info("OpenCL Available: True")
                for platform in platforms:
                    logger.info(f"  - Platform: {platform.name}")
                    devices = platform.get_devices()
                    for device in devices:
                        logger.info(f"    - Device: {device.name}")
                        logger.info(f"      Type: {device.type}")
                        if device.type == cl.device_type.GPU:
                            logger.info(f"      Memory: {device.global_mem_size / (1024**3):.1f} GB")
            else:
                logger.info("OpenCL Available: False")
        except ImportError:
            logger.info("OpenCL Available: False (pyopencl not installed)")
        except Exception:
            logger.info("OpenCL Available: False")
        
        return cuda_available or mps_available or rocm_available
        
    except ImportError:
        logger.error("PyTorch not installed. Please install torch to use GPU acceleration.")
        return False
    except Exception as e:
        logger.error(f"Error checking GPU availability: {e}")
        return False

def check_amd_specific_optimizations():
    """Check for AMD-specific optimizations."""
    logger.info("\n=== AMD System Analysis ===")
    
    # Check for AMD Ryzen specific optimizations
    try:
        import platform
        cpu_info = platform.processor()
        logger.info(f"CPU: {cpu_info}")
        
        if "AMD" in cpu_info or "Ryzen" in cpu_info:
            logger.info("✅ AMD Ryzen system detected")
            logger.info("💡 AMD Ryzen with integrated graphics recommendations:")
            logger.info("  - Use CPU mode for best stability")
            logger.info("  - Consider using smaller embedding models")
            logger.info("  - Enable safe retrieval mode for stability")
            logger.info("  - AMD integrated graphics typically work better with CPU mode")
            
            return True
        else:
            logger.info("Not an AMD Ryzen system")
            return False
            
    except Exception as e:
        logger.error(f"Error checking CPU info: {e}")
        return False

def optimize_config_for_amd():
    """Optimize configuration specifically for AMD systems."""
    config_path = Path("config.json")
    
    if not config_path.exists():
        logger.error("config.json not found. Please ensure you're in the correct directory.")
        return False
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info("=== AMD-Optimized Configuration ===")
        
        # AMD-specific optimizations
        config['EMBEDDING_DEVICE'] = 'cpu'  # AMD integrated graphics work better with CPU
        config['RAG_ULTRA_SAFE_MODE'] = True  # Enable safe mode for stability
        config['RAG_SAFE_RETRIEVAL_MODE'] = True  # Enable safe retrieval mode
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info("✅ Configuration optimized for AMD Ryzen:")
        logger.info("  - EMBEDDING_DEVICE set to 'cpu' (best for AMD integrated graphics)")
        logger.info("  - RAG_ULTRA_SAFE_MODE enabled for stability")
        logger.info("  - RAG_SAFE_RETRIEVAL_MODE enabled for stability")
        logger.info("  - This configuration prioritizes stability over raw performance")
        
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing configuration: {e}")
        return False

def optimize_config_for_gpu():
    """Optimize configuration for GPU usage."""
    config_path = Path("config.json")
    
    if not config_path.exists():
        logger.error("config.json not found. Please ensure you're in the correct directory.")
        return False
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info("=== Current Configuration ===")
        logger.info(f"RAG_ULTRA_SAFE_MODE: {config.get('RAG_ULTRA_SAFE_MODE', False)}")
        logger.info(f"RAG_SAFE_RETRIEVAL_MODE: {config.get('RAG_SAFE_RETRIEVAL_MODE', False)}")
        logger.info(f"EMBEDDING_DEVICE: {config.get('EMBEDDING_DEVICE', 'cpu')}")
        
        # Check GPU availability
        gpu_available = check_gpu_availability()
        
        # Check if it's an AMD system
        is_amd = check_amd_specific_optimizations()
        
        # Optimize settings based on system type
        if is_amd:
            logger.info("\n=== AMD System Detected - Using AMD-Optimized Settings ===")
            return optimize_config_for_amd()
        elif gpu_available:
            logger.info("\n=== Optimizing for GPU ===")
            
            # Update configuration for GPU
            config['EMBEDDING_DEVICE'] = 'auto'  # Let the system auto-detect best device
            config['RAG_ULTRA_SAFE_MODE'] = False  # Disable ultra safe mode for better performance
            config['RAG_SAFE_RETRIEVAL_MODE'] = False  # Disable safe retrieval mode for better quality
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info("✅ Configuration optimized for GPU:")
            logger.info("  - EMBEDDING_DEVICE set to 'auto'")
            logger.info("  - RAG_ULTRA_SAFE_MODE disabled")
            logger.info("  - RAG_SAFE_RETRIEVAL_MODE disabled")
            logger.info("  - This will enable GPU acceleration for embeddings")
            
        else:
            logger.info("\n=== Optimizing for CPU ===")
            
            # Update configuration for CPU
            config['EMBEDDING_DEVICE'] = 'cpu'
            config['RAG_ULTRA_SAFE_MODE'] = True  # Enable safe mode for CPU
            config['RAG_SAFE_RETRIEVAL_MODE'] = True  # Enable safe retrieval mode for CPU
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info("✅ Configuration optimized for CPU:")
            logger.info("  - EMBEDDING_DEVICE set to 'cpu'")
            logger.info("  - RAG_ULTRA_SAFE_MODE enabled for stability")
            logger.info("  - RAG_SAFE_RETRIEVAL_MODE enabled for stability")
        
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing configuration: {e}")
        return False

def install_gpu_dependencies():
    """Install GPU dependencies if needed."""
    logger.info("=== GPU Dependencies Check ===")
    
    try:
        import torch
        logger.info("✅ PyTorch is installed")
        
        # Check if CUDA version matches
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            logger.info(f"✅ CUDA version: {cuda_version}")
        else:
            logger.info("⚠️  CUDA not available - using CPU")
            
    except ImportError:
        logger.info("❌ PyTorch not installed")
        logger.info("To install PyTorch with GPU support:")
        logger.info("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        logger.info("  (Replace cu118 with your CUDA version if different)")
        return False
    
    return True

def main():
    """Main function to run GPU optimization."""
    logger.info("🚀 GPU Optimization for Python Agents")
    logger.info("=" * 50)
    
    # Check and install dependencies
    install_gpu_dependencies()
    
    # Optimize configuration
    success = optimize_config_for_gpu()
    
    if success:
        logger.info("\n✅ GPU optimization completed successfully!")
        logger.info("You can now restart the application for the changes to take effect.")
    else:
        logger.error("\n❌ GPU optimization failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 