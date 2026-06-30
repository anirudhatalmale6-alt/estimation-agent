"""
Demo: Full workflow from Teams meeting transcript to Performance Test Plan PDF.

Workflow:
1. Parse a Teams meeting transcript (.vtt)
2. Extract NFR answers, numeric targets, open items, risks
3. Combine with HLD summary and PET estimation data
4. Generate a professional Performance Test Plan PDF

Usage:
    python -m examples.demo_transcript_to_testplan
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.transcript_processor import TranscriptProcessor
from src.test_plan_generator import TestPlanGenerator

SAMPLE_TRANSCRIPT = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v Sarah Johnson>Welcome everyone to the NFR discovery session for the Billing Gateway project.

00:00:06.000 --> 00:00:12.000
<v Sarah Johnson>This is a new billing middleware service that processes customer payments and billing cycles for our telecom platform.

00:00:13.000 --> 00:00:20.000
<v Sarah Johnson>Let's start with the architecture. Mike, can you walk us through the HLD?

00:00:21.000 --> 00:00:35.000
<v Mike Chen>Sure. The Billing Gateway is a Java Spring Boot application deployed on Kubernetes. It connects to an Oracle database for customer accounts and uses Kafka for event streaming to downstream systems.

00:00:36.000 --> 00:00:48.000
<v Mike Chen>We have three main APIs - account lookup, payment processing, and billing cycle trigger. The billing cycle runs as a batch job every night processing about 500000 accounts.

00:00:49.000 --> 00:00:58.000
<v Sarah Johnson>Thanks Mike. What about the expected load? How many concurrent users do we expect?

00:00:59.000 --> 00:01:10.000
<v Mike Chen>Normal hours we see about 2000 concurrent users. Peak is around 5000 concurrent users, usually on the first of the month when everyone checks their bills.

00:01:11.000 --> 00:01:20.000
<v Sarah Johnson>And transaction throughput?

00:01:21.000 --> 00:01:30.000
<v Mike Chen>We target 500 transactions per second at peak. Normal is around 200 TPS. The API response time should be under 2 seconds for reads and 3 seconds for writes.

00:01:31.000 --> 00:01:40.000
<v Sarah Johnson>What about availability targets?

00:01:41.000 --> 00:01:48.000
<v Mike Chen>We need 99.95 percent availability. Error rate should be less than 0.5 percent under normal load.

00:01:49.000 --> 00:02:00.000
<v Sarah Johnson>Resource utilization thresholds?

00:02:01.000 --> 00:02:10.000
<v Mike Chen>CPU should stay under 65 percent, memory under 75 percent. We had issues last release where CPU spiked to 95% during billing cycle.

00:02:11.000 --> 00:02:20.000
<v Lisa Park>That's a known bottleneck from the previous release. The billing cycle query was doing a full table scan. We've added an index but need to validate it under load.

00:02:21.000 --> 00:02:30.000
<v Sarah Johnson>Good, we'll add that as a targeted test scenario. What about the batch processing SLA?

00:02:31.000 --> 00:02:40.000
<v Mike Chen>The nightly billing cycle must complete within 4 hours. It processes 500000 accounts and generates invoices. Currently running in about 3 hours in production.

00:02:41.000 --> 00:02:50.000
<v Sarah Johnson>External integrations?

00:02:51.000 --> 00:03:00.000
<v Mike Chen>We integrate with Stripe for payment processing and SendGrid for email notifications. We also send events to Kafka which downstream CRM consumes.

00:03:01.000 --> 00:03:10.000
<v Sarah Johnson>Authentication?

00:03:11.000 --> 00:03:18.000
<v Mike Chen>OAuth 2.0 with JWT tokens. API gateway handles rate limiting at 1000 requests per minute per client.

00:03:19.000 --> 00:03:28.000
<v Sarah Johnson>Test data - can we use production data?

00:03:29.000 --> 00:03:38.000
<v Lisa Park>We need to check with the security team about masking production data. We might need synthetic data generation instead.

00:03:39.000 --> 00:03:48.000
<v Sarah Johnson>What monitoring tools are available?

00:03:49.000 --> 00:03:58.000
<v Mike Chen>We use Dynatrace for APM, Grafana with Prometheus for infrastructure, and Splunk for log aggregation.

00:03:59.000 --> 00:04:08.000
<v Sarah Johnson>Environment for perf testing?

00:04:09.000 --> 00:04:18.000
<v Mike Chen>We have a Pre-Prod environment that mirrors production. It should be available next week for our testing window.

00:04:19.000 --> 00:04:28.000
<v Sarah Johnson>Go-live date?

00:04:29.000 --> 00:04:35.000
<v Mike Chen>We're targeting August 15th for production release.
"""


