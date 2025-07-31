
"""OpenAI integration: rank trips by preferences and return top N."""
import os
import json
import logging
from typing import List, Dict

from openai import OpenAI, OpenAIError

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logging.warning('OPENAI_API_KEY not set – LLM ranking disabled.')

def get_openai_client():
    """Get OpenAI client instance, created only when needed."""
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)

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

    client = get_openai_client()
    if not client:
        raise RuntimeError('Failed to initialize OpenAI client.')

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
    logging.debug(f"OpenAI response content: {content}")
    
    if not content:
        raise ValueError("Empty response from OpenAI")
    
    try:
        data = json.loads(content)
        
        # Handle different response formats
        if isinstance(data, list):
            ranked_list = data
        elif isinstance(data, dict) and 'trips' in data:
            ranked_list = data['trips']
        elif isinstance(data, dict) and 'rankings' in data:
            ranked_list = data['rankings']
        else:
            # If it's a dict with no expected key, try to extract the list
            for key, value in data.items():
                if isinstance(value, list):
                    ranked_list = value
                    break
            else:
                raise ValueError("No valid trip list found in response")
        
        # Validate the structure
        if not isinstance(ranked_list, list) or not ranked_list:
            raise ValueError("Expected non-empty list of trips")
            
        # Ensure each item has required fields
        for i, item in enumerate(ranked_list):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} is not a dictionary")
            if 'trip_id' not in item:
                item['trip_id'] = str(i + 1000)  # Fallback trip ID
            if 'rank' not in item:
                item['rank'] = i + 1
            if 'comment' not in item:
                item['comment'] = "Recommended based on preferences"
        
        return ranked_list
        
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f'Could not process LLM output: {e}. Raw content: {content}')
        # Return a fallback response to prevent complete failure
        return [
            {
                "rank": 1,
                "trip_id": "fallback",
                "comment": "AI processing failed - showing sample result"
            }
        ]
