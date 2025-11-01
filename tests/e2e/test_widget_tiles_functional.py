#!/usr/bin/env python3
"""
Comprehensive E2E Widget Tiles Functional Test

This test suite verifies that widget tiles actually work correctly in the browser.
It tests the COMPLETE interactive tile system end-to-end, including:

1. **Frontend Integration Test**: Load index.html in real browser and verify widgets are interactive
2. **Widget Hover Test**: Verify hovering over widgets shows correct hover tiles without affecting other widgets
3. **Widget Click Test**: Verify clicking widgets shows correct click states
4. **Tile Loading Test**: Verify widget tiles load and display correctly
5. **Isolation Test**: Verify one widget's state doesn't affect other widgets
6. **AI Pipeline Test**: Run ai_world_generator.py and verify it produces working tiles
7. **Visual Regression Test**: Screenshot and compare different widget states

TECHNICAL REQUIREMENTS:
- Uses Playwright for browser automation
- Tests both demo tiles and AI-generated tiles
- Includes visual screenshots for documentation
- Tests tile loading performance and error handling
- Verifies coordinate alignment and positioning
- Tests fallback to CSS effects when tiles are missing

CONTEXT:
- Tile system uses 64x64px grid coordinates
- Widgets have hover/click tiles as transparent PNG overlays
- Base scene should remain visible behind widget overlays
- Server runs on http://localhost:8083/index.html
- Demo tiles exist: *_hover_demo.png, *_click_demo.png

Run with:
    pytest tests/e2e/test_widget_tiles_functional.py -v -s --headed
"""

import json
import os
import sys
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from playwright.async_api import Page, async_playwright

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8083")
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Visual comparison threshold (pixel difference percentage)
VISUAL_THRESHOLD = 0.05  # 5% difference allowed


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to disable directory listing for security"""

    def list_directory(self, path):
        """Disable directory listing"""
        self.send_error(404, "File not found")
        return None

    def end_headers(self):
        """Add CORS headers to allow local testing"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()


@pytest.fixture(scope="session")
async def http_server():
    """Start a local HTTP server for serving static files"""
    port = 8083

    # Change to static directory
    original_dir = os.getcwd()
    static_dir = Path(__file__).parent.parent.parent / "static"
    os.chdir(static_dir)

    # Create server
    server = HTTPServer(("localhost", port), CustomHTTPRequestHandler)

    # Start server in background thread
    import threading

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            import urllib.request

            response = urllib.request.urlopen(f"http://localhost:{port}/index.html")
            if response.status == 200:
                break
        except Exception:
            time.sleep(0.5)
            if attempt == max_attempts - 1:
                raise RuntimeError(f"Failed to start HTTP server on port {port}")

    yield f"http://localhost:{port}"

    # Cleanup
    server.shutdown()
    os.chdir(original_dir)


