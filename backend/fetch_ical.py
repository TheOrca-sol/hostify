import requests
import sys

def fetch_and_print_ical(url: str):
    """
    Fetches content from an iCal URL and prints it to the console.

    Args:
        url: The iCal URL to fetch.
    """
    print(f"Fetching data from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        print("\n--- iCal Raw Data ---\n")
        print(response.text)
        print("\n--- End of Data ---\n")

    except requests.exceptions.RequestException as e:
        print(f"\nError: Failed to fetch data from the URL.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/fetch_ical.py <your_ical_url>")
        sys.exit(1)
    
    ical_url = sys.argv[1]
    fetch_and_print_ical(ical_url)
