import requests
import time

def test_logs():
    # Trigger LLM Analysis
    print("Triggering run-llm...")
    resp = requests.post("http://localhost:8000/api/predictions/run-llm")
    print(resp.json())
    
    # Poll logs
    for i in range(5):
        time.sleep(2)
        resp = requests.get("http://localhost:8000/api/predictions/run-llm/logs")
        logs = resp.json()
        print(f"Poll {i}: {len(logs)} logs found")
        if len(logs) > 0:
            print(f"Sample log: {logs[-1]}")
            break

if __name__ == "__main__":
    test_logs()
