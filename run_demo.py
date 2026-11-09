"""AMRA Live Interactive Demonstration Script.

Simulates a real-time researcher session against the running AMRA backend:
1. Probes the service health status.
2. Streams an academic paper and dataset discovery query.
3. Requests tabular dataset cleaning (triggers cryptographic HITL token gate).
4. Submits the approval token to execute data cleaning.
5. Displays the Data Health Score improvement and output Parquet/CSV artifacts.
"""

import urllib.request
import json
import time
import sys

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_banner("1. SERVICE HEALTH & PROVIDER STATUS")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/health") as resp:
            health = json.loads(resp.read().decode())
            print(f"Service:             {health.get('service')}")
            print(f"Version:             {health.get('version')}")
            print(f"Status:              {health.get('status')}")
            print(f"Configured Provider: {health.get('configured_provider')}")
            print(f"Gemini Key Present:  {health.get('has_gemini_key')}")
            print(f"Groq Key Present:    {health.get('has_groq_key')}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return

    print_banner("2. SSE REAL-TIME DISCOVERY STREAM (/api/chat/stream)")
    session_id = f"demo_{int(time.time())}"
    payload = {
        "message": "Find recent papers on graph neural networks for fraud detection and find a benchmark dataset",
        "session_id": session_id,
        "provider": "mock"
    }

    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                event = json.loads(line_str[6:])
                etype = event.get("type")
                if etype == "thought":
                    print(f" [THOUGHT]    {event.get('content')}")
                elif etype == "tool_start":
                    print(f" [TOOL START] Tool: {event.get('tool')} | Args: {event.get('args')}")
                elif etype == "tool_result":
                    res = event.get("result")
                    if isinstance(res, list):
                        print(f" [TOOL RESULT] Retrieved {len(res)} items:")
                        for r in res[:2]:
                            title = r.get("title") or r.get("dataset_id") or "Item"
                            url = r.get("pdf_url") or r.get("kaggle_url") or ""
                            print(f"    * {title}")
                            if url:
                                print(f"      Canonical URL: {url}")
                    else:
                        print(f" [TOOL RESULT] {res}")
                elif etype == "text_delta":
                    print(event.get("content"), end="", flush=True)
                elif etype == "cost_audit":
                    print(f"\n [COST AUDIT] Provider: {event.get('provider')}, Prompt Tokens: {event.get('prompt_tokens')}, Cost: ${event.get('cost_usd'):.4f} (Free Tier: {event.get('is_free_tier')})")
                elif etype == "complete":
                    print(f" [COMPLETE]   Session '{session_id}' turn successfully closed.")

    print_banner("3. HUMAN-IN-THE-LOOP (HITL) GATE INTERCEPTION")
    clean_payload = {
        "message": "Please download and clean the creditcardfraud dataset for baseline training",
        "session_id": session_id,
        "provider": "mock"
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/chat/stream",
        data=json.dumps(clean_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    approval_token = None
    with urllib.request.urlopen(req2) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                event = json.loads(line_str[6:])
                etype = event.get("type")
                if etype == "thought":
                    print(f" [THOUGHT]    {event.get('content')}")
                elif etype == "hitl_required":
                    approval_token = event.get("approval_token")
                    print(f"\n >>> HITL SECURITY GATE TRIGGERED! <<<")
                    print(f" Target Dataset:   {event.get('dataset_id')}")
                    print(f" Single-Use Token: {approval_token}")
                    print(f" Proposed Recipe:  {json.dumps(event.get('cleaning_recipe'), indent=2)}")
                elif etype == "text_delta":
                    print(event.get("content"), end="", flush=True)

    if approval_token:
        print_banner("4. AUTHORIZE & EXECUTE PIPELINE (/api/chat/approve)")
        approve_payload = {
            "approval_token": approval_token,
            "session_id": session_id
        }
        req3 = urllib.request.Request(
            f"{BASE_URL}/api/chat/approve",
            data=json.dumps(approve_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req3) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    event = json.loads(line_str[6:])
                    etype = event.get("type")
                    if etype == "thought":
                        print(f" [THOUGHT]    {event.get('content')}")
                    elif etype == "tool_start":
                        print(f" [TOOL START] Executing: {event.get('tool')}")
                    elif etype == "tool_result":
                        res = event.get("result", {})
                        if isinstance(res, dict):
                            stats_b = res.get("stats_before", {})
                            stats_a = res.get("stats_after", {})
                            print(f"\n [PIPELINE OUTPUT METRICS]")
                            print(f" Raw Rows:         {stats_b.get('total_rows')}")
                            print(f" Cleaned Rows:     {stats_a.get('total_rows')}")
                            print(f" Pre-Health Score: {stats_b.get('health_score')}/100")
                            print(f" Post-Health Score:{stats_a.get('health_score')}/100")
                            print(f" Quality Delta:    +{res.get('health_score_delta')}%")
                            print(f" Cleaned Output:   {res.get('output_filename')}")
                            print(f" Inferred Types:   {res.get('inferred_types')}")
                            print(f" Actions Taken:")
                            for act in res.get("actions_taken", []):
                                print(f"    - {act}")
                    elif etype == "text_delta":
                        print(event.get("content"), end="", flush=True)
                    elif etype == "complete":
                        print(f"\n [COMPLETE]   Pipeline run completed.")

    print_banner("5. VERIFYING GENERATED DATA LAKE ASSETS (/api/data/processed)")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/data/processed") as resp:
            data_assets = json.loads(resp.read().decode())
            print(f"Available Cleaned Files in /processed_data/:")
            for f in data_assets.get("files", []):
                print(f" - {f.get('filename')} ({f.get('format')}, {f.get('size_bytes')} bytes)")
    except Exception as e:
        print(f"Error fetching data assets: {e}")

if __name__ == "__main__":
    main()
