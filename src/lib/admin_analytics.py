"""
Admin Analytics System for VectorBid
"""

from datetime import datetime
from typing import Dict, List

class PilotAnalytics:
    """Analytics for individual pilots"""

    def get_pilot_analytics(self, user_id: str) -> Dict:
        """Get pilot analytics"""
        return {
            'user_id': user_id,
            'success_metrics': {
                'overall_success_rate': 0.72,
                'trend': 'improving',
                'average_satisfaction': 8.2
            },
            'preference_patterns': {
                'most_common_preferences': [
                    {'preference': 'Weekends off', 'frequency': 0.92},
                    {'preference': 'No early mornings', 'frequency': 0.78}
                ]
            },
            'career_progression': {
                'seniority_progression': {
                    'current_seniority': 245,
                    'percentile': 72
                }
            },
            'usage_statistics': {
                'account_created': '2024-01-15',
                'bids_generated': 24,
                'last_active': datetime.utcnow().isoformat()
            }
        }

class BroadcastSystem:
    """Broadcast messaging system"""

    def __init__(self):
        self.messages = []

    def create_broadcast(self, message_type: str, content: str) -> Dict:
        """Create a broadcast message"""
        message = {
            'id': f'msg_{len(self.messages) + 1}',
            'type': message_type,
            'content': content,
            'created_at': datetime.utcnow().isoformat()
        }
        self.messages.append(message)
        return message

    def get_broadcast_analytics(self) -> Dict:
        """Get broadcast analytics"""
        return {
            'total_sent': len(self.messages),
            'recent_messages': self.messages[-5:]
        }

class AdminDashboard:
    """Main admin dashboard"""

    def __init__(self):
        self.pilot_analytics = PilotAnalytics()
        self.broadcast_system = BroadcastSystem()

    def get_dashboard_data(self) -> Dict:
        """Get dashboard data"""
        return {
            'system_stats': {
                'total_users': 234,
                'active_users_30d': 89,
                'bids_generated': 1567
            },
            'broadcast_stats': self.broadcast_system.get_broadcast_analytics()
        }
