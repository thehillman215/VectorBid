"""
Subscription Management System for VectorBid
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List, Tuple
import json
from pathlib import Path

class SubscriptionTier(Enum):
    FREE_TRIAL = "free_trial"
    ESSENTIAL = "essential"
    PRO = "pro"

class SubscriptionManager:
    """Manages user subscriptions"""

    def __init__(self):
        self.data_file = Path("data/subscriptions.json")
        self.data_file.parent.mkdir(exist_ok=True)

    def create_new_user_subscription(self, user_id: str) -> Dict:
        """Create a new free trial subscription"""
        subscription = {
            'user_id': user_id,
            'tier': SubscriptionTier.FREE_TRIAL.value,
            'status': 'active',
            'started_at': datetime.utcnow().isoformat(),
            'trial_ends_at': (datetime.utcnow() + timedelta(days=60)).isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=60)).isoformat(),
            'usage': {'monthly_generations': 0}
        }

        self._save_subscription(subscription)
        return subscription

    def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Get user subscription"""
        subs = self._load_subscriptions()

        if user_id not in subs:
            return self.create_new_user_subscription(user_id)

        return subs[user_id]

    def check_feature_access(self, user_id: str, feature: str) -> Tuple[bool, str]:
        """Check if user has access to feature"""
        subscription = self.get_user_subscription(user_id)

        if subscription and subscription['status'] != 'active':
            return False, "Subscription expired"

        # For MVP, all features available during trial
        return True, "Access granted"

    def _save_subscription(self, subscription: Dict):
        """Save subscription to file"""
        subs = self._load_subscriptions()
        subs[subscription['user_id']] = subscription

        with open(self.data_file, 'w') as f:
            json.dump(subs, f, indent=2)

    def _load_subscriptions(self) -> Dict:
        """Load subscriptions from file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {}

    def get_pricing_page_data(self) -> Dict:
        """Get pricing page data"""
        return {
            'tiers': [
                {
                    'id': 'free_trial',
                    'name': 'Free Trial',
                    'price': 0,
                    'price_display': 'Free for 60 days',
                    'features': [
                        'Upload schedule files',
                        'Basic PBS command generation',
                        'Save preferences',
                        'View bid packets'
                    ]
                },
                {
                    'id': 'essential',
                    'name': 'Essential',
                    'price': 19.99,
                    'price_display': '$19.99/mo',
                    'features': [
                        'Everything in Free Trial',
                        'Advanced PBS generation',
                        'Unlimited preferences',
                        'Conflict resolution',
                        '12-month history',
                        'Priority support'
                    ]
                },
                {
                    'id': 'pro',
                    'name': 'Professional',
                    'price': 39.99,
                    'price_display': '$39.99/mo',
                    'features': [
                        'Everything in Essential',
                        'Advanced analytics',
                        'Career progression tracking',
                        'API access',
                        'Phone support'
                    ]
                }
            ]
        }
