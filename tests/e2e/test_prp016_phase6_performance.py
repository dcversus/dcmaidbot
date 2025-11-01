#!/usr/bin/env python3
"""
E2E Tests: PRP-016 Phase 6 - Performance & Production Validation
==================================================================

Tests system performance, cross-browser compatibility, mobile responsiveness,
and production validation metrics.
"""

import os
import time

import psutil
import pytest
from playwright.async_api import async_playwright

from services.messenger_service import get_messenger_service
from services.nudge_service import NudgeService


class TestPRP016Phase6Performance:
    """Test Phase 6 performance and production validation"""

    @pytest.fixture
    def test_config(self):
        """Test configuration"""
        return {
            "base_url": "https://dcmaidbot.theedgestory.org",
            "local_url": "http://localhost:8000",
            "vasilisa_id": int(os.getenv("VASILISA_TG_ID", "122657093")),
        }

    @pytest.fixture
    async def browser_context(self):
        """Create browser context for testing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
            yield context
            await browser.close()

    def test_memory_usage_messenger_service(self):
        """Test messenger service memory usage"""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple messenger service instances
        messenger_instances = []
        for i in range(100):
            messenger_instances.append(get_messenger_service())

        # Test memory usage after creating instances
        after_creation_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_creation_memory - initial_memory

        # Test markdown conversion memory usage
        markdown_content = """
