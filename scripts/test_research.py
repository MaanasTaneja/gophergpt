import requests
import os

BACKEND = os.getenv('RESEARCH_BACKEND', 'http://localhost:8000')

def test_query(q='climate adaptation'):
    url = f"{BACKEND}/research"
    r = requests.post(url, json={'query': q, 'max_results': 3}, timeout=30)
    print('STATUS:', r.status_code)
    try:
        data = r.json()
        print('SOURCE:', data.get('source'))
        print('SUMMARY:\n', data.get('summary'))
        for i, it in enumerate(data.get('results', []), 1):
            print(f"\n[{i}] {it.get('title')}\n{it.get('url')}\n{it.get('snippet')[:400]}\n")
    except Exception as e:
        print('NON-JSON RESPONSE:', r.text[:1000])

if __name__ == '__main__':
    test_query()
