import os
from google import genai
from google.genai import types

def test_imagen():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API key")
        return
        
    client = genai.Client(api_key=api_key)
    try:
        print("Generating image...")
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt='A realistic CCTV camera frame capturing a white cargo van at night.',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="4:3"
            )
        )
        for generated_image in result.generated_images:
            with open("test_cctv.jpg", "wb") as f:
                f.write(generated_image.image.image_bytes)
            print("Successfully saved test_cctv.jpg")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_imagen()
