import google.generativeai as genai

# Configure your real API key
genai.configure(api_key="AIzaSyCPsQ5Hd0gteHyIryT6zm4-Lske0zzKWvU")

# List all models available to your key
models = genai.list_models()
for m in models:
    print(m.name, m.supported_generation_methods)
