"""
Generates a structured Performance Test Plan PDF from:
1. Jira PET ticket data
2. HLD document content
3. Teams meeting transcript (NFR answers)

Uses reportlab for PDF generation.
"""

import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


class TestPlanGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="CoverTitle",
            parent=self.styles["Title"],
            fontSize=28,
            spaceAfter=12,
            textColor=colors.HexColor("#1a237e"),
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name="CoverSubtitle",
            parent=self.styles["Normal"],
            fontSize=16,
            spaceAfter=6,
            textColor=colors.HexColor("#37474f"),
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading1"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#1a237e"),
            borderWidth=1,
            borderColor=colors.HexColor("#1a237e"),
            borderPadding=4
        ))
        self.styles.add(ParagraphStyle(
            name="SubSection",
            parent=self.styles["Heading2"],
            fontSize=13,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#283593")
        ))
        self.styles.add(ParagraphStyle(
            name="BodyText2",
            parent=self.styles["Normal"],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name="TableCell",
            parent=self.styles["Normal"],
            fontSize=9,
            alignment=TA_LEFT
        ))

    def generate(self, project_name, output_path, hld_summary=None,
                 nfr_data=None, estimation_data=None, pet_ticket=None):

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=20*mm
        )

        story = []

        story.extend(self._cover_page(project_name, pet_ticket))
        story.append(PageBreak())

        story.extend(self._document_control())
        story.append(PageBreak())

        story.extend(self._table_of_contents())
        story.append(PageBreak())

        story.extend(self._section_introduction(project_name, hld_summary))
        story.extend(self._section_scope(hld_summary, nfr_data))
        story.extend(self._section_test_environment(nfr_data))
        story.extend(self._section_workload_model(nfr_data))
        story.extend(self._section_test_scenarios(nfr_data, hld_summary))
        story.extend(self._section_test_data(nfr_data))
        story.extend(self._section_performance_targets(nfr_data))
        story.extend(self._section_test_schedule(estimation_data))
        story.extend(self._section_entry_exit_criteria(nfr_data))
        story.extend(self._section_risks_and_mitigations(nfr_data))
        story.extend(self._section_tools_and_monitoring(nfr_data))
        story.extend(self._section_deliverables())
        story.extend(self._section_appendix_nfr(nfr_data))

        doc.build(story)
        return output_path

    def _cover_page(self, project_name, pet_ticket):
        elements = []
        elements.append(Spacer(1, 80*mm))
        elements.append(Paragraph("Performance Test Plan", self.styles["CoverTitle"]))
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(project_name, self.styles["CoverSubtitle"]))
        elements.append(Spacer(1, 15*mm))

        ticket_id = pet_ticket.get("ticket_id", "PET-XXX") if pet_ticket else "PET-XXX"
        cover_data = [
            ["Document ID", f"PTP-{project_name.replace(' ', '-').upper()[:20]}"],
            ["PET Ticket", ticket_id],
            ["Version", "1.0"],
            ["Date", str(date.today())],
            ["Status", "Draft"],
            ["Classification", "Internal"]
        ]
        cover_table = Table(cover_data, colWidths=[50*mm, 80*mm])
        cover_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#90a4ae")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eceff1")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(cover_table)
        return elements

    def _document_control(self):
        elements = []
        elements.append(Paragraph("Document Control", self.styles["SectionHeader"]))

        elements.append(Paragraph("Revision History", self.styles["SubSection"]))
        rev_data = [
            ["Version", "Date", "Author", "Changes"],
            ["0.1", str(date.today()), "Performance Team", "Initial draft from NFR discovery meeting"],
            ["1.0", str(date.today()), "Performance Team", "Baseline approved"]
        ]
        rev_table = Table(rev_data, colWidths=[20*mm, 30*mm, 45*mm, 65*mm])
        rev_table.setStyle(self._header_table_style())
        elements.append(rev_table)
        elements.append(Spacer(1, 10*mm))

        elements.append(Paragraph("Approvals", self.styles["SubSection"]))
        app_data = [
            ["Role", "Name", "Signature", "Date"],
            ["Performance Lead", "", "", ""],
            ["Project Manager", "", "", ""],
            ["Technical Lead", "", "", ""]
        ]
        app_table = Table(app_data, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
        app_table.setStyle(self._header_table_style())
        elements.append(app_table)
        return elements

    def _table_of_contents(self):
        elements = []
        elements.append(Paragraph("Table of Contents", self.styles["SectionHeader"]))
        toc_items = [
            "1. Introduction",
            "2. Scope",
            "3. Test Environment",
            "4. Workload Model",
            "5. Test Scenarios",
            "6. Test Data",
            "7. Performance Targets & SLAs",
            "8. Test Schedule & Effort",
            "9. Entry & Exit Criteria",
            "10. Risks & Mitigations",
            "11. Tools & Monitoring",
            "12. Deliverables",
            "Appendix A: NFR Discovery Answers"
        ]
        for item in toc_items:
            elements.append(Paragraph(item, self.styles["BodyText2"]))
        return elements

    def _section_introduction(self, project_name, hld_summary):
        elements = []
        elements.append(Paragraph("1. Introduction", self.styles["SectionHeader"]))

        elements.append(Paragraph("1.1 Purpose", self.styles["SubSection"]))
        elements.append(Paragraph(
            f"This document defines the performance test strategy, approach, and execution plan "
            f"for the <b>{project_name}</b> project. It establishes the scope of performance testing, "
            f"workload models, acceptance criteria, environment requirements, and deliverables.",
            self.styles["BodyText2"]
        ))

        elements.append(Paragraph("1.2 Background", self.styles["SubSection"]))
        if hld_summary:
            bg = hld_summary.get("description", "Refer to the attached HLD for project background.")
        else:
            bg = "Refer to the attached High-Level Design (HLD) document for project background and architecture."
        elements.append(Paragraph(bg, self.styles["BodyText2"]))

        elements.append(Paragraph("1.3 References", self.styles["SubSection"]))
        ref_data = [
            ["Document", "Location"],
            ["High-Level Design (HLD)", "Attached to PET Jira ticket"],
            ["NFR Discovery Meeting Transcript", "Teams meeting recording/transcript"],
            ["Performance Estimation (PET)", "Jira PET ticket"],
            ["Non-Functional Requirements", "Captured during NFR discovery session"]
        ]
        ref_table = Table(ref_data, colWidths=[70*mm, 90*mm])
        ref_table.setStyle(self._header_table_style())
        elements.append(ref_table)
        return elements

    def _section_scope(self, hld_summary, nfr_data):
        elements = []
        elements.append(Paragraph("2. Scope", self.styles["SectionHeader"]))

        elements.append(Paragraph("2.1 In-Scope", self.styles["SubSection"]))
        in_scope = [
            "Peak load testing against defined concurrent user targets",
            "Stress testing to identify system breaking points",
            "Endurance/soak testing for memory leaks and resource degradation",
            "Batch job performance validation against SLA targets",
            "API response time validation for critical transactions",
            "Database query performance under load",
            "Middleware/message queue throughput validation"
        ]
        if hld_summary and hld_summary.get("in_scope"):
            in_scope = hld_summary["in_scope"] + in_scope
        for item in in_scope:
            elements.append(Paragraph(f"• {item}", self.styles["BodyText2"]))

        elements.append(Paragraph("2.2 Out of Scope", self.styles["SubSection"]))
        out_scope = [
            "Security/penetration testing (covered by security team)",
            "Functional testing (covered by QA team)",
            "UI/UX performance (frontend not in scope for backend services)",
            "Disaster recovery testing",
            "Third-party service performance (will be stubbed/mocked)"
        ]
        for item in out_scope:
            elements.append(Paragraph(f"• {item}", self.styles["BodyText2"]))

        elements.append(Paragraph("2.3 Test Types", self.styles["SubSection"]))
        test_types = [
            ["Test Type", "Description", "Duration"],
            ["Baseline", "Single user to establish baseline response times", "1-2 hours"],
            ["Load Test", "Normal expected load to validate SLAs", "1-2 hours steady state"],
            ["Peak Load", "Maximum expected concurrent users", "1 hour at peak"],
            ["Stress Test", "Beyond peak to find breaking point", "Incremental ramp"],
            ["Endurance", "Sustained load over extended period", "8-12 hours"],
            ["Batch Test", "Batch processing jobs under load", "Per batch SLA"],
            ["Spike Test", "Sudden traffic surge simulation", "15-30 min bursts"]
        ]
        tt_table = Table(test_types, colWidths=[35*mm, 80*mm, 45*mm])
        tt_table.setStyle(self._header_table_style())
        elements.append(tt_table)
        return elements

    def _section_test_environment(self, nfr_data):
        elements = []
        elements.append(Paragraph("3. Test Environment", self.styles["SectionHeader"]))

        elements.append(Paragraph("3.1 Environment Requirements", self.styles["SubSection"]))
        elements.append(Paragraph(
            "The performance test environment should mirror production configuration as closely as possible. "
            "Key requirements:",
            self.styles["BodyText2"]
        ))
        env_reqs = [
            "Production-equivalent hardware sizing (CPU, memory, storage)",
            "Same application version and configuration as target release",
            "Dedicated environment - not shared with other testing activities during execution",
            "Network configuration matching production topology",
            "Database populated with production-representative data volumes"
        ]
        for req in env_reqs:
            elements.append(Paragraph(f"• {req}", self.styles["BodyText2"]))

        elements.append(Paragraph("3.2 Environment Topology", self.styles["SubSection"]))
        if nfr_data:
            techs = nfr_data.get("technologies_mentioned", [])
            if techs:
                elements.append(Paragraph(
                    f"Technologies identified from NFR discovery: {', '.join(techs)}",
                    self.styles["BodyText2"]
                ))

        env_data = [
            ["Component", "Specification", "Quantity", "Notes"],
            ["Application Server", "[To be confirmed]", "[TBC]", "Match production sizing"],
            ["Database Server", "[To be confirmed]", "[TBC]", "Production data volume"],
            ["Load Balancer", "[To be confirmed]", "1", "Production-equivalent rules"],
            ["Message Queue", "[To be confirmed]", "[TBC]", "Match cluster config"],
            ["Load Generator", "[To be sized]", "[TBC]", "Sufficient for target load"]
        ]
        env_table = Table(env_data, colWidths=[35*mm, 45*mm, 25*mm, 55*mm])
        env_table.setStyle(self._header_table_style())
        elements.append(env_table)
        return elements

    def _section_workload_model(self, nfr_data):
        elements = []
        elements.append(Paragraph("4. Workload Model", self.styles["SectionHeader"]))

        elements.append(Paragraph("4.1 User Distribution", self.styles["SubSection"]))

        nv = nfr_data.get("numeric_values", {}) if nfr_data else {}
        normal_users = nv.get("concurrent_users", "[TBC]")
        peak_users = nv.get("peak_users", "[TBC]")
        tps = nv.get("tps", "[TBC]")

        wl_data = [
            ["Parameter", "Normal Load", "Peak Load", "Stress"],
            ["Concurrent Users", str(normal_users), str(peak_users), f"{peak_users}x1.5" if peak_users != "[TBC]" else "[TBC]"],
            ["Target TPS", str(tps), f"{tps}x1.5" if tps != "[TBC]" else "[TBC]", f"{tps}x2" if tps != "[TBC]" else "[TBC]"],
            ["Ramp-up Period", "15 minutes", "15 minutes", "5 minutes"],
            ["Steady State", "60 minutes", "60 minutes", "Until failure"],
            ["Ramp-down", "5 minutes", "5 minutes", "Immediate"]
        ]
        wl_table = Table(wl_data, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
        wl_table.setStyle(self._header_table_style())
        elements.append(wl_table)

        elements.append(Paragraph("4.2 Transaction Mix", self.styles["SubSection"]))
        elements.append(Paragraph(
            "The transaction mix should reflect production usage patterns. "
            "Percentages to be finalized based on production analytics:",
            self.styles["BodyText2"]
        ))
        mix_data = [
            ["Transaction", "Type", "Weight %", "Think Time (s)"],
            ["Account Lookup", "Read", "30%", "5-10"],
            ["Billing Inquiry", "Read", "20%", "8-15"],
            ["Payment Processing", "Write", "15%", "3-5"],
            ["Order Submission", "Write", "10%", "10-20"],
            ["Account Update", "Write", "10%", "5-10"],
            ["Report Generation", "Read", "10%", "15-30"],
            ["Authentication", "Write", "5%", "2-3"]
        ]
        mix_table = Table(mix_data, colWidths=[45*mm, 20*mm, 25*mm, 30*mm])
        mix_table.setStyle(self._header_table_style())
        elements.append(mix_table)
        return elements

    def _section_test_scenarios(self, nfr_data, hld_summary):
        elements = []
        elements.append(Paragraph("5. Test Scenarios", self.styles["SectionHeader"]))

        scenarios = [
            {
                "id": "TS-001", "name": "Baseline - Single User",
                "objective": "Establish baseline response times with single user",
                "type": "Baseline", "users": "1", "duration": "30 min per transaction"
            },
            {
                "id": "TS-002", "name": "Load Test - Normal",
                "objective": "Validate SLAs under expected normal load",
                "type": "Load", "users": "Normal concurrent users", "duration": "1 hour steady state"
            },
            {
                "id": "TS-003", "name": "Peak Load Test",
                "objective": "Validate system handles peak expected traffic",
                "type": "Peak", "users": "Peak concurrent users", "duration": "1 hour at peak"
            },
            {
                "id": "TS-004", "name": "Stress Test - Beyond Peak",
                "objective": "Identify system breaking point and failure behavior",
                "type": "Stress", "users": "Incremental beyond peak", "duration": "Until degradation"
            },
            {
                "id": "TS-005", "name": "Endurance Test",
                "objective": "Detect memory leaks, connection pool exhaustion, resource degradation",
                "type": "Endurance", "users": "70% of peak", "duration": "8-12 hours"
            },
            {
                "id": "TS-006", "name": "Batch Processing",
                "objective": "Validate batch job SLAs under concurrent online load",
                "type": "Batch", "users": "Batch + background online load", "duration": "Per batch SLA"
            },
            {
                "id": "TS-007", "name": "Spike Test",
                "objective": "Validate auto-scaling and recovery from sudden traffic surge",
                "type": "Spike", "users": "3x normal, sudden ramp", "duration": "15 min bursts"
            }
        ]

        for s in scenarios:
            sc_data = [
                ["Scenario ID", s["id"]],
                ["Name", s["name"]],
                ["Objective", s["objective"]],
                ["Test Type", s["type"]],
                ["Virtual Users", s["users"]],
                ["Duration", s["duration"]]
            ]
            sc_table = Table(sc_data, colWidths=[35*mm, 125*mm])
            sc_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdbdbd")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(KeepTogether([sc_table, Spacer(1, 5*mm)]))
        return elements

    def _section_test_data(self, nfr_data):
        elements = []
        elements.append(Paragraph("6. Test Data", self.styles["SectionHeader"]))

        elements.append(Paragraph("6.1 Data Requirements", self.styles["SubSection"]))
        data_reqs = [
            ["Data Category", "Volume", "Source", "Preparation Method"],
            ["User Accounts", "Production-equivalent", "Synthetic generation", "Data gen scripts"],
            ["Transaction History", "6-12 months equivalent", "Masked production data", "ETL pipeline"],
            ["Product/Service Catalog", "Full catalog", "Production copy", "DB restore"],
            ["Configuration Data", "Production-equivalent", "Config management", "Environment setup"],
            ["Test Credentials", "Per virtual user count", "Generated", "Credential store"]
        ]
        data_table = Table(data_reqs, colWidths=[35*mm, 40*mm, 40*mm, 45*mm])
        data_table.setStyle(self._header_table_style())
        elements.append(data_table)

        elements.append(Paragraph("6.2 Data Refresh Strategy", self.styles["SubSection"]))
        elements.append(Paragraph(
            "Test data must be refreshed before each major test execution cycle to ensure "
            "consistent and repeatable results. Database snapshots should be taken before "
            "test execution and restored between test runs that modify data.",
            self.styles["BodyText2"]
        ))
        return elements

    def _section_performance_targets(self, nfr_data):
        elements = []
        elements.append(Paragraph("7. Performance Targets & SLAs", self.styles["SectionHeader"]))

        nv = nfr_data.get("numeric_values", {}) if nfr_data else {}
        resp_time = nv.get("response_time", "2")
        avail = nv.get("availability", "99.9")
        err_rate = nv.get("error_rate", "1")
        cpu = nv.get("cpu_threshold", "70")
        memory = nv.get("memory_threshold", "80")

        elements.append(Paragraph("7.1 Response Time Targets", self.styles["SubSection"]))
        rt_data = [
            ["Transaction Category", "Target (p90)", "Target (p95)", "Target (p99)", "Max"],
            ["API Calls - Read", f"< {resp_time}s", f"< {float(resp_time)*1.5:.1f}s", f"< {float(resp_time)*2:.1f}s", f"< {float(resp_time)*3:.1f}s"],
            ["API Calls - Write", f"< {float(resp_time)*1.5:.1f}s", f"< {float(resp_time)*2:.1f}s", f"< {float(resp_time)*3:.1f}s", f"< {float(resp_time)*5:.1f}s"],
            ["Batch Jobs", "Per SLA", "Per SLA", "Per SLA", "SLA + 10%"],
            ["Authentication", "< 1s", "< 1.5s", "< 2s", "< 3s"],
            ["Reports", "< 5s", "< 8s", "< 10s", "< 15s"]
        ]
        rt_table = Table(rt_data, colWidths=[40*mm, 30*mm, 30*mm, 30*mm, 30*mm])
        rt_table.setStyle(self._header_table_style())
        elements.append(rt_table)

        elements.append(Paragraph("7.2 Server Resource Thresholds", self.styles["SubSection"]))
        res_data = [
            ["Metric", "Warning", "Critical", "Action"],
            ["CPU Utilization", f"< {cpu}%", f"> {cpu}%", "Investigate and optimize"],
            ["Memory Utilization", f"< {memory}%", f"> {memory}%", "Check for memory leaks"],
            ["Disk I/O Wait", "< 10%", "> 20%", "Review query plans, indexing"],
            ["Network Utilization", "< 60%", "> 80%", "Review payload sizes"],
            ["Connection Pool", "< 80%", "> 90%", "Tune pool configuration"],
            ["Thread Pool", "< 75%", "> 90%", "Review thread usage patterns"],
            ["GC Pause Time", "< 200ms", "> 500ms", "Tune JVM/runtime parameters"]
        ]
        res_table = Table(res_data, colWidths=[40*mm, 30*mm, 30*mm, 60*mm])
        res_table.setStyle(self._header_table_style())
        elements.append(res_table)

        elements.append(Paragraph("7.3 Availability & Error Targets", self.styles["SubSection"]))
        avail_data = [
            ["Metric", "Target"],
            ["Availability", f"{avail}%"],
            ["Error Rate (under normal load)", f"< {err_rate}%"],
            ["Error Rate (under peak load)", f"< {float(err_rate)*2:.1f}%"],
            ["Zero Data Loss", "100% transaction integrity"],
            ["Recovery Time (after failure)", "< 30 seconds"]
        ]
        avail_table = Table(avail_data, colWidths=[60*mm, 60*mm])
        avail_table.setStyle(self._header_table_style())
        elements.append(avail_table)
        return elements

    def _section_test_schedule(self, estimation_data):
        elements = []
        elements.append(Paragraph("8. Test Schedule & Effort", self.styles["SectionHeader"]))

        if estimation_data:
            total_pd = estimation_data.get("total_pd_after_efficiency", "[TBC]")
            elements.append(Paragraph(
                f"Estimated total effort: <b>{total_pd} person-days</b> (from PET estimation, after 19% efficiency).",
                self.styles["BodyText2"]
            ))

        schedule_data = [
            ["Phase", "Activities", "Duration", "Dependencies"],
            ["Planning & Setup", "Environment setup, tool installation, script framework", "Week 1", "Environment provisioned"],
            ["Script Development", "Script design, development, parameterization", "Week 2-3", "Test data available"],
            ["Dry Run", "Baseline tests, script validation, environment shakeout", "Week 3", "Scripts reviewed"],
            ["Test Execution Cycle 1", "Load, peak load, stress tests", "Week 4", "Dry run passed"],
            ["Defect Fix & Retest", "Fix analysis, optimization, re-execution", "Week 5", "Defects assigned"],
            ["Test Execution Cycle 2", "Regression, endurance, batch tests", "Week 5-6", "Fixes deployed"],
            ["Reporting & Closure", "Analysis, report generation, sign-off", "Week 6", "All tests executed"]
        ]
        sch_table = Table(schedule_data, colWidths=[35*mm, 55*mm, 25*mm, 45*mm])
        sch_table.setStyle(self._header_table_style())
        elements.append(sch_table)
        return elements

    def _section_entry_exit_criteria(self, nfr_data):
        elements = []
        elements.append(Paragraph("9. Entry & Exit Criteria", self.styles["SectionHeader"]))

        elements.append(Paragraph("9.1 Entry Criteria", self.styles["SubSection"]))
        entry = [
            "Performance test environment provisioned and accessible",
            "Application build deployed and smoke tested",
            "Test data loaded and validated",
            "Performance test scripts developed, reviewed, and dry-run validated",
            "Monitoring agents installed and configured on all servers",
            "Baseline test completed successfully",
            "All external integrations stubbed or available",
            "Test plan reviewed and approved by stakeholders"
        ]
        for item in entry:
            elements.append(Paragraph(f"• {item}", self.styles["BodyText2"]))

        elements.append(Paragraph("9.2 Exit Criteria", self.styles["SubSection"]))
        exit_c = [
            "All planned test scenarios executed at least once",
            "Response time targets met for all critical transactions at p90",
            "Error rate below threshold under normal and peak load",
            "No critical or high-severity performance defects open",
            "Endurance test completed without memory leaks or resource degradation",
            "Batch processing completed within SLA window",
            "Server resource utilization within defined thresholds",
            "Performance test report reviewed and accepted"
        ]
        for item in exit_c:
            elements.append(Paragraph(f"• {item}", self.styles["BodyText2"]))

        elements.append(Paragraph("9.3 Suspension Criteria", self.styles["SubSection"]))
        suspend = [
            "Application crash or environment instability preventing test execution",
            "Error rate exceeding 10% (indicates functional issues, not performance)",
            "Test data corruption requiring full refresh",
            "Environment taken for emergency production support"
        ]
        for item in suspend:
            elements.append(Paragraph(f"• {item}", self.styles["BodyText2"]))
        return elements

    def _section_risks_and_mitigations(self, nfr_data):
        elements = []
        elements.append(Paragraph("10. Risks & Mitigations", self.styles["SectionHeader"]))

        risks = [
            ["Risk", "Impact", "Probability", "Mitigation"],
            ["Environment not production-equivalent", "High", "Medium",
             "Validate sizing before test cycle; document deviations"],
            ["Test data insufficient or stale", "High", "Medium",
             "Data preparation starts in parallel with scripting; validate counts"],
            ["Shared environment interference", "Medium", "High",
             "Dedicated test windows; coordinate with other teams"],
            ["Third-party service unavailable for testing", "Medium", "Medium",
             "Build service virtualization/stubs for external dependencies"],
            ["Late code changes invalidating test results", "High", "Medium",
             "Code freeze during test execution; retest impacted flows"],
            ["Insufficient load generator capacity", "Medium", "Low",
             "Size load generators based on peak scenario; scale horizontally"],
            ["Monitoring gaps - missing metrics", "Medium", "Medium",
             "Validate monitoring setup during dry run; add custom metrics"]
        ]

        if nfr_data and nfr_data.get("risks"):
            for risk in nfr_data["risks"][:5]:
                risks.append([
                    risk["text"][:60], "Medium", "Medium",
                    "Identified during NFR discovery - investigate and mitigate"
                ])

        risk_table = Table(risks, colWidths=[45*mm, 20*mm, 20*mm, 75*mm])
        risk_table.setStyle(self._header_table_style())
        elements.append(risk_table)
        return elements

    def _section_tools_and_monitoring(self, nfr_data):
        elements = []
        elements.append(Paragraph("11. Tools & Monitoring", self.styles["SectionHeader"]))

        elements.append(Paragraph("11.1 Performance Testing Tools", self.styles["SubSection"]))
        tools_data = [
            ["Tool", "Purpose", "Notes"],
            ["JMeter / Gatling / k6", "Load generation and script execution", "Select based on team expertise"],
            ["Jenkins / Azure DevOps", "Test execution orchestration", "CI/CD integration"],
            ["Git", "Script version control", "Branch per test cycle"]
        ]
        tools_table = Table(tools_data, colWidths=[45*mm, 55*mm, 60*mm])
        tools_table.setStyle(self._header_table_style())
        elements.append(tools_table)

        elements.append(Paragraph("11.2 Monitoring Stack", self.styles["SubSection"]))

        techs = nfr_data.get("technologies_mentioned", []) if nfr_data else []
        monitoring_tools = [
            ["Layer", "Tool", "Metrics"],
            ["APM", "Dynatrace / AppDynamics / New Relic", "Transaction traces, service maps, code-level"],
            ["Infrastructure", "Grafana + Prometheus / Datadog", "CPU, memory, disk, network"],
            ["Database", "Native DB monitoring / Slow query logs", "Query times, locks, connections, I/O"],
            ["Logs", "Splunk / ELK Stack", "Error patterns, correlation IDs"],
            ["Network", "Wireshark / tcpdump (if needed)", "Latency, packet loss, DNS"]
        ]

        mon_table = Table(monitoring_tools, colWidths=[30*mm, 60*mm, 70*mm])
        mon_table.setStyle(self._header_table_style())
        elements.append(mon_table)

        if techs:
            elements.append(Paragraph(
                f"Note: Technologies identified in NFR discovery ({', '.join(techs)}) should inform "
                f"the final tool selection. Use native monitoring for identified platforms where available.",
                self.styles["BodyText2"]
            ))
        return elements

    def _section_deliverables(self):
        elements = []
        elements.append(Paragraph("12. Deliverables", self.styles["SectionHeader"]))

        deliverables = [
            ["Deliverable", "Format", "Timing"],
            ["Performance Test Plan", "PDF", "Before test execution"],
            ["Test Scripts (version controlled)", "Git repository", "Before dry run"],
            ["Dry Run Results", "Summary report", "After dry run"],
            ["Test Execution Results - Per Cycle", "Detailed report with graphs", "After each cycle"],
            ["Defect Reports", "Jira tickets", "During execution"],
            ["Final Performance Test Report", "PDF with executive summary", "After all cycles"],
            ["Recommendations & Tuning Guide", "Document", "With final report"],
            ["Raw Test Data & Logs", "Archive", "With final report"]
        ]
        del_table = Table(deliverables, colWidths=[55*mm, 45*mm, 60*mm])
        del_table.setStyle(self._header_table_style())
        elements.append(del_table)
        return elements

    def _section_appendix_nfr(self, nfr_data):
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("Appendix A: NFR Discovery Answers", self.styles["SectionHeader"]))

        if not nfr_data:
            elements.append(Paragraph(
                "NFR discovery meeting data not yet available. This appendix will be populated "
                "after the Teams meeting with the project team.",
                self.styles["BodyText2"]
            ))
            return elements

        nv = nfr_data.get("numeric_values", {})
        if nv:
            elements.append(Paragraph("Numeric Values Captured", self.styles["SubSection"]))
            for key, value in nv.items():
                label = key.replace("_", " ").title()
                elements.append(Paragraph(f"• {label}: {value}", self.styles["BodyText2"]))

        open_items = nfr_data.get("open_items", [])
        if open_items:
            elements.append(Paragraph(f"Open Items ({len(open_items)})", self.styles["SubSection"]))
            for item in open_items:
                elements.append(Paragraph(
                    f"• [{item.get('speaker', 'Unknown')}] {item.get('text', '')[:200]}",
                    self.styles["BodyText2"]
                ))

        risks = nfr_data.get("risks", [])
        if risks:
            elements.append(Paragraph(f"Risks Identified ({len(risks)})", self.styles["SubSection"]))
            for risk in risks:
                elements.append(Paragraph(
                    f"• [{risk.get('speaker', 'Unknown')}] {risk.get('text', '')[:200]}",
                    self.styles["BodyText2"]
                ))

        return elements

    def _header_table_style(self):
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdbdbd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
