
"""OpenAI integration: rank trips by preferences and return top N."""
import os
import json
import logging
from typing import List, Dict

from openai import OpenAI, OpenAIError

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logging.warning('OPENAI_API_KEY not set – LLM ranking disabled.')

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are VectorBid, an AI assistant that helps airline pilots choose bid trips.
Rank trips based on how well they satisfy the pilot's stated preferences.
Only return the **top 10** trips as JSON in this exact schema:
[
  { "rank": 1, "trip_id": "1234", "comment": "why it's ranked here" },
  ...
]
"""

def _summarize_trip(trip: Dict) -> str:
    return (
        f"Trip {trip['trip_id']}: {trip['days']}-day, "
        f"{trip['credit_hours']} credit hrs, "
        f"{'includes weekend' if trip['includes_weekend'] else 'weekday only'}, "
        f"routing {trip['routing']}"
    )


def rank_trips_with_ai(trips: List[Dict], preferences: str) -> List[Dict]:
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY missing – cannot call OpenAI.')

    # Summarize trips (max 50 to keep tokens under control)
    summaries = [_summarize_trip(t) for t in trips[:50]]
    user_prompt = (
        f"Pilot preferences: {preferences}\n\n"
        f"Available trips:\n" +
        "\n".join(summaries)
    )

    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            temperature=0,
            max_tokens=800,
            messages=[
                { "role": "system", "content": SYSTEM_PROMPT },
                { "role": "user", "content": user_prompt }
            ],
            response_format={ "type": "json_object" }
        )
    except OpenAIError as exc:
        logging.error(f'OpenAI API error: {exc}')
        raise

    content = response.choices[0].message.content
    try:
        ranked_list = json.loads(content)
        return ranked_list
    except json.JSONDecodeError:
        logging.error('Could not decode LLM JSON output. Raw content:\n%s', content)
        raise
