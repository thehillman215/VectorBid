import os

os.environ["USE_LLM"] = "true"

import sys

sys.path.insert(0, "src/lib")

from pbs_command_generator import generate_pbs_commands

# Simple test
result = generate_pbs_commands(
    "I want weekends off and maximum pay, prefer morning flights",
    {"base": "Denver (DEN)", "seniority": 70},
)

print(f"Method: {result['stats']['generation_method']}")
print(f"Quality: {result['stats']['quality_score']}/100")
print(f"Commands: {len(result['commands'])}")

if result["stats"]["generation_method"] == "llm":
    print("✅ LLM IS WORKING!")
else:
    print("❌ Still using fallback")
    if result.get("errors"):
        print(f"Errors: {result['errors']}")
