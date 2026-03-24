import json
import time
import queue
import random
import threading
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def _worker(worker_id, endpoints, duration, results_queue, credential=None, extra_headers=None):
    weights = [ep.get("weight", 1) for ep in endpoints]
    start_time = time.time()
    
    user_name = credential.get("name", f"worker-{worker_id}") if credential else f"worker-{worker_id}"
    cred_headers = credential.get("headers", {}) if credential else {}
    
    # Session per worker for connection pooling (simulates a user)
    session = requests.Session()

    while time.time() - start_time < duration:
        # Select an endpoint based on weight
        endpoint = random.choices(endpoints, weights=weights, k=1)[0]
        
        method = endpoint.get("method", "GET").upper()
        url = endpoint.get("url")
        headers = endpoint.get("headers", {}).copy()
        if extra_headers:
            headers.update(extra_headers)
        headers.update(cred_headers)
        body = endpoint.get("body", None)
        
        if not url:
            continue
            
        endpoint_name = f"{method} {url}"
            
        req_start = time.time()
        try:
            response = session.request(method, url, headers=headers, data=body, timeout=10)
            latency = time.time() - req_start
            
            # response size
            size = len(response.content)
            status = response.status_code
            
            results_queue.put({
                "worker": worker_id,
                "user": user_name,
                "endpoint": endpoint_name,
                "latency": latency,
                "size": size,
                "status": status,
                "error": None
            })
            
        except Exception as e:
            latency = time.time() - req_start
            results_queue.put({
                "worker": worker_id,
                "user": user_name,
                "endpoint": endpoint_name,
                "latency": latency,
                "size": 0,
                "status": 0,
                "error": str(e)
            })

def execute_load_test(config_file: str, filter_user: str = None, token: str = None, custom_headers: list = None):
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}", file=sys.stderr)
        sys.exit(1)
        
    duration = config.get("duration_seconds", 60)
    users = config.get("users", 10)
    endpoints = config.get("endpoints", [])
    credentials = config.get("credentials", [])
    
    if not endpoints:
        print("Error: No endpoints defined in configuration.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Starting Load Test with {users} users for {duration} seconds...")
    print(f"Targeting {len(endpoints)} endpoint(s).")
    
    results_queue = queue.Queue()
    
    extra_headers = {}
    if token:
        extra_headers["Authorization"] = f"Bearer {token}"
    if custom_headers:
        for h in custom_headers:
            if ":" in h:
                k, v = h.split(":", 1)
                extra_headers[k.strip()] = v.strip()
    
    test_start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=users) as executor:
        futures = []
        for i in range(users):
            cred = credentials[i % len(credentials)] if credentials else None
            futures.append(executor.submit(_worker, i, endpoints, duration, results_queue, cred, extra_headers))
            
        # Wait for all workers to complete
        for _ in as_completed(futures):
            pass
            
    actual_duration = time.time() - test_start_time
    
    # Process results
    latencies = []
    sizes = []
    statuses = {}
    errors = 0
    total_requests = 0
    
    all_results = []
    endpoint_stats = {}
    
    while not results_queue.empty():
        res = results_queue.get()
        
        # Filter metrics by user if parameter is provided
        if filter_user and res.get("user") != filter_user:
            continue
            
        all_results.append(res)
        total_requests += 1
        
        ep_name = res.get("endpoint", "Unknown")
        if ep_name not in endpoint_stats:
            endpoint_stats[ep_name] = []
            
        if res["error"]:
            errors += 1
        else:
            latencies.append(res["latency"])
            sizes.append(res["size"])
            status = res["status"]
            statuses[status] = statuses.get(status, 0) + 1
            endpoint_stats[ep_name].append(res["latency"])
            
    print("\n" + "="*40)
    print("LOAD TEST RESULTS")
    print("="*40)
    print(f"Test Duration:    {actual_duration:.2f} s")
    print(f"Total Requests:   {total_requests}")
    
    if actual_duration > 0:
        print(f"Reqs per second:  {total_requests / actual_duration:.2f} RPS")
        
    success_requests = len(latencies)
    print(f"Successful Reqs:  {success_requests}")
    print(f"Failed Reqs:      {errors}")
    
    if statuses:
        print("\nStatus Codes:")
        for st, count in sorted(statuses.items()):
            print(f"  {st}: {count}")
            
    if latencies:
        print("\nLatency (seconds):")
        print(f"  Min:  {min(latencies):.4f}")
        print(f"  Max:  {max(latencies):.4f}")
        print(f"  Avg:  {statistics.mean(latencies):.4f}")
        if len(latencies) > 1:
            print(f"  P95:  {statistics.quantiles(latencies, n=100)[94]:.4f}")
            
    if sizes:
        total_bytes = sum(sizes)
        print("\nResponse Size (bytes):")
        print(f"  Total: {total_bytes}")
        print(f"  Avg:   {total_bytes / len(sizes):.0f}")
        
    if endpoint_stats:
        print("\n" + "-"*40)
        print("ENDPOINT SUMMARY")
        print("-"*40)
        for ep, ep_lats in sorted(endpoint_stats.items()):
            print(f"\n[{ep}] ({len(ep_lats)} successful reqs):")
            if ep_lats:
                quant = statistics.quantiles(ep_lats, n=100) if len(ep_lats) >= 2 else None
                p50 = quant[49] if quant else ep_lats[0]
                p75 = quant[74] if quant else ep_lats[0]
                p90 = quant[89] if quant else ep_lats[0]
                p99 = quant[98] if quant else ep_lats[0]
                
                print(f"  Avg: {statistics.mean(ep_lats):.4f}s")
                print(f"  Min: {min(ep_lats):.4f}s  |  Max: {max(ep_lats):.4f}s")
                print(f"  P50: {p50:.4f}s  |  P75: {p75:.4f}s")
                print(f"  P90: {p90:.4f}s  |  P99: {p99:.4f}s")

    print("="*40)

    # Convert results internally to save CSV 
    import os
    import csv
    from datetime import datetime

    timestamp_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    report_filename = f"load_test_report_{timestamp_str}.csv"
    report_dir = os.path.join("LOCAL_DATA", "REPORTS")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, report_filename)

    try:
        with open(report_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["worker", "user", "endpoint", "latency", "size", "status", "error"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for res in all_results:
                writer.writerow(res)
        print(f"\n[+] Report successfully saved to: {report_path}")
    except Exception as e:
        print(f"\n[!] Error saving report: {e}", file=sys.stderr)

