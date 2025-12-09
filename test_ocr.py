#!/usr/bin/env python3
"""
OCR Testing Script for Hackathon
Tests image text extraction on receipts, invoices, and documents
"""

import os
import sys
import asyncio
from pathlib import Path
import base64
from PIL import Image
import io

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️  pytesseract not available")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  OpenCV not available")

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = None
if os.getenv('OPENAI_API_KEY'):
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("✅ OpenAI client initialized")
else:
    print("⚠️  OpenAI API key not found")


def preprocess_image_cv2(image_bytes: bytes):
    """Preprocess image using OpenCV for better OCR."""
    if not CV2_AVAILABLE:
        return None
    
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    except Exception as e:
        print(f"❌ OpenCV preprocessing error: {e}")
        return None


def preprocess_image_pil(image_bytes: bytes):
    """Preprocess image using PIL for better OCR."""
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # Convert bytes to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to grayscale
        gray_image = pil_image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced = enhancer.enhance(2.0)
        
        # Sharpen
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        
        return sharpened
    except Exception as e:
        print(f"❌ PIL preprocessing error: {e}")
        return None


def extract_text_pytesseract(image_bytes: bytes) -> str:
    """Extract text using pytesseract."""
    if not PYTESSERACT_AVAILABLE:
        return ""
    
    try:
        # Try with OpenCV preprocessing first
        if CV2_AVAILABLE:
            processed = preprocess_image_cv2(image_bytes)
            if processed is not None:
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(processed, config=custom_config)
                return text.strip()
        
        # Fallback to PIL preprocessing
        processed = preprocess_image_pil(image_bytes)
        if processed is not None:
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed, config=custom_config)
            return text.strip()
        
        return ""
    except Exception as e:
        print(f"❌ Pytesseract error: {e}")
        return ""


async def extract_text_gpt_vision(image_bytes: bytes) -> str:
    """Extract text using GPT Vision."""
    if openai_client is None:
        return ""
    
    try:
        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract ALL text from this receipt/invoice/document image. Include amounts, dates, items, merchant names, addresses - everything visible. Format it clearly and preserve the structure."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        text = response.choices[0].message.content
        return text.strip() if text else ""
    except Exception as e:
        print(f"❌ GPT Vision error: {e}")
        return ""


async def test_image(image_path: str):
    """Test OCR on a single image."""
    print(f"\n{'='*80}")
    print(f"📸 Testing: {os.path.basename(image_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return
    
    # Read image bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Get image info
    try:
        img = Image.open(image_path)
        print(f"📊 Image size: {img.size[0]}x{img.size[1]} pixels")
        print(f"📊 Format: {img.format}")
        print(f"📊 Mode: {img.mode}")
    except Exception as e:
        print(f"⚠️  Could not read image info: {e}")
    
    print()
    
    # Test with pytesseract
    if PYTESSERACT_AVAILABLE:
        print("🔍 Testing Pytesseract OCR...")
        pytesseract_text = extract_text_pytesseract(image_bytes)
        if pytesseract_text:
            print("✅ Pytesseract extracted text:")
            print("-" * 80)
            print(pytesseract_text)
            print("-" * 80)
            print(f"📏 Length: {len(pytesseract_text)} characters")
        else:
            print("❌ Pytesseract: No text extracted")
        print()
    
    # Test with GPT Vision
    if openai_client:
        print("🔍 Testing GPT Vision OCR...")
        gpt_text = await extract_text_gpt_vision(image_bytes)
        if gpt_text:
            print("✅ GPT Vision extracted text:")
            print("-" * 80)
            print(gpt_text)
            print("-" * 80)
            print(f"📏 Length: {len(gpt_text)} characters")
        else:
            print("❌ GPT Vision: No text extracted")
        print()


async def main():
    """Main test function."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         OCR Testing Script for Hackathon - Aliran Tunai       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # Check what's available
    print("🔧 Available OCR Methods:")
    print(f"  • Pytesseract: {'✅ Available' if PYTESSERACT_AVAILABLE else '❌ Not available'}")
    print(f"  • OpenCV: {'✅ Available' if CV2_AVAILABLE else '❌ Not available'}")
    print(f"  • GPT Vision: {'✅ Available' if openai_client else '❌ Not available'}")
    print()
    
    # Create test_images directory if it doesn't exist
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Look for test images
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    test_images = []
    
    for ext in image_extensions:
        test_images.extend(test_dir.glob(f'*{ext}'))
    
    if not test_images:
        print("⚠️  No test images found in 'test_images/' directory")
        print()
        print("📝 To test OCR:")
        print("  1. Create a 'test_images' folder")
        print("  2. Add receipt/invoice images (JPG, PNG, etc.)")
        print("  3. Run this script again")
        print()
        print("💡 Example structure:")
        print("  test_images/")
        print("    ├── receipt1.jpg")
        print("    ├── invoice2.png")
        print("    └── document3.jpg")
        return
    
    print(f"📂 Found {len(test_images)} test image(s)")
    
    # Test each image
    for image_path in test_images:
        await test_image(str(image_path))
    
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