def main():
    print("=" * 70)
    print("  Teams Transcript -> Performance Test Plan Demo")
    print("=" * 70)

    os.makedirs("examples/output", exist_ok=True)

    print("\n--- Step 1: Parse Teams Meeting Transcript ---")
    processor = TranscriptProcessor()
    result = processor.process_transcript(SAMPLE_TRANSCRIPT, format="vtt")

    print(f"  Entries parsed: {result['entry_count']}")
    print(f"  Speakers: {', '.join(result['speakers'])}")

    print("\n--- Step 2: Extract NFR Data ---")
    extracted = result["extracted"]
    print(result["summary"])

    print("\n--- Step 3: Generate Performance Test Plan PDF ---")
    generator = TestPlanGenerator()

    hld_summary = {
        "description": (
            "The Billing Gateway is a Java Spring Boot middleware service deployed on Kubernetes. "
            "It processes customer payments and billing cycles for the telecom platform, "
            "connecting to Oracle for account data and Kafka for event streaming."
        ),
        "in_scope": [
            "Account Lookup API - GET /api/accounts/{id}",
            "Payment Processing API - POST /api/payments",
            "Billing Cycle Trigger API - POST /api/billing/cycle",
            "Nightly batch billing cycle (500K accounts)",
            "Kafka event publishing to downstream CRM",
            "OAuth 2.0 / JWT authentication flow"
        ]
    }

    estimation_data = {
        "total_pd_before_efficiency": 55.69,
        "total_pd_after_efficiency": 45.11,
        "efficiency_percentage": 19,
        "cost_per_pd": 250,
        "total_cost": 11277.50
    }

    pet_ticket = {
        "ticket_id": "PERF-2847",
        "project_name": "Billing Gateway v2.1"
    }

    output_path = generator.generate(
        project_name="Billing Gateway v2.1",
        output_path="examples/output/Performance_Test_Plan_Billing_Gateway.pdf",
        hld_summary=hld_summary,
        nfr_data=extracted,
        estimation_data=estimation_data,
        pet_ticket=pet_ticket
    )

    file_size = os.path.getsize(output_path)
    print(f"\n  PDF generated: {output_path}")
    print(f"  File size: {file_size:,} bytes")

    print("\n--- Summary ---")
    print(f"""
  Input:
    - Teams transcript: {result['entry_count']} entries from {len(result['speakers'])} speakers
    - HLD summary: 6 in-scope items
    - PET estimation: {estimation_data['total_pd_after_efficiency']} PD

  Extracted from transcript:
    - Numeric targets: {len(extracted.get('numeric_values', {}))} values
    - Technologies: {len(extracted.get('technologies_mentioned', []))} identified
    - Open items: {len(extracted.get('open_items', []))}
    - Risks: {len(extracted.get('risks', []))}

  Output:
    - 12-section Performance Test Plan PDF
    - Includes: scope, workload model, scenarios, targets, schedule, risks
    - NFR answers appended as Appendix A
    """)

    print("=" * 70)
    print("  Done. Open the PDF to review the test plan.")
    print("=" * 70)


if __name__ == "__main__":
    main()
