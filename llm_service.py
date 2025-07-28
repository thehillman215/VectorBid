import json
import os
import logging
from typing import List, Dict, Any

from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY environment variable not set")
    raise ValueError("OpenAI API key is required")

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def rank_trips_with_ai(trips: List[Dict[str, Any]], preferences: str) -> List[Dict[str, Any]]:
    """
    Use OpenAI to rank trips based on user preferences.
    
    Args:
        trips: List of trip dictionaries
        preferences: Natural language preferences from the user
    
    Returns:
        List of ranked trips with AI comments
    """
    try:
        # Prepare the trips data for the AI
        trips_summary = []
        for trip in trips:
            summary = {
                'id': trip['id'],
                'duration': trip['duration'],
                'dates': trip['dates'],
                'routing': trip['routing'],
                'credit_hours': trip['credit_hours'],
                'includes_weekend': trip['includes_weekend']
            }
            trips_summary.append(summary)
        
        # Create the prompt for ranking
        system_prompt = """You are an expert airline pilot schedule assistant. You help pilots rank their trip bids based on their personal preferences and quality of life factors.

Your task is to analyze the provided trips and rank them according to the pilot's stated preferences. Consider factors like:
- Trip duration and layover quality
- Weekend and time off preferences  
- Route preferences and destinations
- Work-life balance factors
- Credit hours and pay considerations
- Commuting and positioning needs

Provide a ranking with brief explanations for why each trip fits or doesn't fit the pilot's preferences."""

        user_prompt = f"""Please rank these pilot trips based on the following preferences: "{preferences}"

Available trips:
{json.dumps(trips_summary, indent=2)}

Please respond with JSON in this exact format:
{{
  "ranked_trips": [
    {{
      "trip_id": "trip_id_here",
      "rank": 1,
      "comment": "Brief explanation of why this trip ranks here based on the preferences"
    }}
  ]
}}

Rank ALL trips from best (rank 1) to worst, with each trip having a unique rank number."""

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent rankings
            max_tokens=2000
        )
        
        # Parse the response
        response_content = response.choices[0].message.content
        if not response_content:
            raise ValueError("Empty response from OpenAI")
        result = json.loads(response_content)
        ranked_trips = result.get('ranked_trips', [])
        
        # Validate that we have rankings for all trips
        trip_ids = {trip['id'] for trip in trips}
        ranked_ids = {item['trip_id'] for item in ranked_trips}
        
        # Add any missing trips at the end
        missing_ids = trip_ids - ranked_ids
        max_rank = max([item.get('rank', 0) for item in ranked_trips], default=0)
        
        for trip_id in missing_ids:
            max_rank += 1
            ranked_trips.append({
                'trip_id': trip_id,
                'rank': max_rank,
                'comment': 'No specific ranking provided by AI'
            })
        
        # Sort by rank and return
        ranked_trips.sort(key=lambda x: x.get('rank', 999))
        
        # Format for frontend (remove rank field, order represents ranking)
        return [{'trip_id': item['trip_id'], 'comment': item['comment']} for item in ranked_trips]
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse AI response as JSON: {str(e)}")
        # Fallback: return trips in original order with generic comments
        return [{'trip_id': trip['id'], 'comment': 'AI ranking unavailable'} for trip in trips]
    
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {str(e)}")
        # Fallback: return trips in original order with error message
        return [{'trip_id': trip['id'], 'comment': f'Error in AI ranking: {str(e)}'} for trip in trips]


def test_openai_connection():
    """Test the OpenAI API connection"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        return True, "OpenAI connection successful"
    except Exception as e:
        return False, f"OpenAI connection failed: {str(e)}"
