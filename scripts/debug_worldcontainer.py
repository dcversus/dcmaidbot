#!/usr/bin/env python3
"""
Debug WorldContainer Visibility Issue
===================================

Debug script to identify why worldContainer remains hidden
and the WorldManager initialization process.
"""

import asyncio

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


async def debug_worldcontainer_visibility():
    """Debug worldContainer visibility with detailed analysis."""
    print("🔍 DEBUGGING: WorldContainer Visibility Issue")
    print("=" * 60)

    # Setup Chrome with debugging enabled
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Keep headless for now
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("📡 Opening page...")
        driver.get("http://localhost:8000/")

        # Wait for page to load
        await asyncio.sleep(3)

        print("\n🔍 CHECKING INITIAL STATE:")

        # Check loading element
        try:
            loading_element = driver.find_element(By.ID, "loading")
            loading_visible = loading_element.is_displayed()
            loading_text = loading_element.text
            print(f"📋 Loading element visible: {loading_visible}")
            print(f"   Loading text: '{loading_text}'")
        except NoSuchElementException:
            print("❌ Loading element not found")

        # Check worldContainer element
        try:
            worldcontainer_element = driver.find_element(By.ID, "worldContainer")
            worldcontainer_exists = True
            worldcontainer_visible = worldcontainer_element.is_displayed()
            worldcontainer_display = driver.execute_script(
                "return window.getComputedStyle(document.getElementById('worldContainer')).display;"
            )
            print(f"📋 WorldContainer element exists: {worldcontainer_exists}")
            print(f"   WorldContainer visible: {worldcontainer_visible}")
            print(f"   WorldContainer display style: '{worldcontainer_display}'")
        except NoSuchElementException:
            print("❌ WorldContainer element not found")
            worldcontainer_exists = False

        print("\n🔍 CHECKING CONSOLE LOGS:")

        # Get console logs
        logs = driver.get_log("browser")
        print(f"Found {len(logs)} console log entries:")

        error_logs = []
        warning_logs = []
        info_logs = []

        for log in logs:
            level = log["level"]
            message = log["message"]

            if level == "SEVERE":
                error_logs.append(message)
                print(f"   🚨 ERROR: {message}")
            elif level == "WARNING":
                warning_logs.append(message)
                print(f"   ⚠️  WARNING: {message}")
            else:
                info_logs.append(message)
                # Only print first 5 info logs to avoid spam
                if len(info_logs) <= 5:
                    print(f"   ℹ️  INFO: {message}")

        print(
            f"\n📊 Console Summary: {len(error_logs)} errors, {len(warning_logs)} warnings, {len(info_logs)} info logs"
        )

        print("\n🔍 CHECKING JAVASCRIPT ERRORS:")

        # Check for JavaScript errors
        js_errors = driver.execute_script("""
            var errors = [];
            var originalError = window.onerror;
            window.onerror = function(message, source, lineno, colno, error) {
                errors.push({
                    message: message,
                    source: source,
                    line: lineno,
                    column: colno,
                    error: error ? error.toString() : 'No error object'
                });
                return false;
            };
            return errors;
        """)

        if js_errors:
            print(f"Found {len(js_errors)} JavaScript errors:")
            for error in js_errors:
                print(f"   🚨 {error['message']} at {error['source']}:{error['line']}")
        else:
            print("✅ No JavaScript errors detected")

        print("\n🔍 CHECKING WORLD MANAGER STATUS:")

        # Check if WorldManager was initialized
        worldmanager_status = driver.execute_script("""
            if (typeof window.worldManager !== 'undefined') {
                return {
                    exists: true,
                    worldData: window.worldManager.worldData ? 'loaded' : 'null',
                    locationsCount: window.worldManager.worldData ? window.worldManager.worldData.locations.length : 0,
                    initializationComplete: true
                };
            } else {
                return {
                    exists: false,
                    initializationComplete: false
                };
            }
        """)

        print("📋 WorldManager Status:")
        print(f"   Exists: {worldmanager_status['exists']}")
        print(f"   World Data: {worldmanager_status.get('worldData', 'N/A')}")
        print(f"   Locations Count: {worldmanager_status.get('locationsCount', 'N/A')}")
        print(
            f"   Initialization Complete: {worldmanager_status.get('initializationComplete', 'N/A')}"
        )

        print("\n🔍 ATTEMPTING MANUAL WORLD CONTAINER REVEAL:")

        # Try to manually trigger hideLoading
        if worldmanager_status["exists"]:
            print("   Trying to call hideLoading() manually...")

            try:
                driver.execute_script("""
                    if (window.worldManager && window.worldManager.hideLoading) {
                        window.worldManager.hideLoading();
                        return 'hideLoading called successfully';
                    } else {
                        return 'hideLoading method not available';
                    }
                """)

                # Wait a moment for DOM update
                await asyncio.sleep(2)

                # Check worldContainer visibility again
                worldcontainer_after = driver.execute_script(
                    "return document.getElementById('worldContainer').style.display;"
                )
                worldcontainer_visible_after = driver.execute_script(
                    "return document.getElementById('worldContainer').offsetWidth > 0;"
                )

                print("   After manual trigger:")
                print(f"   Display style: '{worldcontainer_after}'")
                print(f"   Visible (has width): {worldcontainer_visible_after}")

            except Exception as e:
                print(f"   Error calling hideLoading: {e}")

        else:
            print("   Cannot call hideLoading - WorldManager not initialized")

        print("\n🔍 CHECKING NETWORK REQUESTS:")

        # Check if static files loaded properly
        network_logs = driver.get_log("network")
        static_files = []
        failed_requests = []

        for log in network_logs:
            if "static/" in log.get("message", ""):
                static_files.append(log["message"])
            if "status" in log and log["status"] >= 400:
                failed_requests.append(log)

        print(f"   Static files requested: {len(static_files)}")
        print(f"   Failed requests: {len(failed_requests)}")

        if failed_requests:
            print("   Failed requests:")
            for req in failed_requests[:5]:  # Show first 5
                print(f"     🚨 {req.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Debug script error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        driver.quit()
        print("\n🔍 Debug session completed")


async def main():
    """Run the debug session."""
    await debug_worldcontainer_visibility()


if __name__ == "__main__":
    asyncio.run(main())
