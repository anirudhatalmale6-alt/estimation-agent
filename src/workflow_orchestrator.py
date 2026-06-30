"""
Orchestrates the full PET estimation workflow:

1. Email trigger detects new PET ticket notification
2. Reads PET ticket and attached HLD from Jira (via MCP)
3. Runs PERF estimation (11 activities)
4. Posts estimation as Jira comment
5. Drafts NFR discovery meeting invite with the PM
6. (After meeting) Processes transcript and generates test plan PDF

This module connects all components into a single automated pipeline.
"""

import os
import json
from datetime import date


class WorkflowOrchestrator:
    def __init__(self, jira_client=None, email_trigger=None,
                 meeting_scheduler=None, transcript_processor=None,
                 test_plan_generator=None):
        self.jira = jira_client
        self.email_trigger = email_trigger
        self.meeting_scheduler = meeting_scheduler
        self.transcript_processor = transcript_processor
        self.test_plan_generator = test_plan_generator

    def process_new_pet_ticket(self, pet_ticket_id, perf_manager_email,
                                output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        results = {"pet_ticket_id": pet_ticket_id, "steps": []}

        # Step 1: Read PET ticket from Jira
        print(f"\n[Step 1] Reading PET ticket: {pet_ticket_id}")
        ticket_data = None
        if self.jira:
            ticket_data = self.jira.get_issue(pet_ticket_id)
            results["steps"].append({
                "step": "read_ticket",
                "status": "done",
                "ticket": pet_ticket_id
            })
        else:
            print("  Jira client not configured - using placeholder data")
            ticket_data = self._placeholder_ticket(pet_ticket_id)
            results["steps"].append({
                "step": "read_ticket",
                "status": "placeholder",
                "note": "Jira MCP not configured"
            })

        # Step 2: Extract HLD content
        print(f"[Step 2] Extracting HLD from ticket attachments")
        hld_summary = self._extract_hld(ticket_data)
        results["steps"].append({
            "step": "extract_hld",
            "status": "done",
            "in_scope_items": len(hld_summary.get("in_scope", []))
        })

        # Step 3: Run estimation
        print(f"[Step 3] Running PERF estimation")
        estimation = self._run_estimation(hld_summary)
        results["steps"].append({
            "step": "estimation",
            "status": "done",
            "total_pd": estimation["total_pd_after_efficiency"],
            "cost": estimation["total_cost"]
        })

        # Step 4: Post estimation to Jira
        print(f"[Step 4] Posting estimation to {pet_ticket_id}")
        estimation_text = self._format_estimation_report(
            pet_ticket_id, hld_summary, estimation
        )
        if self.jira:
            self.jira.add_comment(pet_ticket_id, estimation_text)
            results["steps"].append({"step": "post_to_jira", "status": "done"})
        else:
            report_path = os.path.join(output_dir, f"estimation_report_{pet_ticket_id}.txt")
            with open(report_path, "w") as f:
                f.write(estimation_text)
            results["steps"].append({
                "step": "post_to_jira",
                "status": "saved_locally",
                "path": report_path
            })

        # Step 5: Draft NFR discovery meeting
        print(f"[Step 5] Drafting NFR discovery meeting invite")
        pm_name = self._get_reporter_name(ticket_data)
        pm_email = self._get_reporter_email(ticket_data)
        project_name = self._get_project_name(ticket_data)

        if self.meeting_scheduler:
            meeting_files = self.meeting_scheduler.draft_and_save(
                project_name=project_name,
                pet_ticket_id=pet_ticket_id,
                pm_name=pm_name,
                pm_email=pm_email,
                perf_manager_email=perf_manager_email,
                estimation_summary=estimation_text,
                output_dir=output_dir
            )
            results["steps"].append({
                "step": "draft_meeting",
                "status": "done",
                "files": meeting_files
            })
        else:
            from .meeting_scheduler import MeetingScheduler
            scheduler = MeetingScheduler()
            meeting_files = scheduler.draft_and_save(
                project_name=project_name,
                pet_ticket_id=pet_ticket_id,
                pm_name=pm_name,
                pm_email=pm_email,
                perf_manager_email=perf_manager_email,
                estimation_summary=estimation_text,
                output_dir=output_dir
            )
            results["steps"].append({
                "step": "draft_meeting",
                "status": "done",
                "files": meeting_files
            })

        print(f"\n[Complete] PET ticket {pet_ticket_id} processed")
        print(f"  Estimation: {estimation['total_pd_after_efficiency']} PD")
        print(f"  Cost: ${estimation['total_cost']:,.2f}")
        print(f"  Meeting invite drafted for: {pm_name} ({pm_email})")

        results["summary"] = {
            "pet_ticket_id": pet_ticket_id,
            "project_name": project_name,
            "estimation_pd": estimation["total_pd_after_efficiency"],
            "estimation_cost": estimation["total_cost"],
            "pm_name": pm_name,
            "pm_email": pm_email,
            "meeting_drafted": True,
            "awaiting": "NFR discovery meeting transcript"
        }

        summary_path = os.path.join(output_dir, f"workflow_summary_{pet_ticket_id}.json")
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        return results

    def process_meeting_transcript(self, pet_ticket_id, transcript_content,
                                    transcript_format="vtt", output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)

        # Load previous workflow state
        summary_path = os.path.join(output_dir, f"workflow_summary_{pet_ticket_id}.json")
        prev_results = {}
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                prev_results = json.load(f)

        # Step 6: Process transcript
        print(f"\n[Step 6] Processing meeting transcript for {pet_ticket_id}")
        if self.transcript_processor is None:
            from .transcript_processor import TranscriptProcessor
            self.transcript_processor = TranscriptProcessor()

        result = self.transcript_processor.process_transcript(
            transcript_content, format=transcript_format
        )
        extracted = result["extracted"]
        print(result["summary"])

        # Step 7: Generate test plan PDF
        print(f"\n[Step 7] Generating Performance Test Plan PDF")
        if self.test_plan_generator is None:
            from .test_plan_generator import TestPlanGenerator
            self.test_plan_generator = TestPlanGenerator()

        project_name = prev_results.get("summary", {}).get("project_name", pet_ticket_id)
        estimation_data = None
        for step in prev_results.get("steps", []):
            if step.get("step") == "estimation":
                estimation_data = {
                    "total_pd_after_efficiency": step.get("total_pd"),
                    "total_cost": step.get("cost")
                }

        pdf_path = os.path.join(
            output_dir,
            f"Performance_Test_Plan_{pet_ticket_id}.pdf"
        )

        self.test_plan_generator.generate(
            project_name=project_name,
            output_path=pdf_path,
            hld_summary=prev_results.get("hld_summary"),
            nfr_data=extracted,
            estimation_data=estimation_data,
            pet_ticket={"ticket_id": pet_ticket_id}
        )

        print(f"  PDF generated: {pdf_path}")
        print(f"  Size: {os.path.getsize(pdf_path):,} bytes")

        # Step 8: Post test plan to Jira
        if self.jira:
            self.jira.add_comment(
                pet_ticket_id,
                f"Performance Test Plan generated. See attached PDF.\n\n"
                f"NFR Summary:\n{result['summary']}"
            )

        return {
            "pet_ticket_id": pet_ticket_id,
            "pdf_path": pdf_path,
            "transcript_entries": result["entry_count"],
            "speakers": result["speakers"],
            "numeric_values": extracted.get("numeric_values", {}),
            "technologies": extracted.get("technologies_mentioned", []),
            "open_items": len(extracted.get("open_items", [])),
            "risks": len(extracted.get("risks", []))
        }

    def _placeholder_ticket(self, pet_ticket_id):
        return {
            "key": pet_ticket_id,
            "fields": {
                "summary": f"Performance Estimation - {pet_ticket_id}",
                "reporter": {
                    "displayName": "Project Manager",
                    "emailAddress": "pm@company.com"
                },
                "project": {"name": "Performance Testing"},
                "description": "HLD document attached.",
                "attachment": []
            }
        }

    def _extract_hld(self, ticket_data):
        fields = ticket_data.get("fields", ticket_data)
        summary = fields.get("summary", "")
        description = fields.get("description", "")

        return {
            "description": description or summary,
            "in_scope": [],
            "project_name": summary
        }

    def _run_estimation(self, hld_summary):
        in_scope_count = len(hld_summary.get("in_scope", []))
        if in_scope_count <= 5:
            size = "small"
        elif in_scope_count <= 15:
            size = "medium"
        else:
            size = "large"

        from importlib import resources
        import yaml
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "estimation_rules.yaml"
        )
        with open(config_path) as f:
            rules = yaml.safe_load(f)

        activities = rules["perf_activities"]
        multipliers = rules["complexity_multipliers"]
        default_units = rules["default_units"][size]
        efficiency = rules["efficiency_percentage"]
        cost_per_pd = rules["cost_per_person_day"]
        minutes_per_day = rules["minutes_per_day"]

        total_minutes = 0
        breakdown = []
        for act in activities:
            act_id = act["id"]
            base_minutes = act["base_time_minutes"]
            complexity = act["default_complexity"]
            multiplier = multipliers.get(complexity, 1.0)
            units = default_units.get(act_id, 1)
            exec_time = base_minutes * multiplier
            total_time = exec_time * units
            total_minutes += total_time
            breakdown.append({
                "activity": act["name"],
                "complexity": complexity,
                "exec_time_days": round(exec_time / minutes_per_day, 2),
                "units": units,
                "total_days": round(total_time / minutes_per_day, 2)
            })

        total_pd = round(total_minutes / minutes_per_day, 2)
        efficiency_saving = round(total_pd * (efficiency / 100), 2)
        total_pd_after = round(total_pd - efficiency_saving, 2)
        total_cost = round(total_pd_after * cost_per_pd, 2)

        return {
            "project_size": size,
            "total_pd_before_efficiency": total_pd,
            "efficiency_percentage": efficiency,
            "efficiency_saving_pd": efficiency_saving,
            "total_pd_after_efficiency": total_pd_after,
            "cost_per_pd": cost_per_pd,
            "total_cost": total_cost,
            "breakdown": breakdown
        }

    def _format_estimation_report(self, pet_ticket_id, hld_summary, estimation):
        lines = []
        lines.append("=" * 70)
        lines.append(f"  PERF ESTIMATION REPORT - {pet_ticket_id}")
        lines.append("=" * 70)
        lines.append(f"  Project Size     : {estimation['project_size'].upper()}")
        lines.append(f"  Estimation Phase : +/- 10%")
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"  {'PERF Activity':<28} {'Complexity':<14} {'Time(days)':<12} {'Units':<8} {'Total(days)'}")
        lines.append("-" * 70)
        for act in estimation["breakdown"]:
            lines.append(
                f"  {act['activity']:<28} {act['complexity']:<14} "
                f"{act['exec_time_days']:<12} {act['units']:<8} {act['total_days']}"
            )
        lines.append("-" * 70)
        lines.append("")
        total_hrs = round(estimation["total_pd_before_efficiency"] * 8, 2)
        lines.append(f"  Vendor Effort GRAND TOTAL (Before Efficiency):")
        lines.append(f"    {total_hrs} hrs = {estimation['total_pd_before_efficiency']} PD")
        lines.append("")
        after_hrs = round(estimation["total_pd_after_efficiency"] * 8, 2)
        lines.append(f"  Vendor Effort GRAND TOTAL (After {estimation['efficiency_percentage']}% Efficiency):")
        lines.append(f"    {after_hrs} hrs = {estimation['total_pd_after_efficiency']} PD")
        lines.append("")
        lines.append(f"  Saving due to Efficiency:")
        lines.append(f"    {estimation['efficiency_saving_pd']} PD")
        lines.append("")
        lines.append(f"  Cost @ ${estimation['cost_per_pd']}/PD = ${estimation['total_cost']:,.2f}")
        lines.append("=" * 70)
        return "\n".join(lines)

    def _get_reporter_name(self, ticket_data):
        fields = ticket_data.get("fields", ticket_data)
        reporter = fields.get("reporter", {})
        return reporter.get("displayName", reporter.get("name", "Project Manager"))

    def _get_reporter_email(self, ticket_data):
        fields = ticket_data.get("fields", ticket_data)
        reporter = fields.get("reporter", {})
        return reporter.get("emailAddress", reporter.get("email", "pm@company.com"))

    def _get_project_name(self, ticket_data):
        fields = ticket_data.get("fields", ticket_data)
        return fields.get("summary", ticket_data.get("key", "Unknown Project"))
