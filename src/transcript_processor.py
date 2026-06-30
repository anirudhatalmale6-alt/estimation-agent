"""
Processes Microsoft Teams meeting transcripts to extract NFR answers,
HLD walkthrough notes, and action items for performance test planning.

Supports .vtt (WebVTT) and .docx (Word) transcript formats from Teams.
"""

import re
import json
import yaml
import os


class TranscriptProcessor:
    def __init__(self, questionnaire_path=None):
        if questionnaire_path is None:
            questionnaire_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config", "nfr_questionnaire.yaml"
            )
        with open(questionnaire_path) as f:
            self.questionnaire = yaml.safe_load(f)

        self.sections = {s["id"]: s for s in self.questionnaire["nfr_questionnaire"]["sections"]}

    def parse_vtt(self, vtt_content):
        entries = []
        blocks = re.split(r"\n\n+", vtt_content.strip())
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue
            timestamp_line = None
            speaker = None
            text_lines = []
            for line in lines:
                if "-->" in line:
                    timestamp_line = line.strip()
                elif line.startswith("<v "):
                    match = re.match(r"<v ([^>]+)>(.*)", line)
                    if match:
                        speaker = match.group(1).strip()
                        text_lines.append(match.group(2).strip())
                elif timestamp_line:
                    text_lines.append(line.strip())

            if timestamp_line and text_lines:
                start_time = timestamp_line.split("-->")[0].strip()
                entries.append({
                    "timestamp": start_time,
                    "speaker": speaker or "Unknown",
                    "text": " ".join(text_lines)
                })
        return entries

    def parse_docx_transcript(self, text_content):
        entries = []
        lines = text_content.strip().split("\n")
        current_speaker = "Unknown"
        current_text = []
        current_time = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            speaker_match = re.match(
                r"^(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\s*[-–]\s*(.+?)$", line
            )
            if speaker_match:
                if current_text:
                    entries.append({
                        "timestamp": current_time,
                        "speaker": current_speaker,
                        "text": " ".join(current_text)
                    })
                current_time = speaker_match.group(1)
                current_speaker = speaker_match.group(2).strip()
                current_text = []
            else:
                speaker_match2 = re.match(r"^(.+?)\s+(\d{1,2}:\d{2})", line)
                if speaker_match2 and len(speaker_match2.group(1).split()) <= 4:
                    if current_text:
                        entries.append({
                            "timestamp": current_time,
                            "speaker": current_speaker,
                            "text": " ".join(current_text)
                        })
                    current_speaker = speaker_match2.group(1).strip()
                    current_time = speaker_match2.group(2)
                    current_text = []
                else:
                    current_text.append(line)

        if current_text:
            entries.append({
                "timestamp": current_time,
                "speaker": current_speaker,
                "text": " ".join(current_text)
            })
        return entries

    def extract_nfr_data(self, transcript_entries):
        full_text = "\n".join(
            f"[{e['speaker']}]: {e['text']}" for e in transcript_entries
        )

        extracted = {
            "project_overview": {},
            "architecture": {},
            "workload_profile": {},
            "performance_targets": {},
            "billing_specific": {},
            "data_and_security": {},
            "constraints": {},
            "open_items": [],
            "risks": [],
            "action_items": []
        }

        numeric_patterns = {
            "concurrent_users": r"(\d[\d,]*)\s*(?:concurrent|simultaneous)\s*users?",
            "peak_users": r"peak\s*(?:of\s*)?(\d[\d,]*)\s*users?",
            "tps": r"(\d[\d,]*)\s*(?:TPS|transactions?\s*per\s*second)",
            "response_time": r"(\d+(?:\.\d+)?)\s*(?:seconds?|ms|milliseconds?)\s*(?:response|latency)",
            "availability": r"(\d{2,3}(?:\.\d+)?)\s*%?\s*(?:availability|uptime|SLA)",
            "error_rate": r"(?:error\s*rate|errors?)\s*(?:of\s*)?(?:less\s*than\s*|<\s*)?(\d+(?:\.\d+)?)\s*%",
            "cpu_threshold": r"CPU\s*(?:less\s*than\s*|<\s*|under\s*)?(\d+)\s*%",
            "memory_threshold": r"(?:memory|RAM)\s*(?:less\s*than\s*|<\s*|under\s*)?(\d+)\s*%",
            "batch_volume": r"(\d[\d,]*)\s*(?:records?|accounts?|transactions?)\s*(?:per\s*)?(?:batch|cycle|run)",
        }

        extracted["numeric_values"] = {}
        for key, pattern in numeric_patterns.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                extracted["numeric_values"][key] = matches[0].replace(",", "")

        tbd_patterns = [
            r"(?:we\s+)?(?:need\s+to|have\s+to|should|will)\s+(?:check|confirm|verify|get\s+back|follow\s+up)",
            r"(?:TBD|to\s+be\s+(?:determined|confirmed|decided))",
            r"(?:not\s+sure|don't\s+know|uncertain|unclear)",
            r"(?:let\s+me|I'll)\s+(?:check|find\s+out|get\s+back)"
        ]
        for entry in transcript_entries:
            for pattern in tbd_patterns:
                if re.search(pattern, entry["text"], re.IGNORECASE):
                    extracted["open_items"].append({
                        "speaker": entry["speaker"],
                        "text": entry["text"],
                        "timestamp": entry["timestamp"]
                    })
                    break

        risk_patterns = [
            r"(?:risk|concern|worry|issue|problem|bottleneck|limitation|constraint)",
            r"(?:might\s+(?:fail|break|not\s+work))",
            r"(?:previous(?:ly)?\s+(?:failed|had\s+issues|caused\s+problems))"
        ]
        for entry in transcript_entries:
            for pattern in risk_patterns:
                if re.search(pattern, entry["text"], re.IGNORECASE):
                    extracted["risks"].append({
                        "speaker": entry["speaker"],
                        "text": entry["text"],
                        "timestamp": entry["timestamp"]
                    })
                    break

        tech_patterns = [
            r"\b(Java|Python|\.NET|Node\.js|Go|Rust|C\+\+|C#)\b",
            r"\b(Oracle|PostgreSQL|MySQL|SQL\s*Server|MongoDB|Redis|Cassandra|DynamoDB)\b",
            r"\b(Kafka|RabbitMQ|ActiveMQ|IBM\s*MQ|SQS|EventBridge)\b",
            r"\b(Kubernetes|Docker|OpenShift|ECS|EKS|AKS)\b",
            r"\b(Jenkins|GitLab|Azure\s*DevOps|GitHub\s*Actions)\b",
            r"\b(Splunk|Dynatrace|AppDynamics|New\s*Relic|Datadog|Grafana|Prometheus)\b",
            r"\b(JMeter|Gatling|LoadRunner|k6|Locust|NeoLoad)\b",
            r"\b(AWS|Azure|GCP|on-prem|on-premise)\b"
        ]
        technologies = set()
        for entry in transcript_entries:
            for pattern in tech_patterns:
                matches = re.findall(pattern, entry["text"], re.IGNORECASE)
                technologies.update(m.strip() for m in matches)
        extracted["technologies_mentioned"] = sorted(technologies)

        return extracted

    def generate_nfr_summary(self, extracted_data):
        summary = []
        summary.append("=" * 70)
        summary.append("  NFR DISCOVERY MEETING SUMMARY")
        summary.append("=" * 70)

        nv = extracted_data.get("numeric_values", {})
        if nv:
            summary.append("\n--- Performance Targets Captured ---")
            label_map = {
                "concurrent_users": "Concurrent Users (Normal)",
                "peak_users": "Peak Concurrent Users",
                "tps": "Target TPS",
                "response_time": "Response Time Target",
                "availability": "Availability SLA",
                "error_rate": "Max Error Rate",
                "cpu_threshold": "CPU Threshold",
                "memory_threshold": "Memory Threshold",
                "batch_volume": "Batch Volume"
            }
            for key, label in label_map.items():
                if key in nv:
                    summary.append(f"  {label}: {nv[key]}")

        techs = extracted_data.get("technologies_mentioned", [])
        if techs:
            summary.append(f"\n--- Technologies Identified ---")
            summary.append(f"  {', '.join(techs)}")

        open_items = extracted_data.get("open_items", [])
        if open_items:
            summary.append(f"\n--- Open Items ({len(open_items)}) ---")
            for i, item in enumerate(open_items, 1):
                summary.append(f"  {i}. [{item['speaker']}] {item['text'][:120]}")

        risks = extracted_data.get("risks", [])
        if risks:
            summary.append(f"\n--- Risks & Concerns ({len(risks)}) ---")
            for i, risk in enumerate(risks, 1):
                summary.append(f"  {i}. [{risk['speaker']}] {risk['text'][:120]}")

        summary.append("\n" + "=" * 70)
        return "\n".join(summary)

    def process_transcript(self, content, format="vtt"):
        if format == "vtt":
            entries = self.parse_vtt(content)
        else:
            entries = self.parse_docx_transcript(content)

        extracted = self.extract_nfr_data(entries)
        summary = self.generate_nfr_summary(extracted)

        return {
            "entries": entries,
            "extracted": extracted,
            "summary": summary,
            "entry_count": len(entries),
            "speakers": list(set(e["speaker"] for e in entries))
        }