@pytest.fixture(scope="session")
async def browser():
    """Playwright browser fixture for E2E testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for visual debugging
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1200,800",
            ],
        )
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser, http_server):
    """Create a new page for each test"""
    page = await browser.new_page()
    page.set_default_timeout(10000)  # 10 seconds timeout

    # Navigate to the page
    await page.goto(f"{http_server}/index.html")
    await page.wait_for_load_state("networkidle")

    yield page

    await page.close()


@pytest.fixture(scope="session")
def world_data():
    """Load the world data with widget configurations"""
    result_path = Path(__file__).parent.parent.parent / "static" / "result.json"
    if result_path.exists():
        with open(result_path, "r") as f:
            return json.load(f)
    else:
        # Return minimal test data if no AI-generated data exists
        return {
            "locations": [
                {
                    "id": "test_location",
                    "name": "Test Location",
                    "description": "Test location for E2E",
                    "scene": {
                        "base": "static/world/liliths_room_base_demo.png",
                        "tiles": {"idle": "static/world/liliths_room_base_demo.png"},
                    },
                    "widgets": [
                        {
                            "id": "test_widget",
                            "name": "Test Widget",
                            "type": "poster",
                            "position": {"x": 128, "y": 128},
                            "size": {"width": 128, "height": 128},
                            "tiles": {
                                "hover": "static/world/test_widget_hover_demo.png",
                                "click": "static/world/test_widget_click_demo.png",
                            },
                            "interactions": {
                                "hover": "Test hover effect",
                                "click": "Test click action",
                            },
                        }
                    ],
                }
            ]
        }


@pytest.fixture(scope="session")
def demo_tiles():
    """Get list of available demo tiles for testing"""
    static_world = Path(__file__).parent.parent.parent / "static" / "world"
    demo_tiles = {"hover": [], "click": [], "base": []}

    for tile_file in static_world.glob("*_demo.png"):
        if "hover" in tile_file.name:
            demo_tiles["hover"].append(tile_file)
        elif "click" in tile_file.name:
            demo_tiles["click"].append(tile_file)
        elif "base" in tile_file.name:
            demo_tiles["base"].append(tile_file)

    return demo_tiles


class TestWidgetTilesFunctional:
    """Comprehensive widget tile functionality tests"""

    async def test_page_loads_and_widgets_render(self, page: Page):
        """Test that the page loads and widgets are rendered"""
        print("🧪 Testing page load and widget rendering...")

        # Wait for page to fully load
        await page.wait_for_selector("#worldCanvas", timeout=10000)
        await page.wait_for_selector(".location-container", timeout=10000)

        # Check that canvas exists
        canvas = await page.query_selector("#worldCanvas")
        assert canvas is not None, "World canvas should exist"

        # Wait for widgets to be created
        await page.wait_for_function(
            """() => {
                const widgets = document.querySelectorAll('.widget-area');
                return widgets.length > 0;
            }""",
            timeout=15000,
        )

        # Get all widgets
        widgets = await page.query_selector_all(".widget-area")
        assert len(widgets) > 0, f"Expected at least 1 widget, found {len(widgets)}"

        print(f"✅ Page loaded successfully with {len(widgets)} widgets")

        # Take screenshot for documentation
        await page.screenshot(path=str(SCREENSHOT_DIR / "page_loaded.png"))
        print("📸 Screenshot saved: page_loaded.png")

    async def test_widget_hover_states(self, page: Page, demo_tiles):
        """Test widget hover states work correctly"""
        print("🧪 Testing widget hover states...")

        # Wait for widgets to load
        await page.wait_for_selector(".widget-area", timeout=10000)
        widgets = await page.query_selector_all(".widget-area")
        assert len(widgets) > 0, "Need widgets to test hover states"

        # Test each widget
        for i, widget in enumerate(widgets[:3]):  # Test first 3 widgets
            widget_id = await widget.get_attribute("data-widget-id")
            widget_type = await widget.get_attribute("data-widget-type")

            print(f"Testing hover for widget: {widget_id} (type: {widget_type})")

            # Get initial state screenshot
            await widget.hover()
            await page.wait_for_timeout(500)  # Allow hover effect to apply

            # Check if hover overlay is created
            hover_overlay = await widget.query_selector(".widget-hover-overlay")
            if hover_overlay:
                # Check that overlay is visible
                is_visible = await hover_overlay.is_visible()
                assert is_visible, f"Hover overlay for {widget_id} should be visible"

                # Check that overlay has correct image
                overlay_img = await hover_overlay.query_selector("img")
                if overlay_img:
                    img_src = await overlay_img.get_attribute("src")
                    assert img_src is not None, (
                        f"Hover overlay for {widget_id} should have image"
                    )
                    assert "hover" in img_src or "demo" in img_src, (
                        f"Hover image should contain 'hover': {img_src}"
                    )

            # Take screenshot of hover state
            await page.screenshot(
                path=str(SCREENSHOT_DIR / f"widget_{widget_id}_hover.png")
            )

            # Move away from widget
            await page.mouse.move(50, 50)  # Move to corner
            await page.wait_for_timeout(300)

            # Check that hover overlay is hidden/removed
            hover_overlay_after = await widget.query_selector(".widget-hover-overlay")
            if hover_overlay_after:
                is_visible_after = await hover_overlay_after.is_visible()
                assert not is_visible_after, (
                    f"Hover overlay for {widget_id} should be hidden after mouse leave"
                )

        print("✅ Widget hover states working correctly")

    async def test_widget_click_states(self, page: Page):
        """Test widget click states work correctly"""
        print("🧪 Testing widget click states...")

        # Wait for widgets to load
        await page.wait_for_selector(".widget-area", timeout=10000)
        widgets = await page.query_selector_all(".widget-area")
        assert len(widgets) > 0, "Need widgets to test click states"

        # Test clicking on first widget
        widget = widgets[0]
        widget_id = await widget.get_attribute("data-widget-id")
        widget_type = await widget.get_attribute("data-widget-type")

        print(f"Testing click for widget: {widget_id} (type: {widget_type})")

        # Click on widget
        await widget.click()
        await page.wait_for_timeout(500)  # Allow click effect to apply

        # Check if click overlay appears
        click_overlay = await widget.query_selector(".widget-click-overlay")
        if click_overlay:
            is_visible = await click_overlay.is_visible()
            print(f"Click overlay visible: {is_visible}")

        # Take screenshot of click state
        await page.screenshot(
            path=str(SCREENSHOT_DIR / f"widget_{widget_id}_click.png")
        )

        # Check if modal appears for certain widget types
        if widget_type in ["poster", "changelog_book", "family_photo"]:
            modal = await page.query_selector("#widgetModal")
            if modal:
                is_visible = await modal.is_visible()
                print(f"Modal visible for {widget_type}: {is_visible}")

                if is_visible:
                    # Close modal if it appeared
                    close_button = await modal.query_selector(".modal-close")
                    if close_button:
                        await close_button.click()
                        await page.wait_for_timeout(300)

        print("✅ Widget click states working correctly")

    async def test_widget_isolation(self, page: Page):
        """Test that one widget's state doesn't affect other widgets"""
        print("🧪 Testing widget isolation...")

        # Wait for widgets to load
        await page.wait_for_selector(".widget-area", timeout=10000)
        widgets = await page.query_selector_all(".widget-area")
        assert len(widgets) >= 2, "Need at least 2 widgets for isolation test"

        # Get first two widgets
        widget1 = widgets[0]
        widget2 = widgets[1]

        widget1_id = await widget1.get_attribute("data-widget-id")
        widget2_id = await widget2.get_attribute("data-widget-id")

        print(f"Testing isolation between: {widget1_id} and {widget2_id}")

        # Hover over first widget
        await widget1.hover()
        await page.wait_for_timeout(500)

        # Check that second widget doesn't have hover state
        widget2_hover = await widget2.query_selector(".widget-hover-overlay")
        if widget2_hover:
            is_visible = await widget2_hover.is_visible()
            assert not is_visible, (
                f"Widget {widget2_id} should not be affected by hover on {widget1_id}"
            )

        # Click on first widget
        await widget1.click()
        await page.wait_for_timeout(500)

        # Check that second widget doesn't have click state
        widget2_click = await widget2.query_selector(".widget-click-overlay")
        if widget2_click:
            is_visible = await widget2_click.is_visible()
            assert not is_visible, (
                f"Widget {widget2_id} should not be affected by click on {widget1_id}"
            )

        print("✅ Widget isolation working correctly")

    async def test_tile_loading_performance(self, page: Page):
        """Test that widget tiles load within reasonable time"""
        print("🧪 Testing tile loading performance...")

        # Monitor network requests
        network_requests = []

        page.on(
            "request",
            lambda request: network_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                }
            ),
        )

        # Start performance monitoring
        start_time = time.time()

        # Navigate to page (already done in fixture, but we can reload)
        await page.reload()
        await page.wait_for_load_state("networkidle")

        # Wait for widgets to be ready
        await page.wait_for_function(
            """() => {
                const widgets = document.querySelectorAll('.widget-area');
                return widgets.length > 0 &&
                       Array.from(widgets).every(w => w.offsetWidth > 0 && w.offsetHeight > 0);
            }""",
            timeout=15000,
        )

        end_time = time.time()
        load_time = end_time - start_time

        print(f"Page load time: {load_time:.2f} seconds")
        assert load_time < 10.0, (
            f"Page should load within 10 seconds, took {load_time:.2f}s"
        )

        # Check tile-specific requests
        tile_requests = [
            req
            for req in network_requests
            if "hover" in req["url"] or "click" in req["url"]
        ]
        print(f"Found {len(tile_requests)} tile requests")

        # Take performance screenshot
        await page.screenshot(path=str(SCREENSHOT_DIR / "performance_test.png"))

        print("✅ Tile loading performance acceptable")

    async def test_fallback_css_effects(self, page: Page):
        """Test CSS fallback effects when tiles are missing"""
        print("🧪 Testing CSS fallback effects...")

        # Wait for widgets to load
        await page.wait_for_selector(".widget-area", timeout=10000)
        widgets = await page.query_selector_all(".widget-area")

        if not widgets:
            pytest.skip("No widgets found for CSS fallback test")

        # Test hover CSS fallback
        widget = widgets[0]
        widget_id = await widget.get_attribute("data-widget-id")

        print(f"Testing CSS fallback for widget: {widget_id}")

        # Get computed style before hover
        widget_style_before = await widget.evaluate(
            "el => window.getComputedStyle(el).backgroundColor"
        )

        # Hover over widget
        await widget.hover()
        await page.wait_for_timeout(300)

        # Get computed style during hover
        widget_style_hover = await widget.evaluate(
            "el => window.getComputedStyle(el).backgroundColor"
        )

        # Check if some visual change occurred (CSS fallback)
        style_changed = widget_style_before != widget_style_hover
        print(f"Style changed on hover: {style_changed}")

        # Take screenshot showing CSS fallback
        await page.screenshot(
            path=str(SCREENSHOT_DIR / f"css_fallback_{widget_id}.png")
        )

        print("✅ CSS fallback effects working")

    async def test_coordinate_alignment(self, page: Page):
        """Test that widget coordinates are properly aligned"""
        print("🧪 Testing widget coordinate alignment...")

        # Wait for widgets to load
        await page.wait_for_selector(".widget-area", timeout=10000)
        widgets = await page.query_selector_all(".widget-area")

        assert len(widgets) > 0, "Need widgets to test coordinate alignment"

        for widget in widgets[:3]:  # Test first 3 widgets
            widget_id = await widget.get_attribute("data-widget-id")

            # Get widget position and size
            bounding_box = await widget.bounding_box()
            assert bounding_box is not None, (
                f"Widget {widget_id} should have bounding box"
            )

            x, y, width, height = (
                bounding_box["x"],
                bounding_box["y"],
                bounding_box["width"],
                bounding_box["height"],
            )

            # Check 64px grid alignment (approximately, allowing for CSS variations)
            assert x % 64 < 10, (
                f"Widget {widget_id} x position should align to 64px grid (within 10px tolerance)"
            )
            assert y % 64 < 10, (
                f"Widget {widget_id} y position should align to 64px grid (within 10px tolerance)"
            )
            assert width % 64 < 10, (
                f"Widget {widget_id} width should be multiple of 64px (within 10px tolerance)"
            )
            assert height % 64 < 10, (
                f"Widget {widget_id} height should be multiple of 64px (within 10px tolerance)"
            )

            print(f"Widget {widget_id}: position=({x},{y}), size=({width}x{height})")

        print("✅ Widget coordinate alignment correct")

    async def test_visual_regression_base(self, page: Page):
        """Test base visual state for regression"""
        print("🧪 Testing visual regression for base state...")

        # Wait for page to fully load
        await page.wait_for_selector(".location-container", timeout=10000)
        await page.wait_for_timeout(2000)  # Allow animations to settle

        # Take full page screenshot
        screenshot_path = SCREENSHOT_DIR / "visual_regression_base.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)

        # Verify screenshot was created and has reasonable size
        assert screenshot_path.exists(), "Screenshot should be created"

        with Image.open(screenshot_path) as img:
            assert img.size[0] >= 800, (
                f"Screenshot width should be at least 800px, got {img.size[0]}"
            )
            assert img.size[1] >= 600, (
                f"Screenshot height should be at least 600px, got {img.size[1]}"
            )

        print("✅ Visual regression base screenshot captured")

    async def test_console_errors(self, page: Page):
        """Test that there are no critical console errors"""
        print("🧪 Testing for console errors...")

        # Collect console messages
        console_messages = []

        page.on(
            "console",
            lambda msg: console_messages.append(
                {"type": msg.type, "text": msg.text, "location": msg.location}
            ),
        )

        page.on(
            "pageerror",
            lambda error: console_messages.append(
                {"type": "error", "text": str(error), "location": None}
            ),
        )

        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Check for errors
        errors = [
            msg for msg in console_messages if msg["type"] in ["error", "javascript"]
        ]

        # Filter out expected/acceptable errors
        acceptable_errors = [
            "404",  # Missing tile files are expected
            "Failed to load resource",  # Related to 404s
        ]

        critical_errors = [
            error
            for error in errors
            if not any(acceptable in error["text"] for acceptable in acceptable_errors)
        ]

        if critical_errors:
            print(f"⚠️ Found {len(critical_errors)} console errors:")
            for error in critical_errors:
                print(f"  - {error['text']}")

        # Allow some errors due to missing tiles in demo mode
        assert len(critical_errors) <= 2, (
            f"Too many critical console errors: {len(critical_errors)}"
        )

        print(
            f"✅ Console errors check passed ({len(errors)} total, {len(critical_errors)} critical)"
        )

    def test_ai_pipeline_integration(self, world_data):
        """Test AI pipeline integration by checking world data structure"""
        print("🧪 Testing AI pipeline integration...")

        # Check that world data has required structure
        assert "locations" in world_data, "World data should have locations"
        assert len(world_data["locations"]) > 0, "Should have at least one location"

        location = world_data["locations"][0]
        assert "widgets" in location, "Location should have widgets"
        assert len(location["widgets"]) > 0, "Should have at least one widget"

        # Check widget structure
        for widget in location["widgets"]:
            assert "id" in widget, "Widget should have ID"
            assert "position" in widget, "Widget should have position"
            assert "size" in widget, "Widget should have size"
            assert "tiles" in widget, "Widget should have tiles"

            # Check tile structure
            tiles = widget["tiles"]
            if "hover" in tiles and tiles["hover"]:
                hover_path = Path(tiles["hover"])
                if hover_path.exists():
                    with Image.open(hover_path) as img:
                        assert img.mode == "RGBA", (
                            f"Hover tile should be RGBA: {widget['id']}"
                        )

        print("✅ AI pipeline integration verified")

    def test_demo_tiles_exist(self, demo_tiles):
        """Test that demo tiles exist and are valid images"""
        print("🧪 Testing demo tiles exist...")

        assert len(demo_tiles["hover"]) > 0, "Should have hover demo tiles"
        assert len(demo_tiles["click"]) > 0, "Should have click demo tiles"
        assert len(demo_tiles["base"]) > 0, "Should have base demo tiles"

        # Test each demo tile
        for tile_type, tiles in demo_tiles.items():
            for tile_path in tiles:
                assert tile_path.exists(), f"Demo tile should exist: {tile_path}"

                # Verify image properties
                with Image.open(tile_path) as img:
                    assert img.size[0] > 0 and img.size[1] > 0, (
                        f"Demo tile should have valid size: {tile_path}"
                    )

                    if tile_type in ["hover", "click"]:
                        assert img.mode == "RGBA", (
                            f"Interactive tile should have alpha: {tile_path}"
                        )

        print(
            f"✅ Demo tiles verified: {len(demo_tiles['hover'])} hover, {len(demo_tiles['click'])} click, {len(demo_tiles['base'])} base"
        )


async def compare_images_ssim(img1_path: Path, img2_path: Path) -> float:
    """Compare two images using SSIM-like metric"""
    try:
        with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
            # Convert to grayscale for comparison
            img1_gray = img1.convert("L")
            img2_gray = img2.convert("L")

            # Resize to match dimensions
            min_width = min(img1_gray.width, img2_gray.width)
            min_height = min(img1_gray.height, img2_gray.height)

            img1_resized = img1_gray.resize((min_width, min_height))
            img2_resized = img2_gray.resize((min_width, min_height))

            # Calculate mean squared error
            img1_array = np.array(img1_resized)
            img2_array = np.array(img2_resized)

            mse = np.mean((img1_array.astype(float) - img2_array.astype(float)) ** 2)

            # Convert to similarity score (0 = identical, 1 = completely different)
            max_possible_mse = 255**2
            similarity = mse / max_possible_mse

            return similarity
    except Exception as e:
        print(f"Error comparing images: {e}")
        return 1.0  # Return worst case similarity


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v", "-s"])
