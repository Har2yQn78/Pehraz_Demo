import os
import json
import requests
from dotenv import load_dotenv

# Load API key from your .env file
load_dotenv()
API_KEY = os.getenv("PLANTNET_API_KEY")
BASE_URL = "https://my-api.plantnet.org/v2/species"

def download_all_species(output_file="species_list.json"):
    if not API_KEY:
        print("Error: PLANTNET_API_KEY not found in .env file.")
        return

    all_species = []
    page = 1
    page_size = 500  # Maximum recommended page size

    print(f"Starting download from {BASE_URL}...")

    while True:
        params = {
            "api-key": API_KEY,
            "page": page,
            "pageSize": page_size,
            "lang": "en"
        }

        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # If the response is an empty list, we've reached the end
            if not data:
                break

            all_species.extend(data)
            print(f"Downloaded page {page} ({len(all_species)} species so far...)")

            # Increment page for next request
            page += 1

        except requests.exceptions.HTTPError as e:
            print(f"Failed to fetch page {page}: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    # Save to a JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_species, f, indent=4, ensure_ascii=False)

    print(f"\nSuccess! Total species downloaded: {len(all_species)}")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    download_all_species()
