import google.generativeai as genai

genai.configure(api_key="AIzaSyAmoVaaE-_lpDNP_v37wi7yHvtLfqDgV8M")

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Hello")

print(response.text)