import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://my-api.plantnet.org/v2/diseases"
OUTPUT_FILE = "plantnet_diseases.json"

def fetch_diseases(api_key):
    """
    Fetch all diseases from the PlantNet API.

    Args:
        api_key (str): Your PlantNet API key

    Returns:
        list: List of disease objects
    """
    print("Fetching diseases from PlantNet API...")

    params = {
        "api-key": api_key
    }

    try:
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        diseases = response.json()
        print(f"✓ Successfully fetched {len(diseases)} diseases")
        return diseases

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching data: {e}")
        sys.exit(1)

def save_to_json(data, filename):
    """
    Save data to a JSON file with metadata.

    Args:
        data (list): Disease data to save
        filename (str): Output filename
    """
    output = {
        "metadata": {
            "source": "PlantNet API",
            "endpoint": API_BASE_URL,
            "extracted_at": datetime.now().isoformat(),
            "total_diseases": len(data)
        },
        "diseases": data
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✓ Data saved to {filename}")

    except IOError as e:
        print(f"✗ Error saving file: {e}")
        sys.exit(1)

def display_summary(diseases):
    """
    Display a summary of the extracted diseases.

    Args:
        diseases (list): List of disease objects
    """
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total diseases: {len(diseases)}")

    # Count diseases by category
    categories = {}
    for disease in diseases:
        cats = disease.get('categories', [])
        if not cats:
            categories['Uncategorized'] = categories.get('Uncategorized', 0) + 1
        else:
            for cat in cats:
                categories[cat] = categories.get(cat, 0) + 1

    if categories:
        print("\nDiseases by category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cat}: {count}")

    # Show first few examples
    print("\nFirst 5 diseases:")
    for disease in diseases[:5]:
        print(f"  - {disease.get('label', 'N/A')} ({disease.get('name', 'N/A')})")
        if disease.get('categories'):
            print(f"    Categories: {', '.join(disease['categories'])}")

def main():
    """Main execution function."""
    print("="*50)
    print("PlantNet Disease List Extractor")
    print("="*50)
    print()

    # Get API key from user
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = input("Enter your PlantNet API key: ").strip()

    if not api_key:
        print("✗ API key is required!")
        print("\nUsage:")
        print("  python plantnet_diseases_extractor.py YOUR_API_KEY")
        print("  or run without arguments to enter it interactively")
        sys.exit(1)

    # Fetch diseases
    diseases = fetch_diseases(api_key)

    # Save to JSON
    save_to_json(diseases, OUTPUT_FILE)

    # Display summary
    display_summary(diseases)

    print("\n✓ Done!")

if __name__ == "__main__":
    main()
