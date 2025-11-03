#!/usr/bin/env python3
"""
/nudge Notification System for DCMAIDBot Deployments

This script handles sending notifications to the /nudge endpoint for various
deployment events including successes, failures, promotions, and rollbacks.
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class NudgeMessage:
    """Structure for /nudge notification messages"""

    user_ids: List[int]
    message: str
    urgency: str = "medium"  # low, medium, high, critical
    pr_url: Optional[str] = None
    prp_file: Optional[str] = None
    prp_section: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NudgeNotifier:
    """Handles /nudge notifications for deployment events"""

    def __init__(self, webhook_url: str, admin_ids: List[int] = None):
        self.webhook_url = webhook_url
        self.admin_ids = admin_ids or []
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_notification(self, message: NudgeMessage) -> bool:
        """Send a notification via /nudge endpoint"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        # Use provided user IDs or fall back to admin IDs
        user_ids = message.user_ids if message.user_ids else self.admin_ids

        if not user_ids:
            logger.warning("No user IDs provided for notification")
            return False

        payload = {
            "user_ids": user_ids,
            "message": message.message,
            "urgency": message.urgency,
        }

        # Add optional fields
        if message.pr_url:
            payload["pr_url"] = message.pr_url
        if message.prp_file:
            payload["prp_file"] = message.prp_file
        if message.prp_section:
            payload["prp_section"] = message.prp_section
        if message.metadata:
            payload["metadata"] = message.metadata

        try:
            logger.info(f"Sending /nudge notification: {message.message[:100]}...")

            async with self.session.post(
                self.webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("✅ /nudge notification sent successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to send /nudge notification: {response.status} - {error_text}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error("❌ Timeout sending /nudge notification")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending /nudge notification: {e}")
            return False

    async def notify_deployment_success(
        self, version: str, environment: str, metadata: Dict = None
    ) -> bool:
        """Send notification for successful deployment"""
        message = NudgeMessage(
            user_ids=[],
            message=f"✅ PRP-011 deployment successful - {version} deployed to {environment}",
            urgency="low",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "deployment_success",
                "version": version,
                "environment": environment,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            },
        )
        return await self.send_notification(message)

    async def notify_deployment_failed(
        self, version: str, environment: str, error: str, metadata: Dict = None
    ) -> bool:
        """Send notification for failed deployment"""
        message = NudgeMessage(
            user_ids=[],
            message=f"🚨 PRP-011 deployment failed - {version} to {environment}\n\nError: {error}",
            urgency="high",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "deployment_failed",
                "version": version,
                "environment": environment,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            },
        )
        return await self.send_notification(message)

    async def notify_canary_promotion(self, version: str, metrics: Dict = None) -> bool:
        """Send notification for canary promotion"""
        metrics_text = ""
        if metrics:
            metrics_text = "\n\nMetrics:\n"
            for key, value in metrics.items():
                metrics_text += f"- {key}: {value}\n"

        message = NudgeMessage(
            user_ids=[],
            message=f"🚀 PRP-011 canary promotion initiated - {version}{metrics_text}",
            urgency="medium",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "canary_promotion",
                "version": version,
                "metrics": metrics or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return await self.send_notification(message)

    async def notify_rollback_triggered(
        self, deployment_type: str, version: str, reason: str, metadata: Dict = None
    ) -> bool:
        """Send notification for rollback trigger"""
        message = NudgeMessage(
            user_ids=[],
            message=f"⚠️ PRP-011 rollback triggered - {deployment_type} deployment of {version}\n\nReason: {reason}",
            urgency="high",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "rollback_triggered",
                "deployment_type": deployment_type,
                "version": version,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            },
        )
        return await self.send_notification(message)

    async def notify_performance_degradation(self, metrics: Dict = None) -> bool:
        """Send notification for performance degradation"""
        metrics_text = ""
        if metrics:
            metrics_text = "\n\nAffected metrics:\n"
            for key, value in metrics.items():
                metrics_text += f"- {key}: {value}\n"

        message = NudgeMessage(
            user_ids=[],
            message=f"📉 PRP-011 performance degradation detected{metrics_text}",
            urgency="medium",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "performance_degradation",
                "metrics": metrics or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return await self.send_notification(message)

    async def notify_slo_breached(
        self, slo_name: str, current_value: float, threshold: float
    ) -> bool:
        """Send notification for SLO breach"""
        message = NudgeMessage(
            user_ids=[],
            message=f"🚨 SLO Breach Alert - {slo_name}\n\nCurrent: {current_value}\nThreshold: {threshold}",
            urgency="high",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "slo_breached",
                "slo_name": slo_name,
                "current_value": current_value,
                "threshold": threshold,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return await self.send_notification(message)

    async def notify_llm_judge_decision(
        self, version: str, decision: str, reasoning: str, confidence: float
    ) -> bool:
        """Send notification for LLM judge decision"""
        emoji = "✅" if decision == "promote" else "❌"
        message = NudgeMessage(
            user_ids=[],
            message=f"{emoji} LLM Judge Decision - {version}\n\nDecision: {decision.upper()}\nConfidence: {confidence}%\n\nReasoning: {reasoning}",
            urgency="medium" if decision == "promote" else "high",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "llm_judge_decision",
                "version": version,
                "decision": decision,
                "reasoning": reasoning,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return await self.send_notification(message)

    async def notify_gitops_update(self, action: str, details: Dict = None) -> bool:
        """Send notification for GitOps updates"""
        message = NudgeMessage(
            user_ids=[],
            message=f"🔄 GitOps Update - {action}",
            urgency="low",
            prp_file="PRPs/PRP-011.md",
            prp_section="progress",
            metadata={
                "event": "gitops_update",
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        return await self.send_notification(message)


async def main():
    parser = argparse.ArgumentParser(
        description="Send /nudge notifications for DCMAIDBot deployments"
    )
    parser.add_argument("--webhook-url", required=True, help="Nudge webhook URL")
    parser.add_argument("--admin-ids", help="Comma-separated list of admin user IDs")
    parser.add_argument(
        "--event",
        required=True,
        choices=[
            "deployment_success",
            "deployment_failed",
            "canary_promotion",
            "rollback_triggered",
            "performance_degradation",
            "slo_breached",
            "llm_judge_decision",
            "gitops_update",
        ],
        help="Event type",
    )
    parser.add_argument("--version", help="Deployment version")
    parser.add_argument("--environment", help="Deployment environment")
    parser.add_argument("--error", help="Error message (for failed deployments)")
    parser.add_argument("--reason", help="Reason (for rollbacks)")
    parser.add_argument("--decision", help="LLM judge decision")
    parser.add_argument("--reasoning", help="LLM judge reasoning")
    parser.add_argument("--confidence", type=float, help="LLM judge confidence")
    parser.add_argument("--slo-name", help="SLO name (for SLO breaches)")
    parser.add_argument(
        "--current-value", type=float, help="Current value (for SLO breaches)"
    )
    parser.add_argument(
        "--threshold", type=float, help="Threshold value (for SLO breaches)"
    )
    parser.add_argument("--metadata", help="JSON metadata string")
    parser.add_argument("--metrics", help="JSON metrics string")

    args = parser.parse_args()

    # Parse admin IDs
    admin_ids = []
    if args.admin_ids:
        try:
            admin_ids = [int(id.strip()) for id in args.admin_ids.split(",")]
        except ValueError:
            logger.error("Invalid admin IDs format")
            sys.exit(1)

    # Parse metadata
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            logger.error("Invalid metadata JSON")
            sys.exit(1)

    # Parse metrics
    metrics = {}
    if args.metrics:
        try:
            metrics = json.loads(args.metrics)
        except json.JSONDecodeError:
            logger.error("Invalid metrics JSON")
            sys.exit(1)

    # Send notification
    async with NudgeNotifier(args.webhook_url, admin_ids) as notifier:
        success = False

        if args.event == "deployment_success":
            success = await notifier.notify_deployment_success(
                args.version, args.environment, metadata
            )
        elif args.event == "deployment_failed":
            success = await notifier.notify_deployment_failed(
                args.version, args.environment, args.error, metadata
            )
        elif args.event == "canary_promotion":
            success = await notifier.notify_canary_promotion(args.version, metrics)
        elif args.event == "rollback_triggered":
            success = await notifier.notify_rollback_triggered(
                "stable", args.version, args.reason, metadata
            )
        elif args.event == "performance_degradation":
            success = await notifier.notify_performance_degradation(metrics)
        elif args.event == "slo_breached":
            success = await notifier.notify_slo_breached(
                args.slo_name, args.current_value, args.threshold
            )
        elif args.event == "llm_judge_decision":
            success = await notifier.notify_llm_judge_decision(
                args.version, args.decision, args.reasoning, args.confidence
            )
        elif args.event == "gitops_update":
            success = await notifier.notify_gitops_update(args.version, metadata)

        if success:
            logger.info("✅ Notification sent successfully")
            sys.exit(0)
        else:
            logger.error("❌ Failed to send notification")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
