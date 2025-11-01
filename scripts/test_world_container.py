#!/usr/bin/env python3
"""
Test script to check if worldContainer becomes visible

This script uses selenium to test the actual index.html loading
and debug why the worldContainer remains hidden.
"""

import asyncio
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


async def test_world_container_visibility():
    """Test if worldContainer becomes visible in the real index.html"""
    print("🔍 Testing worldContainer visibility in index.html")
    print("=" * 50)

    # Setup Chrome with headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Navigate to the index.html
        print("🌐 Loading index.html...")
        driver.get("http://localhost:8081/index.html")

        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(3)

        # Check for loading element
        try:
            loading_element = driver.find_element(By.ID, "loading")
            loading_visible = loading_element.is_displayed()
            print(f"📊 Loading element visible: {loading_visible}")
            print(f"   Loading text: {loading_element.text}")
        except NoSuchElementException:
            print("❌ Loading element not found")

        # Check for worldContainer
        try:
            world_container = driver.find_element(By.ID, "worldContainer")
            world_visible = world_container.is_displayed()
            world_display_style = world_container.value_of_css_property("display")
            print(f"🌍 WorldContainer element found: {bool(world_container)}")
            print(f"   WorldContainer visible: {world_visible}")
            print(f"   WorldContainer display style: {world_display_style}")

            if not world_visible:
                print("⚠️  WorldContainer is not visible!")

                # Check if it exists in DOM at all
                world_exists = driver.execute_script(
                    "return document.getElementById('worldContainer') !== null;"
                )
                print(f"   WorldContainer exists in DOM: {world_exists}")

                # Check console for errors
                console_logs = driver.get_log("browser")
                if console_logs:
                    print("🔍 Console logs:")
                    for log in console_logs[-10:]:  # Last 10 logs
                        level = log["level"]
                        message = log["message"]
                        print(f"   [{level}] {message}")

                # Try to wait a bit longer and check again
                print("⏳ Waiting 5 more seconds for worldContainer to appear...")
                time.sleep(5)

                world_visible_after_wait = world_container.is_displayed()
                print(
                    f"   WorldContainer visible after wait: {world_visible_after_wait}"
                )

                if not world_visible_after_wait:
                    # Try to manually trigger worldManager init
                    print("🔧 Attempting to manually trigger worldManager...")
                    try:
                        driver.execute_script("""
                            console.log('Manual trigger attempt');
                            if (window.worldManager) {
                                console.log('worldManager exists:', window.worldManager);
                                console.log('worldManager.worldData:', window.worldManager.worldData);
                                console.log('Calling hideLoading manually...');
                                window.worldManager.hideLoading();
                            } else {
                                console.log('worldManager does not exist');
                            }
                        """)
                        time.sleep(2)
                        world_visible_after_manual = world_container.is_displayed()
                        print(
                            f"   WorldContainer visible after manual trigger: {world_visible_after_manual}"
                        )
                    except Exception as e:
                        print(f"   Error during manual trigger: {e}")
            else:
                print("✅ WorldContainer is visible!")

                # Check for locations
                try:
                    locations_wrapper = driver.find_element(By.ID, "locationsWrapper")
                    locations_children = driver.execute_script(
                        "return arguments[0].children.length;", locations_wrapper
                    )
                    print(f"   Locations wrapper children: {locations_children}")

                    if locations_children > 0:
                        print("✅ Locations are rendered!")
                    else:
                        print("⚠️  No locations rendered")
                except Exception as e:
                    print(f"❌ Error checking locations: {e}")

        except Exception as e:
            print(f"❌ Error finding worldContainer: {e}")

        # Take screenshot for debugging
        try:
            screenshot_path = "debug_screenshot.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        if driver:
            driver.quit()

    print("🏁 Test completed")


if __name__ == "__main__":
    asyncio.run(test_world_container_visibility())
