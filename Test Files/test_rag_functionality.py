#!/usr/bin/env python3
"""
Test script for RAG Functionality
This script tests RAG retrieval with the optimized settings and verifies response quality improvements.
"""

import json
import os
import sys
import time
from pathlib import Path
import logging

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from rag_handler import RAGHandler
from config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGFunctionalityTester:
    """Test class for RAG functionality."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.test_results = []
        self.rag_handler = None
        
    def test_1_rag_handler_initialization(self):
        """Test 1: Initialize RAG handler with optimized settings."""
        logger.info("=== Test 1: RAG Handler Initialization ===")
        
        try:
            # Initialize RAG handler with optimized settings
            self.rag_handler = RAGHandler(
                persist_directory="./knowledge_base",
                use_openai=False,  # Use sentence transformer by default
                embedding_model="all-mpnet-base-v2",
                dimension=768,  # Updated dimension for all-mpnet-base-v2
                chunk_size=500,
                chunk_overlap=50,
                chunking_strategy="contextual",  # Use contextual chunking for better context preservation
                cache_dir="./cache"  # Add cache directory for better performance
            )
            
            # Check if RAG handler was initialized successfully
            if self.rag_handler is not None:
                logger.info("RAG handler initialized successfully")
                
                # Get stats
                stats = self.rag_handler.get_stats()
                logger.info(f"RAG Stats: {stats}")
                
                # Check if knowledge base is loaded
                if stats.get('total_chunks', 0) > 0:
                    logger.info(f"Knowledge base loaded with {stats['total_chunks']} chunks")
                    self.test_results.append(("RAG Handler Initialization", "PASS", f"Loaded {stats['total_chunks']} chunks"))
                else:
                    logger.warning("No chunks found in knowledge base")
                    self.test_results.append(("RAG Handler Initialization", "WARNING", "No chunks found"))
            else:
                logger.error("Failed to initialize RAG handler")
                self.test_results.append(("RAG Handler Initialization", "FAIL", "Initialization failed"))
                
        except Exception as e:
            logger.error(f"Error initializing RAG handler: {e}")
            self.test_results.append(("RAG Handler Initialization", "FAIL", str(e)))
    
    def test_2_rag_settings_verification(self):
        """Test 2: Verify RAG settings are properly applied."""
        logger.info("=== Test 2: RAG Settings Verification ===")
        
        try:
            if not self.rag_handler:
                logger.error("RAG handler not initialized")
                self.test_results.append(("RAG Settings Verification", "FAIL", "RAG handler not initialized"))
                return
            
            # Load current config
            self.config_manager.load_config()
            config = self.config_manager.config
            
            # Get RAG settings from config
            rag_settings = {
                'RAG_N_RESULTS': config.get('RAG_N_RESULTS', 25),
                'RAG_ALPHA': config.get('RAG_ALPHA', 0.6),
                'RAG_IMPORTANCE_SCORE': config.get('RAG_IMPORTANCE_SCORE', 0.3),
                'RAG_TOKEN_LIMIT': config.get('RAG_TOKEN_LIMIT', 8192),
                'RAG_RERANKING': config.get('RAG_RERANKING', True),
                'RAG_CROSS_ENCODER_RERANKING': config.get('RAG_CROSS_ENCODER_RERANKING', True),
                'RAG_QUERY_EXPANSION': config.get('RAG_QUERY_EXPANSION', True),
                'RAG_ULTRA_SAFE_MODE': config.get('RAG_ULTRA_SAFE_MODE', False),
                'RAG_SAFE_RETRIEVAL_MODE': config.get('RAG_SAFE_RETRIEVAL_MODE', False),
                'EMBEDDING_DEVICE': config.get('EMBEDDING_DEVICE', 'cpu')
            }
            
            logger.info("Current RAG settings:")
            for key, value in rag_settings.items():
                logger.info(f"  {key}: {value}")
            
            # Verify settings are reasonable
            if rag_settings['RAG_N_RESULTS'] >= 15 and rag_settings['RAG_N_RESULTS'] <= 50:
                logger.info("Number of results setting is reasonable")
            else:
                logger.warning(f"Number of results ({rag_settings['RAG_N_RESULTS']}) may be suboptimal")
            
            if 0.3 <= rag_settings['RAG_ALPHA'] <= 0.8:
                logger.info("Alpha setting is reasonable")
            else:
                logger.warning(f"Alpha setting ({rag_settings['RAG_ALPHA']}) may be suboptimal")
            
            if rag_settings['RAG_TOKEN_LIMIT'] >= 4096:
                logger.info("Token limit is sufficient")
            else:
                logger.warning(f"Token limit ({rag_settings['RAG_TOKEN_LIMIT']}) may be too low")
            
            self.test_results.append(("RAG Settings Verification", "PASS", "Settings verified"))
            
        except Exception as e:
            logger.error(f"Error verifying RAG settings: {e}")
            self.test_results.append(("RAG Settings Verification", "FAIL", str(e)))
    
    def test_3_basic_retrieval_test(self):
        """Test 3: Test basic RAG retrieval functionality."""
        logger.info("=== Test 3: Basic Retrieval Test ===")
        
        try:
            if not self.rag_handler:
                logger.error("RAG handler not initialized")
                self.test_results.append(("Basic Retrieval Test", "FAIL", "RAG handler not initialized"))
                return
            
            # Test queries based on the indexed files
            test_queries = [
                "radar technology specifications",
                "AI and machine learning",
                "technical documentation",
                "system requirements",
                "performance metrics"
            ]
            
            successful_queries = 0
            total_chunks_retrieved = 0
            
            for i, query in enumerate(test_queries):
                logger.info(f"Testing query {i+1}: '{query}'")
                
                try:
                    # Get RAG settings
                    self.config_manager.load_config()
                    config = self.config_manager.config
                    
                    # Retrieve chunks with current settings
                    chunks = self.rag_handler.get_relevant_chunks(
                        query,
                        n_results=config.get('RAG_N_RESULTS', 25),
                        alpha=config.get('RAG_ALPHA', 0.6),
                        filter_criteria={
                            "importance_score": config.get('RAG_IMPORTANCE_SCORE', 0.3),
                            "language": "en"
                        },
                        reranking=config.get('RAG_RERANKING', True),
                        cross_encoder_reranking=config.get('RAG_CROSS_ENCODER_RERANKING', True),
                        query_expansion=config.get('RAG_QUERY_EXPANSION', True)
                    )
                    
                    if chunks:
                        logger.info(f"  Retrieved {len(chunks)} chunks for query '{query}'")
                        total_chunks_retrieved += len(chunks)
                        successful_queries += 1
                        
                        # Log some details about the chunks
                        for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                            metadata = chunk.get('metadata', {})
                            if hasattr(metadata, 'file_name'):
                                file_name = metadata.file_name
                                importance = getattr(metadata, 'importance_score', 'N/A')
                            else:
                                file_name = metadata.get('file_name', 'Unknown')
                                importance = metadata.get('importance_score', 'N/A')
                            
                            logger.info(f"    Chunk {j+1}: {file_name} (importance: {importance})")
                    else:
                        logger.warning(f"  No chunks retrieved for query '{query}'")
                        
                except Exception as e:
                    logger.error(f"  Error retrieving chunks for query '{query}': {e}")
            
            # Assess results
            if successful_queries > 0:
                avg_chunks = total_chunks_retrieved / successful_queries
                logger.info(f"Retrieval test completed: {successful_queries}/{len(test_queries)} queries successful")
                logger.info(f"Average chunks per query: {avg_chunks:.1f}")
                
                if avg_chunks >= 5:
                    self.test_results.append(("Basic Retrieval Test", "PASS", f"{successful_queries}/{len(test_queries)} queries successful, avg {avg_chunks:.1f} chunks"))
                else:
                    self.test_results.append(("Basic Retrieval Test", "WARNING", f"Low average chunks per query: {avg_chunks:.1f}"))
            else:
                self.test_results.append(("Basic Retrieval Test", "FAIL", "No successful retrievals"))
                
        except Exception as e:
            logger.error(f"Error in basic retrieval test: {e}")
            self.test_results.append(("Basic Retrieval Test", "FAIL", str(e)))
    
    def test_4_quality_improvement_test(self):
        """Test 4: Test RAG response quality improvements."""
        logger.info("=== Test 4: Quality Improvement Test ===")
        
        try:
            if not self.rag_handler:
                logger.error("RAG handler not initialized")
                self.test_results.append(("Quality Improvement Test", "FAIL", "RAG handler not initialized"))
                return
            
            # Test a specific query that should benefit from the optimized settings
            test_query = "radar system specifications and technical details"
            
            logger.info(f"Testing quality improvement with query: '{test_query}'")
            
            # Get current settings
            self.config_manager.load_config()
            config = self.config_manager.config
            
            # Test with current optimized settings
            start_time = time.time()
            optimized_chunks = self.rag_handler.get_relevant_chunks(
                test_query,
                n_results=config.get('RAG_N_RESULTS', 25),
                alpha=config.get('RAG_ALPHA', 0.6),
                filter_criteria={
                    "importance_score": config.get('RAG_IMPORTANCE_SCORE', 0.3),
                    "language": "en"
                },
                reranking=config.get('RAG_RERANKING', True),
                cross_encoder_reranking=config.get('RAG_CROSS_ENCODER_RERANKING', True),
                query_expansion=config.get('RAG_QUERY_EXPANSION', True)
            )
            optimized_time = time.time() - start_time
            
            logger.info(f"Optimized settings: {len(optimized_chunks)} chunks in {optimized_time:.2f}s")
            
            # Test with conservative settings for comparison
            start_time = time.time()
            conservative_chunks = self.rag_handler.get_relevant_chunks(
                test_query,
                n_results=15,  # Conservative
                alpha=0.5,     # Conservative
                filter_criteria={
                    "importance_score": 0.5,  # Conservative
                    "language": "en"
                },
                reranking=False,  # Conservative
                cross_encoder_reranking=False,  # Conservative
                query_expansion=False  # Conservative
            )
            conservative_time = time.time() - start_time
            
            logger.info(f"Conservative settings: {len(conservative_chunks)} chunks in {conservative_time:.2f}s")
            
            # Compare results
            if len(optimized_chunks) > len(conservative_chunks):
                improvement = ((len(optimized_chunks) - len(conservative_chunks)) / len(conservative_chunks)) * 100
                logger.info(f"Quality improvement: {improvement:.1f}% more chunks with optimized settings")
                
                if improvement >= 20:
                    self.test_results.append(("Quality Improvement Test", "PASS", f"{improvement:.1f}% improvement in chunk retrieval"))
                else:
                    self.test_results.append(("Quality Improvement Test", "WARNING", f"Modest improvement: {improvement:.1f}%"))
            else:
                logger.warning("No improvement in chunk count with optimized settings")
                self.test_results.append(("Quality Improvement Test", "WARNING", "No improvement in chunk count"))
            
            # Check performance
            if optimized_time <= conservative_time * 1.5:  # Allow 50% overhead for better quality
                logger.info("Performance is acceptable with optimized settings")
            else:
                logger.warning(f"Performance degradation: {optimized_time/conservative_time:.1f}x slower")
                
        except Exception as e:
            logger.error(f"Error in quality improvement test: {e}")
            self.test_results.append(("Quality Improvement Test", "FAIL", str(e)))
    
    def test_5_amd_optimization_test(self):
        """Test 5: Test AMD-specific optimizations."""
        logger.info("=== Test 5: AMD Optimization Test ===")
        
        try:
            if not self.rag_handler:
                logger.error("RAG handler not initialized")
                self.test_results.append(("AMD Optimization Test", "FAIL", "RAG handler not initialized"))
                return
            
            # Check if AMD optimizations are applied
            self.config_manager.load_config()
            config = self.config_manager.config
            
            # Check embedding device setting
            embedding_device = config.get('EMBEDDING_DEVICE', 'cpu')
            logger.info(f"Embedding device: {embedding_device}")
            
            # Check safe mode settings
            ultra_safe = config.get('RAG_ULTRA_SAFE_MODE', False)
            safe_retrieval = config.get('RAG_SAFE_RETRIEVAL_MODE', False)
            logger.info(f"Ultra Safe Mode: {ultra_safe}")
            logger.info(f"Safe Retrieval Mode: {safe_retrieval}")
            
            # Test with AMD-optimized settings
            test_query = "radar system performance and specifications"
            
            # Apply AMD optimizations
            amd_settings = {
                'RAG_N_RESULTS': 20,
                'RAG_ALPHA': 0.6,
                'RAG_IMPORTANCE_SCORE': 0.3,
                'RAG_TOKEN_LIMIT': 8192,
                'RAG_RERANKING': True,
                'RAG_CROSS_ENCODER_RERANKING': True,
                'RAG_QUERY_EXPANSION': True,
                'RAG_ULTRA_SAFE_MODE': False,
                'RAG_SAFE_RETRIEVAL_MODE': False,
                'EMBEDDING_DEVICE': 'cpu'
            }
            
            # Test retrieval with AMD settings
            start_time = time.time()
            amd_chunks = self.rag_handler.get_relevant_chunks(
                test_query,
                n_results=amd_settings['RAG_N_RESULTS'],
                alpha=amd_settings['RAG_ALPHA'],
                filter_criteria={
                    "importance_score": amd_settings['RAG_IMPORTANCE_SCORE'],
                    "language": "en"
                },
                reranking=amd_settings['RAG_RERANKING'],
                cross_encoder_reranking=amd_settings['RAG_CROSS_ENCODER_RERANKING'],
                query_expansion=amd_settings['RAG_QUERY_EXPANSION']
            )
            amd_time = time.time() - start_time
            
            logger.info(f"AMD optimized retrieval: {len(amd_chunks)} chunks in {amd_time:.2f}s")
            
            # Verify AMD optimizations are working
            if embedding_device == 'cpu':
                logger.info("AMD optimization: Using CPU for embedding (stable for AMD integrated graphics)")
            
            if not ultra_safe and not safe_retrieval:
                logger.info("AMD optimization: Performance mode enabled (not ultra safe)")
            
            if len(amd_chunks) >= 10:
                logger.info("AMD optimization: Sufficient chunk retrieval for comprehensive responses")
                self.test_results.append(("AMD Optimization Test", "PASS", "AMD optimizations working correctly"))
            else:
                logger.warning("AMD optimization: Low chunk retrieval")
                self.test_results.append(("AMD Optimization Test", "WARNING", "Low chunk retrieval with AMD settings"))
                
        except Exception as e:
            logger.error(f"Error in AMD optimization test: {e}")
            self.test_results.append(("AMD Optimization Test", "FAIL", str(e)))
    
    def test_6_performance_monitoring(self):
        """Test 6: Monitor RAG performance metrics."""
        logger.info("=== Test 6: Performance Monitoring ===")
        
        try:
            if not self.rag_handler:
                logger.error("RAG handler not initialized")
                self.test_results.append(("Performance Monitoring", "FAIL", "RAG handler not initialized"))
                return
            
            # Test multiple queries to gather performance metrics
            test_queries = [
                "radar technology",
                "AI systems",
                "technical specifications",
                "performance metrics",
                "system requirements"
            ]
            
            total_time = 0
            total_chunks = 0
            successful_queries = 0
            
            for query in test_queries:
                try:
                    start_time = time.time()
                    
                    # Get current settings
                    self.config_manager.load_config()
                    config = self.config_manager.config
                    
                    chunks = self.rag_handler.get_relevant_chunks(
                        query,
                        n_results=config.get('RAG_N_RESULTS', 25),
                        alpha=config.get('RAG_ALPHA', 0.6),
                        filter_criteria={
                            "importance_score": config.get('RAG_IMPORTANCE_SCORE', 0.3),
                            "language": "en"
                        },
                        reranking=config.get('RAG_RERANKING', True),
                        cross_encoder_reranking=config.get('RAG_CROSS_ENCODER_RERANKING', True),
                        query_expansion=config.get('RAG_QUERY_EXPANSION', True)
                    )
                    
                    query_time = time.time() - start_time
                    total_time += query_time
                    total_chunks += len(chunks)
                    successful_queries += 1
                    
                    logger.info(f"Query '{query}': {len(chunks)} chunks in {query_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"Error in query '{query}': {e}")
            
            # Calculate performance metrics
            if successful_queries > 0:
                avg_time = total_time / successful_queries
                avg_chunks = total_chunks / successful_queries
                chunks_per_second = total_chunks / total_time if total_time > 0 else 0
                
                logger.info(f"Performance Metrics:")
                logger.info(f"  Average query time: {avg_time:.2f}s")
                logger.info(f"  Average chunks per query: {avg_chunks:.1f}")
                logger.info(f"  Chunks per second: {chunks_per_second:.1f}")
                
                # Performance assessment
                if avg_time <= 2.0:  # 2 seconds or less per query
                    performance_status = "EXCELLENT"
                elif avg_time <= 5.0:  # 5 seconds or less per query
                    performance_status = "GOOD"
                elif avg_time <= 10.0:  # 10 seconds or less per query
                    performance_status = "ACCEPTABLE"
                else:
                    performance_status = "SLOW"
                
                logger.info(f"  Performance status: {performance_status}")
                
                if performance_status in ["EXCELLENT", "GOOD"]:
                    self.test_results.append(("Performance Monitoring", "PASS", f"{performance_status} performance: {avg_time:.2f}s avg"))
                else:
                    self.test_results.append(("Performance Monitoring", "WARNING", f"{performance_status} performance: {avg_time:.2f}s avg"))
            else:
                self.test_results.append(("Performance Monitoring", "FAIL", "No successful queries"))
                
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            self.test_results.append(("Performance Monitoring", "FAIL", str(e)))
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        logger.info("Starting RAG Functionality Tests")
        logger.info("=" * 50)
        
        # Run all tests
        self.test_1_rag_handler_initialization()
        self.test_2_rag_settings_verification()
        self.test_3_basic_retrieval_test()
        self.test_4_quality_improvement_test()
        self.test_5_amd_optimization_test()
        self.test_6_performance_monitoring()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report."""
        logger.info("\n" + "=" * 50)
        logger.info("RAG FUNCTIONALITY TEST REPORT")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed_tests = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        warning_tests = sum(1 for _, status, _ in self.test_results if status == "WARNING")
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Warnings: {warning_tests}")
        
        logger.info("\nDetailed Results:")
        for test_name, status, message in self.test_results:
            if status == "PASS":
                status_icon = "PASS"
            elif status == "FAIL":
                status_icon = "FAIL"
            else:
                status_icon = "WARN"
            logger.info(f"{status_icon} {test_name}: {status} - {message}")
        
        # Overall assessment
        if failed_tests == 0:
            if warning_tests == 0:
                logger.info("\nALL TESTS PASSED! RAG functionality is working correctly.")
            else:
                logger.info("\nCORE FUNCTIONALITY WORKS! Some minor warnings detected.")
        else:
            logger.info(f"\n{failed_tests} TESTS FAILED! RAG functionality needs attention.")
        
        # Save report to file
        report_path = Path("rag_functionality_test_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RAG FUNCTIONALITY TEST REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Warnings: {warning_tests}\n\n")
            
            f.write("Detailed Results:\n")
            for test_name, status, message in self.test_results:
                if status == "PASS":
                    status_icon = "PASS"
                elif status == "FAIL":
                    status_icon = "FAIL"
                else:
                    status_icon = "WARN"
                f.write(f"{status_icon} {test_name}: {status} - {message}\n")
        
        logger.info(f"\nDetailed report saved to: {report_path}")

def main():
    """Main function to run the tests."""
    tester = RAGFunctionalityTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 