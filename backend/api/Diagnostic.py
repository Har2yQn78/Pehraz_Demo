import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('PLANTNET_API_KEY')
PROJECT = 'all'

def test_image_validation():
    """Test if image validation corrupts the data"""
    print("=" * 60)
    print("TEST 1: Image Validation")
    print("=" * 60)

    # Create test image
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    image_data = img_bytes.getvalue()

    print(f"Original image size: {len(image_data)} bytes")

    # Test with verify() - THE BAD WAY
    print("\n🔴 Testing with img.verify() (BAD):")
    img1 = Image.open(BytesIO(image_data))
    try:
        img1.verify()
        print("  ✓ Verification passed")
        # Try to use image_data again
        img1_check = Image.open(BytesIO(image_data))
        print(f"  ✓ Can still open: format={img1_check.format}")
    except Exception as e:
        print(f"  ✗ Error after verify: {e}")

    # Test with load() - THE GOOD WAY
    print("\n🟢 Testing with img.load() (GOOD):")
    img2 = Image.open(BytesIO(image_data))
    try:
        img2.load()
        print("  ✓ Load passed")
        # Try to use image_data again
        img2_check = Image.open(BytesIO(image_data))
        print(f"  ✓ Can still open: format={img2_check.format}")
    except Exception as e:
        print(f"  ✗ Error after load: {e}")


def test_request_formats():
    """Test different request formats"""
    print("\n" + "=" * 60)
    print("TEST 2: Request Formats")
    print("=" * 60)

    if not API_KEY:
        print("❌ No API_KEY found in environment")
        return

    api_endpoint = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"

    # Create test image
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    image_data = img_bytes.getvalue()

    data = {'organs': ['leaf']}

    # Test 1: Dictionary format (WRONG)
    print("\n🔴 Test with files as DICT (WRONG):")
    files_dict = {
        'images': ('test.jpg', image_data, 'image/jpeg')
    }
    try:
        response = requests.post(api_endpoint, files=files_dict, data=data, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✓ Unexpected success with dict format!")
        else:
            print(f"  ✗ Failed as expected: {response.text[:100]}")
    except Exception as e:
        print(f"  ✗ Exception: {str(e)[:100]}")

    # Test 2: List format with prepared request (CORRECT)
    print("\n🟢 Test with files as LIST + prepared request (CORRECT):")
    files_list = [
        ('images', ('test.jpg', image_data, 'image/jpeg'))
    ]
    try:
        req = requests.Request('POST', url=api_endpoint, files=files_list, data=data)
        prepared = req.prepare()

        session = requests.Session()
        response = session.send(prepared, timeout=10)

        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Success! Found {len(result.get('results', []))} results")
            if result.get('results'):
                top = result['results'][0]
                species = top.get('species', {})
                print(f"  Top match: {species.get('scientificNameWithoutAuthor', 'Unknown')}")
        else:
            print(f"  ✗ Failed: {response.text[:200]}")
    except Exception as e:
        print(f"  ✗ Exception: {str(e)[:100]}")


def test_full_pipeline():
    """Test the complete pipeline as it would work in your app"""
    print("\n" + "=" * 60)
    print("TEST 3: Full Pipeline Simulation")
    print("=" * 60)

    if not API_KEY:
        print("❌ No API_KEY found in environment")
        return

    # Simulate uploaded file
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')

    # Step 1: Read image (as Django would)
    print("\n1️⃣ Reading uploaded file...")
    image_data = img_bytes.getvalue()
    print(f"   Size: {len(image_data)} bytes")

    # Step 2: Validate image (FIXED version)
    print("\n2️⃣ Validating image...")
    try:
        img_check = Image.open(BytesIO(image_data))
        if img_check.format is None:
            raise ValueError("Cannot determine image format")
        img_check.load()
        print(f"   ✓ Valid image: {img_check.format}")
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return

    # Step 3: Send to PlantNet
    print("\n3️⃣ Sending to PlantNet API...")
    api_endpoint = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"

    data = {'organs': ['leaf']}
    files = [
        ('images', ('test.jpg', image_data, 'image/jpeg'))
    ]

    try:
        req = requests.Request('POST', url=api_endpoint, files=files, data=data)
        prepared = req.prepare()

        session = requests.Session()
        response = session.send(prepared, timeout=10)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ SUCCESS! Got {len(result.get('results', []))} results")
            print(f"   Remaining requests: {result.get('remainingIdentificationRequests', 'N/A')}")
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}")

    except Exception as e:
        print(f"   ✗ Exception: {str(e)}")


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PlantNet API Integration Diagnostic Tool             ║
╚══════════════════════════════════════════════════════════════╝
    """)

    test_image_validation()
    test_request_formats()
    test_full_pipeline()

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("""
If all tests passed (🟢), your fix is working correctly!
If tests failed (🔴), check the error messages above.

Common issues:
- Missing API_KEY in .env file
- Network connectivity problems
- Invalid API key
- Rate limiting (too many requests)
    """)
