"""
Demo: Full end-to-end PET estimation workflow.

Simulates the complete pipeline:
1. Email trigger detects new PET ticket notification
2. Orchestrator reads ticket, extracts HLD, runs estimation
3. Posts estimation report to Jira (simulated)
4. Drafts NFR discovery meeting invite with PM
5. Processes meeting transcript (simulated)
6. Generates Performance Test Plan PDF

Usage:
    python3 -m examples.demo_full_workflow
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow_orchestrator import WorkflowOrchestrator
from src.meeting_scheduler import MeetingScheduler
from src.transcript_processor import TranscriptProcessor
from src.test_plan_generator import TestPlanGenerator


SAMPLE_TRANSCRIPT = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v Sarah Johnson>Welcome everyone to the NFR discovery session for the Billing Gateway project.

00:00:06.000 --> 00:00:12.000
<v Sarah Johnson>This is a new billing middleware service that processes customer payments and billing cycles for our telecom platform.

00:00:21.000 --> 00:00:35.000
<v Mike Chen>The Billing Gateway is a Java Spring Boot application deployed on Kubernetes. It connects to an Oracle database for customer accounts and uses Kafka for event streaming to downstream systems.

00:00:36.000 --> 00:00:48.000
<v Mike Chen>We have three main APIs - account lookup, payment processing, and billing cycle trigger. The billing cycle runs as a batch job every night processing about 500000 accounts.

00:00:59.000 --> 00:01:10.000
<v Mike Chen>Normal hours we see about 2000 concurrent users. Peak is around 5000 concurrent users, usually on the first of the month when everyone checks their bills.

00:01:21.000 --> 00:01:30.000
<v Mike Chen>We target 500 transactions per second at peak. The API response time should be under 2 seconds for reads and 3 seconds for writes.

00:01:41.000 --> 00:01:48.000
<v Mike Chen>We need 99.95 percent availability. Error rate should be less than 0.5 percent under normal load.

00:02:01.000 --> 00:02:10.000
<v Mike Chen>CPU should stay under 65 percent, memory under 75 percent. We had issues last release where CPU spiked to 95 percent during billing cycle.

00:02:11.000 --> 00:02:20.000
<v Lisa Park>That's a known bottleneck from the previous release. The billing cycle query was doing a full table scan.

00:02:31.000 --> 00:02:40.000
<v Mike Chen>The nightly billing cycle must complete within 4 hours. It processes 500000 accounts.

00:02:51.000 --> 00:03:00.000
<v Mike Chen>We integrate with Stripe for payment processing and SendGrid for email. We also send events to Kafka.

00:03:11.000 --> 00:03:18.000
<v Mike Chen>OAuth 2.0 with JWT tokens. API gateway handles rate limiting at 1000 requests per minute per client.

00:03:29.000 --> 00:03:38.000
<v Lisa Park>We need to check with the security team about masking production data.

00:03:49.000 --> 00:03:58.000
<v Mike Chen>We use Dynatrace for APM, Grafana with Prometheus for infrastructure, and Splunk for log aggregation.

00:04:09.000 --> 00:04:18.000
<v Mike Chen>We have a Pre-Prod environment that mirrors production.

00:04:29.000 --> 00:04:35.000
<v Mike Chen>We're targeting August 15th for production release.
"""


def main():
    output_dir = "examples/output"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("  FULL PET ESTIMATION WORKFLOW DEMO")
    print("=" * 70)

    # --- PHASE 1: Email Trigger ---
    print("\n" + "=" * 70)
    print("  PHASE 1: Email Trigger (Simulated)")
    print("=" * 70)
    print("  Outlook notification received:")
    print("  Subject: PET Estimation Ticket Created - PET-2847")
    print("  From: jira-notifications@company.com")
    print("  Body: A new PET ticket PET-2847 has been created for")
    print("        Billing Gateway v2.1. HLD document attached.")
    print("  -> Extracted ticket ID: PET-2847")

    pet_ticket_id = "PET-2847"

    # --- PHASE 2: Auto-Estimation ---
    print("\n" + "=" * 70)
    print("  PHASE 2: Auto-Estimation + Meeting Draft")
    print("=" * 70)

    orchestrator = WorkflowOrchestrator(
        meeting_scheduler=MeetingScheduler(),
        transcript_processor=TranscriptProcessor(),
        test_plan_generator=TestPlanGenerator()
    )

    results = orchestrator.process_new_pet_ticket(
        pet_ticket_id=pet_ticket_id,
        perf_manager_email="sarah.johnson@company.com",
        output_dir=output_dir
    )

    print("\n  Generated files:")
    for step in results["steps"]:
        if "files" in step:
            for key, path in step["files"].items():
                if isinstance(path, str) and os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"    {key}: {path} ({size:,} bytes)")
        elif "path" in step:
            if os.path.exists(step["path"]):
                size = os.path.getsize(step["path"])
                print(f"    {step['step']}: {step['path']} ({size:,} bytes)")

    # --- PHASE 3: Post-Meeting Transcript Processing ---
    print("\n" + "=" * 70)
    print("  PHASE 3: Post-Meeting - Transcript Processing")
    print("=" * 70)
    print("  NFR discovery meeting completed.")
    print("  Transcript downloaded from Teams (.vtt format)")
    print("  Processing transcript...")

    transcript_results = orchestrator.process_meeting_transcript(
        pet_ticket_id=pet_ticket_id,
        transcript_content=SAMPLE_TRANSCRIPT,
        transcript_format="vtt",
        output_dir=output_dir
    )

    # --- SUMMARY ---
    print("\n" + "=" * 70)
    print("  WORKFLOW COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"""
  PET Ticket: {pet_ticket_id}

  Phase 1 - Email Trigger:
    Detected PET notification email
    Extracted ticket ID: {pet_ticket_id}

  Phase 2 - Auto-Estimation:
    Estimation: {results['summary']['estimation_pd']} person-days
    Cost: ${results['summary']['estimation_cost']:,.2f}
    Posted estimation to Jira (simulated)
    Meeting invite drafted for: {results['summary']['pm_name']}

  Phase 3 - Post-Meeting:
    Transcript: {transcript_results['transcript_entries']} entries from {len(transcript_results['speakers'])} speakers
    Speakers: {', '.join(transcript_results['speakers'])}
    Technologies: {', '.join(transcript_results['technologies'])}
    Numeric targets: {json.dumps(transcript_results['numeric_values'], indent=6)}
    Open items: {transcript_results['open_items']}
    Risks: {transcript_results['risks']}
    Test Plan PDF: {transcript_results['pdf_path']}
    PDF size: {os.path.getsize(transcript_results['pdf_path']):,} bytes

  Output files in {output_dir}/:
""")
    for f in sorted(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, f)
        if os.path.isfile(fpath):
            print(f"    {f} ({os.path.getsize(fpath):,} bytes)")

    print("\n" + "=" * 70)
    print("  Done. All workflow artifacts generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
