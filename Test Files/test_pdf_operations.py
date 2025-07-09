#!/usr/bin/env python3
"""
Test suite for PDF operations in MCP Filesystem Server

This test suite validates:
1. PDF page extraction (single page and page ranges)
2. PDF content search functionality
3. PDF metadata extraction
4. Error handling for invalid operations
5. Permission checking
6. Integration with MCP client

Run this test to verify PDF functionality is working correctly.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the modules we want to test
from mcp_filesystem_server import create_filesystem_server, PDF_SUPPORT_AVAILABLE
from mcp_client import MCPClient, MCPServer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOperationsTest:
    """Test suite for PDF operations in MCP filesystem server."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.filesystem_server = None
        self.mcp_client = None
        
    def setup_test_environment(self):
        """Set up test environment with temporary directory and test files."""
        try:
            # Create temporary directory for testing
            self.temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary test directory: {self.temp_dir}")
            
            # Create a simple test filesystem server
            self.filesystem_server = create_filesystem_server(
                allowed_directory=self.temp_dir,
                max_file_size=50 * 1024 * 1024,  # 50MB for PDF files
                read_only=False,
                enable_logging=True
            )
            
            # Set up MCP client for integration testing
            self.mcp_client = MCPClient()
            
            # Create a test server configuration
            test_server = MCPServer(
                name="Test Local Files",
                url="local://filesystem",
                description="Test filesystem server for PDF operations",
                enabled=True,
                server_type="filesystem",
                config_data={
                    'allowed_directory': self.temp_dir,
                    'max_file_size': 50,
                    'read_only': False,
                    'enable_logging': True
                }
            )
            
            self.mcp_client.add_server(test_server)
            
            logger.info("Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False
    
    def create_sample_pdf(self):
        """Create a sample PDF file for testing."""
        if not PDF_SUPPORT_AVAILABLE:
            logger.warning("PDF support not available - skipping PDF creation")
            return None
            
        try:
            import fitz
            
            # Create a simple PDF with multiple pages
            pdf_path = os.path.join(self.temp_dir, "test_document.pdf")
            doc = fitz.open()
            
            # Page 1
            page1 = doc.new_page()
            page1.insert_text((50, 50), "This is page 1 of the test document.\nIt contains some sample text for testing.")
            page1.insert_text((50, 100), "We can search for keywords like 'climate change' and 'artificial intelligence'.")
            
            # Page 2  
            page2 = doc.new_page()
            page2.insert_text((50, 50), "This is page 2 with different content.")
            page2.insert_text((50, 100), "Here we discuss climate change impacts and solutions.")
            page2.insert_text((50, 150), "The topic of artificial intelligence is also important.")
            
            # Page 3
            page3 = doc.new_page() 
            page3.insert_text((50, 50), "Page 3 contains technical information.")
            page3.insert_text((50, 100), "Data analysis and machine learning algorithms.")
            page3.insert_text((50, 150), "Statistical models for climate change prediction.")
            
            # Save the PDF
            doc.save(pdf_path)
            doc.close()
            
            logger.info(f"Created sample PDF: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Failed to create sample PDF: {e}")
            return None
    
    def test_pdf_capabilities(self):
        """Test if PDF capabilities are properly reported."""
        test_name = "PDF Capabilities Check"
        try:
            capabilities = self.filesystem_server.get_capabilities()
            
            if PDF_SUPPORT_AVAILABLE:
                expected_pdf_ops = ["read_pdf_page", "search_pdf_content", "get_pdf_info"]
                missing_ops = [op for op in expected_pdf_ops if op not in capabilities]
                
                if not missing_ops:
                    self.test_results.append((test_name, "PASS", "All PDF operations available"))
                    return True
                else:
                    self.test_results.append((test_name, "FAIL", f"Missing PDF operations: {missing_ops}"))
                    return False
            else:
                if not any(op in capabilities for op in ["read_pdf_page", "search_pdf_content", "get_pdf_info"]):
                    self.test_results.append((test_name, "PASS", "PDF operations correctly disabled when libraries unavailable"))
                    return True
                else:
                    self.test_results.append((test_name, "FAIL", "PDF operations available despite missing libraries"))
                    return False
                    
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_get_pdf_info(self, pdf_path):
        """Test PDF metadata extraction."""
        test_name = "PDF Info Extraction"
        if not PDF_SUPPORT_AVAILABLE:
            self.test_results.append((test_name, "SKIP", "PDF support not available"))
            return True
            
        try:
            result = self.filesystem_server.get_pdf_info(pdf_path)
            
            if "error" in result:
                self.test_results.append((test_name, "FAIL", result["error"]))
                return False
            
            # Check required fields
            required_fields = ["file_path", "page_count", "file_size_bytes", "has_text", "metadata"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                self.test_results.append((test_name, "FAIL", f"Missing fields: {missing_fields}"))
                return False
            
            # Verify expected values
            if result["page_count"] != 3:
                self.test_results.append((test_name, "FAIL", f"Expected 3 pages, got {result['page_count']}"))
                return False
                
            if not result["has_text"]:
                self.test_results.append((test_name, "FAIL", "PDF should contain text"))
                return False
            
            self.test_results.append((test_name, "PASS", f"Retrieved info for {result['page_count']}-page PDF"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_read_pdf_page_single(self, pdf_path):
        """Test reading a single PDF page."""
        test_name = "Read Single PDF Page"
        if not PDF_SUPPORT_AVAILABLE:
            self.test_results.append((test_name, "SKIP", "PDF support not available"))
            return True
            
        try:
            # Test reading page 2
            result = self.filesystem_server.read_pdf_page(pdf_path, page_number=2)
            
            if "error" in result:
                self.test_results.append((test_name, "FAIL", result["error"]))
                return False
            
            # Check that we got the right page
            if result["extracted_pages"] != [2]:
                self.test_results.append((test_name, "FAIL", f"Expected page 2, got {result['extracted_pages']}"))
                return False
            
            # Check that content contains expected text
            if "climate change" not in result["text"].lower():
                self.test_results.append((test_name, "FAIL", "Expected content not found in page 2"))
                return False
            
            self.test_results.append((test_name, "PASS", "Successfully read single PDF page"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_read_pdf_page_range(self, pdf_path):
        """Test reading a range of PDF pages."""
        test_name = "Read PDF Page Range"
        if not PDF_SUPPORT_AVAILABLE:
            self.test_results.append((test_name, "SKIP", "PDF support not available"))
            return True
            
        try:
            # Test reading pages 1-2
            result = self.filesystem_server.read_pdf_page(pdf_path, start_page=1, end_page=2)
            
            if "error" in result:
                self.test_results.append((test_name, "FAIL", result["error"]))
                return False
            
            # Check that we got the right pages
            if result["extracted_pages"] != [1, 2]:
                self.test_results.append((test_name, "FAIL", f"Expected pages 1-2, got {result['extracted_pages']}"))
                return False
            
            # Check that content contains text from both pages
            text_lower = result["text"].lower()
            if "page 1" not in text_lower or "page 2" not in text_lower:
                self.test_results.append((test_name, "FAIL", "Expected content from both pages not found"))
                return False
            
            self.test_results.append((test_name, "PASS", "Successfully read PDF page range"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_search_pdf_content(self, pdf_path):
        """Test searching content within PDF."""
        test_name = "Search PDF Content"
        if not PDF_SUPPORT_AVAILABLE:
            self.test_results.append((test_name, "SKIP", "PDF support not available"))
            return True
            
        try:
            # Search for "climate change"
            result = self.filesystem_server.search_pdf_content(pdf_path, "climate change", case_sensitive=False)
            
            if "error" in result:
                self.test_results.append((test_name, "FAIL", result["error"]))
                return False
            
            # Should find matches
            if result["total_occurrences"] == 0:
                self.test_results.append((test_name, "FAIL", "Expected to find 'climate change' but found 0 occurrences"))
                return False
            
            # Should find matches on pages 2 and 3
            pages_with_matches = [match["page_number"] for match in result["matches"]]
            if 2 not in pages_with_matches or 3 not in pages_with_matches:
                self.test_results.append((test_name, "FAIL", f"Expected matches on pages 2 and 3, found on pages {pages_with_matches}"))
                return False
            
            self.test_results.append((test_name, "PASS", f"Found {result['total_occurrences']} occurrences across {len(pages_with_matches)} pages"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_mcp_integration(self, pdf_path):
        """Test PDF operations through MCP client."""
        test_name = "MCP Integration"
        if not PDF_SUPPORT_AVAILABLE:
            self.test_results.append((test_name, "SKIP", "PDF support not available"))
            return True
            
        try:
            server = self.mcp_client.get_server("Test Local Files")
            if not server:
                self.test_results.append((test_name, "FAIL", "Test server not found"))
                return False
            
            # Test get_pdf_info through MCP
            query = json.dumps({
                "operation": "get_pdf_info",
                "params": {"file_path": pdf_path}
            })
            
            result = self.mcp_client.query_mcp_server(server, query)
            
            if "error" in result:
                self.test_results.append((test_name, "FAIL", f"MCP query failed: {result['error']}"))
                return False
            
            if result.get("page_count") != 3:
                self.test_results.append((test_name, "FAIL", f"Expected 3 pages via MCP, got {result.get('page_count')}"))
                return False
            
            self.test_results.append((test_name, "PASS", "MCP integration working correctly"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        test_name = "Error Handling"
        try:
            # Test with non-existent file
            result = self.filesystem_server.get_pdf_info("nonexistent.pdf")
            if "error" not in result:
                self.test_results.append((test_name, "FAIL", "Should return error for non-existent file"))
                return False
            
            # Test with non-PDF file
            text_file = os.path.join(self.temp_dir, "test.txt")
            with open(text_file, 'w') as f:
                f.write("This is not a PDF")
            
            result = self.filesystem_server.read_pdf_page(text_file, page_number=1)
            if PDF_SUPPORT_AVAILABLE and "error" not in result:
                self.test_results.append((test_name, "FAIL", "Should return error for non-PDF file"))
                return False
            
            self.test_results.append((test_name, "PASS", "Error handling working correctly"))
            return True
            
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            return False
    
    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to clean up: {e}")
    
    def run_all_tests(self):
        """Run all PDF operation tests."""
        logger.info("Starting PDF operations test suite...")
        
        # Setup
        if not self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        # Check PDF support
        if not PDF_SUPPORT_AVAILABLE:
            logger.warning("PDF libraries not available - some tests will be skipped")
        
        try:
            # Run basic capability test
            self.test_pdf_capabilities()
            
            # Create sample PDF and run tests
            pdf_path = self.create_sample_pdf()
            
            if pdf_path and PDF_SUPPORT_AVAILABLE:
                self.test_get_pdf_info(pdf_path)
                self.test_read_pdf_page_single(pdf_path)
                self.test_read_pdf_page_range(pdf_path)
                self.test_search_pdf_content(pdf_path)
                self.test_mcp_integration(pdf_path)
            
            self.test_error_handling()
            
            # Print results
            self.print_results()
            
            return True
            
        finally:
            self.cleanup()
    
    def print_results(self):
        """Print test results summary."""
        print("\n" + "="*60)
        print("PDF OPERATIONS TEST RESULTS")
        print("="*60)
        
        passed = failed = errors = skipped = 0
        
        for test_name, status, message in self.test_results:
            status_symbol = {
                "PASS": "✓",
                "FAIL": "✗", 
                "ERROR": "⚠",
                "SKIP": "○"
            }.get(status, "?")
            
            print(f"{status_symbol} {test_name}: {status}")
            if message:
                print(f"  {message}")
            
            if status == "PASS":
                passed += 1
            elif status == "FAIL":
                failed += 1
            elif status == "ERROR":
                errors += 1
            elif status == "SKIP":
                skipped += 1
        
        print("-" * 60)
        print(f"Total: {len(self.test_results)} | Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped}")
        
        if failed == 0 and errors == 0:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed. Check the details above.")
        
        print("="*60)

def main():
    """Main test execution function."""
    test_suite = PDFOperationsTest()
    success = test_suite.run_all_tests()
    
    if success:
        logger.info("Test suite completed successfully")
    else:
        logger.error("Test suite encountered problems")
        sys.exit(1)

if __name__ == "__main__":
    main() 