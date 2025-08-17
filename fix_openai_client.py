import re

# Read the file
with open("src/lib/pbs_command_generator.py") as f:
    content = f.read()

# Fix the OpenAI client initialization - remove the timeout parameter that might be causing issues
old_client = """self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                timeout=Config.OPENAI_TIMEOUT
            )"""

new_client = """self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY
            )"""

content = content.replace(old_client, new_client)

# Also fix any 'proxies' parameter if it exists
content = re.sub(r",\s*proxies=[^)]+", "", content)

# Write back
with open("src/lib/pbs_command_generator.py", "w") as f:
    f.write(content)

print("Fixed OpenAI client initialization!")
