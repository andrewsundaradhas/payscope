"""Quick test script for the PayScope API."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    r = requests.get(f"{BASE_URL}/health")
    print(f"Health: {r.json()}")

def test_chat():
    """Test chat query endpoint."""
    payload = {
        "report_id": "r_auth_visa_dec",
        "question": "Why did settlement amounts drop last week?",
        "filters": {"network": "All", "range_days": 7}
    }
    r = requests.post(f"{BASE_URL}/api/chat/query", json=payload)
    data = r.json()
    print(f"\n=== Chat Query ===")
    print(f"Intent: {data.get('intent')}")
    print(f"Confidence: {data.get('confidence')}")
    print(f"\nAnswer:\n{data.get('answer')[:500]}...")
    print(f"\nMetrics: {data.get('metrics_used')}")
    print(f"Followups: {data.get('followups')}")

def test_insights():
    """Test insights generation endpoint."""
    payload = {
        "report_id": "r_auth_visa_dec",
        "filters": {"network": "All", "range_days": 7}
    }
    r = requests.post(f"{BASE_URL}/api/insights/generate", json=payload)
    data = r.json()
    print(f"\n=== Insights ===")
    print(f"KPIs: {[kpi['label'] for kpi in data.get('kpis', [])]}")
    print(f"Insight Cards: {[card['title'][:50] for card in data.get('insight_cards', [])]}")

def test_forecast():
    """Test forecast endpoint."""
    payload = {
        "report_id": "r_auth_visa_dec",
        "metric": "transactions",
        "horizon_days": 7
    }
    r = requests.post(f"{BASE_URL}/api/insights/forecast", json=payload)
    data = r.json()
    print(f"\n=== Forecast ===")
    print(f"Metric: {data.get('metric')}")
    print(f"Trend: {data.get('trend')}")
    print(f"Confidence: {data.get('confidence')}")
    print(f"Narrative: {data.get('narrative')[:200]}...")

def test_reports():
    """Test reports list endpoint."""
    r = requests.get(f"{BASE_URL}/api/reports/list")
    data = r.json()
    print(f"\n=== Reports ===")
    for report in data:
        print(f"  - {report['name']} ({report['type']} / {report['network']})")

def test_cross_analysis():
    """Test cross-analysis endpoint."""
    payload = {
        "auth_report_id": "r_auth_visa_dec",
        "settlement_report_id": "r_settle_visa_dec",
        "filters": {"network": "Visa", "range_days": 7}
    }
    r = requests.post(f"{BASE_URL}/api/insights/cross-analysis", json=payload)
    data = r.json()
    print(f"\n=== Cross-Analysis ===")
    print(f"Reconciliation Rate: {data.get('reconciliation_rate')}%")
    print(f"Narrative: {data.get('narrative')[:200]}...")

if __name__ == "__main__":
    try:
        test_health()
        test_reports()
        test_chat()
        test_insights()
        test_forecast()
        test_cross_analysis()
        print("\n✅ All API tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

