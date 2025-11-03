#!/usr/bin/env python3
"""
Update DCMaidBot Deployment with Analytics

Script to update the Kubernetes deployment to use the new analytics-enabled image.
"""

import subprocess
import sys
import time
import json


def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    print(f"🔧 Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        if result.stderr and result.returncode != 0:
            print(f"   Error: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        raise


def update_deployment_with_analytics():
    """Update deployment to use analytics-enabled image"""
    print("🚀 Updating DCMaidBot deployment with analytics capabilities...")

    # New image with analytics
    analytics_image = "ghcr.io/dcversus/dcmaidbot:analytics"

    try:
        # Update the deployment image
        print(f"📦 Updating image to: {analytics_image}")
        run_command(
            f"kubectl set image deployment/dcmaidbot-prod dcmaidbot={analytics_image} -n prod-core"
        )

        # Wait for rollout to complete
        print("⏳ Waiting for rollout to complete...")
        run_command(
            "kubectl rollout status deployment/dcmaidbot-prod -n prod-core --timeout=300s"
        )

        print("✅ Deployment updated successfully!")

        # Test the metrics endpoint
        print("🔍 Testing metrics endpoint...")

        # Start port forward
        port_forward = subprocess.Popen([
            "kubectl", "port-forward", "-n", "prod-core", "svc/dcmaidbot-prod", "8081:8080"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        time.sleep(5)  # Wait for port forward to be ready

        try:
            import requests

            # Test metrics endpoint
            response = requests.get("http://localhost:8081/metrics", timeout=10)
            if response.status_code == 200:
                metrics = response.text
                if "dcmaidbot" in metrics:
                    print("✅ Metrics endpoint is working!")
                    print(f"   Found {metrics.count('dcmaidbot_')} dcmaidbot metrics")
                else:
                    print("⚠️  Metrics endpoint accessible but no dcmaidbot metrics found")
            else:
                print(f"❌ Metrics endpoint returned status {response.status_code}")

            # Test health endpoint
            response = requests.get("http://localhost:8081/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint is working!")
            else:
                print(f"❌ Health endpoint returned status {response.status_code}")

        except Exception as e:
            print(f"❌ Error testing endpoints: {e}")
        finally:
            port_forward.terminate()
            port_forward.wait()

        print("\n🎉 Analytics deployment completed!")
        print("\nNext steps:")
        print("1. Import Grafana dashboard: grafana-dcmaidbot-dashboard.json")
        print("2. Monitor metrics at: http://localhost:3000 (Grafana)")
        print("3. Check Prometheus: http://localhost:9090")
        print("4. Verify Loki logs: http://localhost:3000/explore")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update deployment: {e}")
        return False


def check_analytics_image_exists():
    """Check if the analytics image exists in the registry"""
    print("🔍 Checking if analytics image exists...")

    # Try to pull the image to see if it exists
    try:
        result = run_command(
            "docker pull ghcr.io/dcversus/dcmaidbot:analytics",
            check=False
        )
        if result.returncode == 0:
            print("✅ Analytics image found in registry!")
            return True
        else:
            print("❌ Analytics image not found in registry")
            return False
    except:
        print("❌ Could not check image availability")
        return False


def main():
    """Main function"""
    print("🤖 DCMaidBot Analytics Deployment")
    print("=" * 50)

    # Check if analytics image exists
    if not check_analytics_image_exists():
        print("\n⚠️  Analytics image not ready yet.")
        print("Please wait for the GitHub Actions build to complete, then run this script again.")
        print("You can check the build status at: https://github.com/dcversus/dcmaidbot/actions")
        sys.exit(1)

    # Update deployment
    success = update_deployment_with_analytics()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()