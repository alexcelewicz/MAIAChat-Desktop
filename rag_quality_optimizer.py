#!/usr/bin/env python3
"""
RAG Quality Optimizer for Python Agents
This script helps optimize RAG settings for better response quality.
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
logger = logging.getLogger("RAGQualityOptimizer")

def analyze_rag_configuration():
    """Analyze current RAG configuration and suggest improvements."""
    logger.info("=== RAG Configuration Analysis ===")
    
    # Check config.json
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info("Current RAG Settings:")
        logger.info(f"  - RAG_ULTRA_SAFE_MODE: {config.get('RAG_ULTRA_SAFE_MODE', False)}")
        logger.info(f"  - RAG_SAFE_RETRIEVAL_MODE: {config.get('RAG_SAFE_RETRIEVAL_MODE', False)}")
        logger.info(f"  - EMBEDDING_DEVICE: {config.get('EMBEDDING_DEVICE', 'cpu')}")
        
        # Analyze settings
        issues = []
        recommendations = []
        
        if config.get('RAG_ULTRA_SAFE_MODE', False):
            issues.append("Ultra safe mode is enabled - this may reduce response quality")
            recommendations.append("Consider disabling RAG_ULTRA_SAFE_MODE for better quality")
        
        if config.get('RAG_SAFE_RETRIEVAL_MODE', False):
            issues.append("Safe retrieval mode is enabled - this reduces the number of results")
            recommendations.append("Consider disabling RAG_SAFE_RETRIEVAL_MODE for more comprehensive results")
        
        if config.get('EMBEDDING_DEVICE', 'cpu') == 'cpu':
            recommendations.append("Consider setting EMBEDDING_DEVICE to 'auto' for better performance")
        
        if issues:
            logger.warning("⚠️  Potential Quality Issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        if recommendations:
            logger.info("💡 Recommendations:")
            for rec in recommendations:
                logger.info(f"  - {rec}")
        
        return config
    else:
        logger.error("config.json not found")
        return None

def check_knowledge_base():
    """Check knowledge base status and files."""
    logger.info("\n=== Knowledge Base Analysis ===")
    
    kb_path = Path("./knowledge_base")
    if not kb_path.exists():
        logger.warning("⚠️  Knowledge base directory not found")
        logger.info("💡 To create a knowledge base:")
        logger.info("  1. Add files through the UI")
        logger.info("  2. Or use the RAG handler directly")
        return False
    
    # Check for indexed files
    index_path = kb_path / "faiss_index.bin"
    if not index_path.exists():
        logger.warning("⚠️  No FAISS index found - knowledge base may be empty")
        return False
    
    # Check for file registry
    registry_path = kb_path / "file_registry.json"
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        file_count = len(registry)
        logger.info(f"✅ Knowledge base contains {file_count} indexed files")
        
        # Show some file examples
        if file_count > 0:
            logger.info("Sample indexed files:")
            for i, (filename, info) in enumerate(list(registry.items())[:5]):
                logger.info(f"  - {filename}")
        
        return True
    else:
        logger.warning("⚠️  File registry not found")
        return False

def optimize_rag_settings():
    """Optimize RAG settings for better quality."""
    logger.info("\n=== Optimizing RAG Settings ===")
    
    config_path = Path("config.json")
    if not config_path.exists():
        logger.error("config.json not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Apply quality optimizations
        original_config = config.copy()
        
        # Quality-focused settings
        config['RAG_ULTRA_SAFE_MODE'] = False
        config['RAG_SAFE_RETRIEVAL_MODE'] = False
        config['EMBEDDING_DEVICE'] = 'auto'
        
        # Save optimized config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info("✅ RAG settings optimized for quality:")
        logger.info("  - RAG_ULTRA_SAFE_MODE: False (enables full functionality)")
        logger.info("  - RAG_SAFE_RETRIEVAL_MODE: False (allows more comprehensive results)")
        logger.info("  - EMBEDDING_DEVICE: auto (enables GPU acceleration when available)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing RAG settings: {e}")
        return False

def check_worker_settings():
    """Check and suggest improvements for Worker RAG settings."""
    logger.info("\n=== Worker RAG Settings Analysis ===")
    
    worker_path = Path("worker.py")
    if not worker_path.exists():
        logger.error("worker.py not found")
        return
    
    try:
        with open(worker_path, 'r') as f:
            content = f.read()
        
        # Check current settings
        if 'n_results=15' in content:
            logger.info("Current n_results: 15")
            logger.info("💡 Recommendation: Increase to 25 for more comprehensive results")
        
        if 'alpha=0.5' in content:
            logger.info("Current alpha: 0.5")
            logger.info("💡 Recommendation: Increase to 0.6 for better semantic balance")
        
        if 'importance_score": 0.5' in content:
            logger.info("Current importance_score filter: 0.5")
            logger.info("💡 Recommendation: Reduce to 0.3 for less restrictive filtering")
        
        if 'max_tokens=4096' in content:
            logger.info("Current RAG content limit: 4096 tokens")
            logger.info("💡 Recommendation: Increase to 8192 for more comprehensive context")
        
    except Exception as e:
        logger.error(f"Error analyzing worker settings: {e}")

def generate_quality_report():
    """Generate a comprehensive quality report."""
    logger.info("\n" + "="*60)
    logger.info("📊 RAG QUALITY OPTIMIZATION REPORT")
    logger.info("="*60)
    
    # Analyze configuration
    config = analyze_rag_configuration()
    
    # Check knowledge base
    kb_status = check_knowledge_base()
    
    # Check worker settings
    check_worker_settings()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📋 SUMMARY")
    logger.info("="*60)
    
    if config:
        safe_mode = config.get('RAG_ULTRA_SAFE_MODE', False)
        safe_retrieval = config.get('RAG_SAFE_RETRIEVAL_MODE', False)
        device = config.get('EMBEDDING_DEVICE', 'cpu')
        
        quality_score = 0
        if not safe_mode:
            quality_score += 25
        if not safe_retrieval:
            quality_score += 25
        if device == 'auto':
            quality_score += 25
        if kb_status:
            quality_score += 25
        
        logger.info(f"Overall RAG Quality Score: {quality_score}/100")
        
        if quality_score >= 75:
            logger.info("✅ Excellent RAG configuration!")
        elif quality_score >= 50:
            logger.info("⚠️  Good RAG configuration with room for improvement")
        else:
            logger.info("❌ RAG configuration needs optimization")
    
    logger.info("\n💡 Next Steps:")
    logger.info("1. Run this script with --optimize to apply quality improvements")
    logger.info("2. Ensure your knowledge base contains relevant files")
    logger.info("3. Test RAG functionality with a query")
    logger.info("4. Monitor response quality and adjust settings as needed")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--optimize':
        logger.info("🚀 RAG Quality Optimization")
        logger.info("=" * 50)
        
        # Optimize settings
        success = optimize_rag_settings()
        
        if success:
            logger.info("\n✅ RAG quality optimization completed!")
            logger.info("Restart the application for changes to take effect.")
        else:
            logger.error("\n❌ RAG optimization failed.")
    else:
        # Generate report
        generate_quality_report()

if __name__ == "__main__":
    main() 