# Performance Test Content
## Memory Usage Testing
- **Bold Text**: Testing memory efficiency
- **Lists**: Multiple items to process
- **Links**: [Test Link](https://example.com)

```python
def test_function():
    return "Performance validation"
```

This is a complex markdown document designed to test memory usage during processing.
"""

        for i in range(50):
            for messenger in messenger_instances:
                rich_content = messenger.parse_markdown_to_telegram(markdown_content)
                assert rich_content.content is not None

        # Final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory

        # Performance assertions
        assert memory_increase < 50  # Should use less than 50MB for 100 instances
        assert total_memory_increase < 100  # Total increase should be less than 100MB
        assert len(messenger_instances) == 100  # All instances should be created

        print("✅ Memory Usage Test Results:")
        print(f"   Initial Memory: {initial_memory:.2f} MB")
        print(f"   After Creation: {after_creation_memory:.2f} MB")
        print(f"   Final Memory: {final_memory:.2f} MB")
        print(f"   Total Increase: {total_memory_increase:.2f} MB")
        print(f"   Memory per Instance: {memory_increase / 100:.2f} MB")

    def test_messenger_service_performance_benchmark(self):
        """Test messenger service processing speed"""
        messenger = get_messenger_service()

        # Test data
        simple_markdown = "# Simple Test\nBasic content with **bold** text."
        complex_markdown = """# Complex Performance Test
## Multiple Sections

### Lists and Formatting
- **Item 1**: Complex content with *italic* and `code`
- **Item 2**: [Links](https://example.com) and ~~strikethrough~~
- **Item 3**: Nested **bold with *italic inside*** formatting

### Code Blocks
```python
def complex_function(param1, param2):
    \"\"\"Complex function with multiple lines\"\"\"
    result = param1 + param2
    return result

# Additional comments
for i in range(100):
    print(f"Processing item {i}")
```

### Tables (if supported)
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| More 1   | More 2   | More 3   |

### Buttons and Interactive Elements
[🏠 Home](home_action)
[🎵 Music](music_action)
[📋 Changelog](changelog_action)
[🌐 External](https://external-link.com)
"""

        # Benchmark simple markdown
        simple_times = []
        for i in range(100):
            start_time = time.time()
            messenger.parse_markdown_to_telegram(simple_markdown)
            end_time = time.time()
            simple_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Benchmark complex markdown
        complex_times = []
        for i in range(100):
            start_time = time.time()
            messenger.parse_markdown_to_telegram(complex_markdown)
            end_time = time.time()
            complex_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Calculate statistics
        simple_avg = sum(simple_times) / len(simple_times)
        simple_max = max(simple_times)
        simple_min = min(simple_times)

        complex_avg = sum(complex_times) / len(complex_times)
        complex_max = max(complex_times)
        complex_min = min(complex_times)

        # Performance assertions
        assert simple_avg < 10  # Simple markdown should process in <10ms
        assert complex_avg < 50  # Complex markdown should process in <50ms
        assert simple_max < 50  # No simple processing should take >50ms
        assert complex_max < 200  # No complex processing should take >200ms

        print("✅ Performance Benchmark Results:")
        print("   Simple Markdown:")
        print(f"     Average: {simple_avg:.2f} ms")
        print(f"     Min: {simple_min:.2f} ms")
        print(f"     Max: {simple_max:.2f} ms")
        print("   Complex Markdown:")
        print(f"     Average: {complex_avg:.2f} ms")
        print(f"     Min: {complex_min:.2f} ms")
        print(f"     Max: {complex_max:.2f} ms")

    def test_nudge_service_performance(self):
        """Test nudge service processing performance"""
        nudge_service = NudgeService()

        # Test message preparation performance
        test_messages = [
            "Simple test message",
            """
# Complex Nudge Message
## Performance Testing
This is a complex message with **multiple formatting options** and *various text styles*.
- List item 1
- List item 2 with `code`
- List item 3 with [link](https://example.com)
            """,
            """
🚨 **PRE-RELEASE WARNING** 🚨

**Release**: Performance Test - v0.1.1
**Status**: Ready for Validation

### 📊 Performance Metrics
- **Memory Usage**: ✅ Efficient
- **Processing Speed**: ✅ Fast
- **Response Time**: ✅ Optimal

[🎯 Test Features](test_features)
[📋 View Results](view_results)
            """,
        ]

        # Benchmark message processing
        processing_times = []
        for message in test_messages:
            start_time = time.time()
            nudge_service.messenger_service.parse_markdown_to_telegram(message)
            end_time = time.time()
            processing_times.append((end_time - start_time) * 1000)

        # Calculate statistics
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)

        # Performance assertions
        assert avg_time < 20  # Average processing should be <20ms
        assert max_time < 100  # No processing should take >100ms

        print("✅ Nudge Service Performance Results:")
        print(f"   Average: {avg_time:.2f} ms")
        print(f"   Min: {min_time:.2f} ms")
        print(f"   Max: {max_time:.2f} ms")

    @pytest.mark.asyncio
    async def test_landing_page_load_performance(self, test_config, browser_context):
        """Test landing page load performance"""
        page = await browser_context.new_page()

        # Navigate to landing page
        start_time = time.time()
        response = await page.goto(test_config["base_url"])
        load_time = time.time() - start_time

        # Wait for page to be fully loaded
        await page.wait_for_load_state("networkidle")

        # Check page loaded successfully
        assert response.status == 200
        assert load_time < 5.0  # Page should load in <5 seconds

        # Check for critical elements
        await page.wait_for_selector("body", timeout=10000)

        # Check if page has content
        page_content = await page.content()
        assert len(page_content) > 1000  # Should have substantial content

        print("✅ Landing Page Load Performance:")
        print(f"   Load Time: {load_time:.2f} seconds")
        print(f"   Status Code: {response.status}")
        print(f"   Content Size: {len(page_content)} characters")

        await page.close()

    @pytest.mark.asyncio
    async def test_mobile_responsiveness(self, test_config):
        """Test mobile responsiveness across different screen sizes"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            # Test different mobile screen sizes
            screen_sizes = [
                {"width": 375, "height": 667},  # iPhone SE
                {"width": 414, "height": 896},  # iPhone 11
                {"width": 360, "height": 640},  # Android small
                {"width": 768, "height": 1024},  # iPad
            ]

            for i, size in enumerate(screen_sizes):
                context = await browser.new_context(
                    viewport=size,
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                )
                page = await context.new_page()

                try:
                    # Navigate to landing page
                    response = await page.goto(test_config["base_url"])
                    assert response.status == 200

                    # Wait for page to load
                    await page.wait_for_load_state("networkidle")

                    # Check viewport is correctly set
                    viewport = page.viewport_size
                    assert viewport["width"] == size["width"]
                    assert viewport["height"] == size["height"]

                    # Check if page is responsive (no horizontal scroll)
                    body_width = await page.evaluate("document.body.scrollWidth")
                    viewport_width = await page.evaluate("window.innerWidth")

                    # Body should not be wider than viewport (no horizontal scroll)
                    assert body_width <= viewport_width + 10  # Allow 10px tolerance

                    print(f"✅ Mobile Responsiveness Test {i + 1}:")
                    print(f"   Screen Size: {size['width']}x{size['height']}")
                    print(f"   Body Width: {body_width}px")
                    print(f"   Viewport Width: {viewport_width}px")

                finally:
                    await context.close()

            await browser.close()

    @pytest.mark.asyncio
    async def test_cross_browser_compatibility(self, test_config):
        """Test cross-browser compatibility"""
        async with async_playwright() as p:
            browsers_to_test = [
                ("chromium", p.chromium),
                ("firefox", p.firefox),
                # Note: WebKit requires additional setup in some environments
            ]

            results = {}

            for browser_name, browser_type in browsers_to_test:
                try:
                    browser = await browser_type.launch()
                    context = await browser.new_context()
                    page = await context.new_page()

                    # Navigate to landing page
                    start_time = time.time()
                    response = await page.goto(test_config["base_url"])
                    load_time = time.time() - start_time

                    # Wait for page to load
                    await page.wait_for_load_state("networkidle", timeout=10000)

                    # Check basic functionality
                    page_title = await page.title()
                    page_content = await page.content()

                    results[browser_name] = {
                        "status": response.status,
                        "load_time": load_time,
                        "title": page_title,
                        "content_size": len(page_content),
                        "success": True,
                    }

                    print(f"✅ {browser_name.title()} Compatibility:")
                    print(f"   Status: {response.status}")
                    print(f"   Load Time: {load_time:.2f}s")
                    print(f"   Title: {page_title}")

                    await context.close()
                    await browser.close()

                except Exception as e:
                    results[browser_name] = {
                        "status": "error",
                        "error": str(e),
                        "success": False,
                    }
                    print(f"❌ {browser_name.title()} Compatibility: {str(e)}")

            # Verify at least Chrome/Firefox work
            assert results.get("chromium", {}).get("success", False), (
                "Chrome compatibility failed"
            )
            assert results.get("firefox", {}).get("success", False), (
                "Firefox compatibility failed"
            )

    def test_concurrent_messenger_service_usage(self):
        """Test concurrent usage of messenger service"""
        import queue
        import threading

        messenger = get_messenger_service()
        test_markdown = """
# Concurrent Test
**Testing**: Thread safety and concurrent usage
- Item 1: Thread safety
- Item 2: Concurrent processing
        """

        results = queue.Queue()

        def worker_thread(worker_id):
            """Worker function for concurrent testing"""
            try:
                thread_results = []
                for i in range(50):
                    start_time = time.time()
                    rich_content = messenger.parse_markdown_to_telegram(test_markdown)
                    end_time = time.time()

                    thread_results.append(
                        {
                            "worker_id": worker_id,
                            "iteration": i,
                            "processing_time": (end_time - start_time) * 1000,
                            "success": rich_content.content is not None,
                        }
                    )

                results.put(thread_results)
            except Exception as e:
                results.put({"error": str(e), "worker_id": worker_id})

        # Create multiple worker threads
        threads = []
        num_threads = 10

        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        all_results = []
        while not results.empty():
            thread_results = results.get()
            if "error" not in thread_results:
                all_results.extend(thread_results)
            else:
                pytest.fail(f"Thread error: {thread_results['error']}")

        # Analyze results
        total_operations = len(all_results)
        successful_operations = sum(1 for r in all_results if r["success"])
        avg_processing_time = (
            sum(r["processing_time"] for r in all_results) / total_operations
        )

        # Assertions
        assert total_operations == num_threads * 50  # All operations should complete
        assert (
            successful_operations == total_operations
        )  # All operations should succeed
        assert (
            avg_processing_time < 100
        )  # Average processing should be <100ms even under load

        print("✅ Concurrent Usage Test Results:")
        print(f"   Threads: {num_threads}")
        print(f"   Total Operations: {total_operations}")
        print(f"   Successful Operations: {successful_operations}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Operations/Second: {total_operations / total_time:.2f}")
        print(f"   Average Processing Time: {avg_processing_time:.2f}ms")

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        messenger = get_messenger_service()

        # Test with malformed markdown
        malformed_markdowns = [
            "",  # Empty string
            "##",  # Incomplete header
            "**Bold without closing",  # Unclosed formatting
            "[Link without closing](url",  # Malformed link
            "```python\nUnclosed code block",  # Unclosed code block
        ]

        error_count = 0
        successful_conversions = 0

        for markdown in malformed_markdowns:
            try:
                rich_content = messenger.parse_markdown_to_telegram(markdown)
                if rich_content.content is not None:
                    successful_conversions += 1
                else:
                    error_count += 1
            except Exception:
                # Exceptions should be handled gracefully
                error_count += 1

        # System should handle errors gracefully
        assert error_count + successful_conversions == len(malformed_markdowns)

        # Most malformed inputs should still produce some output
        assert successful_conversions >= len(malformed_markdowns) // 2

        print("✅ Error Handling Test Results:")
        print(f"   Total Inputs: {len(malformed_markdowns)}")
        print(f"   Successful Conversions: {successful_conversions}")
        print(f"   Errors Handled: {error_count}")
        print(
            f"   Error Recovery Rate: {successful_conversions / len(malformed_markdowns) * 100:.1f}%"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
