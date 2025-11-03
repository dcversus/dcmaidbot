#!/usr/bin/env python3
"""
Deploy Analytics-Enabled Bot (PRP-012)

Script to deploy dcmaidbot with analytics and observability features.
"""

import subprocess
import sys
from pathlib import Path


class AnalyticsBotDeployer:
    """Handle deployment of analytics-enabled bot"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.namespace = "prod-core"

    def run_command(
        self, command: str, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        print(f"🔧 Running: {command}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=check
            )
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            if result.stderr and result.returncode != 0:
                print(f"   Error: {result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}")
            raise

    def check_prerequisites(self) -> bool:
        """Check that all prerequisites are met"""
        print("🔍 Checking prerequisites...")

        # Check if we're in the right directory
        if not (self.project_root / "bot.py").exists():
            print("❌ bot.py not found. Make sure you're in the dcmaidbot directory.")
            return False

        # Check if kubectl is available
        try:
            self.run_command("kubectl version --client", check=False)
        except Exception:
            print("❌ kubectl not found. Please install kubectl.")
            return False

        # Check if we can access the cluster
        try:
            result = self.run_command("kubectl get nodes", check=False)
            if result.returncode != 0:
                print("❌ Cannot access Kubernetes cluster.")
                return False
        except Exception:
            print("❌ Cannot access Kubernetes cluster.")
            return False

        # Check if monitoring namespace exists
        result = self.run_command("kubectl get namespace monitoring", check=False)
        if result.returncode != 0:
            print("❌ Monitoring namespace not found.")
            return False

        print("✅ All prerequisites met.")
        return True

    def build_and_push_image(self) -> bool:
        """Build and push the Docker image with analytics"""
        print("🐳 Building Docker image with analytics...")

        # Get current image tag
        try:
            result = self.run_command(
                "kubectl get deployment dcmaidbot-prod -n prod-core -o jsonpath='{.spec.template.spec.containers[0].image}'",
                check=False,
            )
            current_image = result.stdout.strip()
            print(f"   Current image: {current_image}")

            # Extract tag and increment
            if ":" in current_image:
                registry, tag = current_image.rsplit(":", 1)
                try:
                    tag_num = int(tag.split("-")[-1])
                    new_tag = f"v{tag_num + 1}"
                except Exception:
                    new_tag = "v1"
            else:
                registry = current_image
                new_tag = "v1"

            new_image = f"{registry}:{new_tag}-analytics"
            print(f"   New image: {new_image}")

        except Exception:
            print("⚠️  Could not determine current image, using default")
            new_image = "ghcr.io/uz0/dcmaidbot:latest-analytics"

        # Build image (if Dockerfile exists)
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            try:
                self.run_command(f"docker build -t {new_image} .", check=True)
                print("✅ Docker image built successfully")

                # Push image
                self.run_command(f"docker push {new_image}", check=True)
                print("✅ Docker image pushed successfully")

                return new_image
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to build/push Docker image: {e}")
                return None
        else:
            print("⚠️  No Dockerfile found, assuming image is already built")
            return new_image

    def update_deployment(self, image: str) -> bool:
        """Update the Kubernetes deployment with the new image"""
        print("🚀 Updating Kubernetes deployment...")

        try:
            # Update the deployment image
            self.run_command(
                f"kubectl set image deployment/dcmaidbot-prod dcmaidbot={image} -n {self.namespace}",
                check=True,
            )

            # Wait for rollout to complete
            print("⏳ Waiting for rollout to complete...")
            self.run_command(
                f"kubectl rollout status deployment/dcmaidbot-prod -n {self.namespace} --timeout=300s",
                check=True,
            )

            print("✅ Deployment updated successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to update deployment: {e}")
            return False

    def verify_deployment(self) -> bool:
        """Verify that the deployment is working correctly"""
        print("🔍 Verifying deployment...")

        try:
            # Check pod status
            result = self.run_command(
                f"kubectl get pods -n {self.namespace} -l app=dcmaidbot", check=True
            )

            if "Running" not in result.stdout:
                print("❌ Pod is not running")
                return False

            # Check if metrics endpoint is accessible
            pod_name = self.run_command(
                f"kubectl get pods -n {self.namespace} -l app=dcmaidbot -o jsonpath='{{.items[0].metadata.name}}'",
                check=True,
            ).stdout.strip()

            print(f"   Testing metrics endpoint on pod: {pod_name}")

            # Port forward to test locally
            port_forward = subprocess.Popen(
                [
                    "kubectl",
                    "port-forward",
                    "-n",
                    self.namespace,
                    "svc/dcmaidbot-prod",
                    "8081:8080",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            import time

            time.sleep(5)  # Wait for port forward to be ready

            try:
                import asyncio

                import aiohttp

                async def test_metrics():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "http://localhost:8081/metrics"
                        ) as response:
                            if response.status == 200:
                                metrics = await response.text()
                                if "dcmaidbot" in metrics:
                                    print("✅ Metrics endpoint is working")
                                    return True
                                else:
                                    print(
                                        "⚠️  Metrics endpoint accessible but no dcmaidbot metrics found"
                                    )
                                    return False
                            else:
                                print(
                                    f"❌ Metrics endpoint returned status {response.status}"
                                )
                                return False

                result = asyncio.run(test_metrics())
                return result

            finally:
                port_forward.terminate()
                port_forward.wait()

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def deploy(self) -> bool:
        """Run the complete deployment process"""
        print("🚀 Starting Analytics Bot Deployment")
        print("=" * 50)

        # Check prerequisites
        if not self.check_prerequisites():
            return False

        # Build and push image
        image = self.build_and_push_image()
        if not image:
            return False

        # Update deployment
        if not self.update_deployment(image):
            return False

        # Verify deployment
        if not self.verify_deployment():
            return False

        print("\n🎉 Analytics bot deployment completed successfully!")
        print("\nNext steps:")
        print("1. Check Grafana dashboard: http://localhost:3000")
        print("2. Monitor Prometheus: http://localhost:9090")
        print("3. Test metrics collection with: python scripts/test_analytics_setup.py")

        return True


def main():
    """Main deployment function"""
    deployer = AnalyticsBotDeployer()

    try:
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
