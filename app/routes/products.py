from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def products_overview(request: Request):
    """Products overview page showcasing all VectorBid solutions"""
    return templates.TemplateResponse("pages/products/index.html", {
        "request": request,
        "page_title": "VectorBid Products",
        "page_description": "Comprehensive suite of AI-powered tools for pilot schedule optimization and bidding strategy.",
        "products": [
            {
                "name": "Bid Optimizer",
                "tagline": "AI-powered schedule optimization",
                "description": "Transform your preferences into winning PBS bids with contract-aware AI that maximizes your time at home.",
                "icon": "fas fa-magic",
                "url": "/products/bid-optimizer",
                "features": ["Contract awareness", "AI optimization", "Success prediction", "Instant export"],
                "stats": {"success_rate": "94%", "time_saved": "3.2h", "users": "1,800+"}
            },
            {
                "name": "Route Analyzer", 
                "tagline": "Smart pattern recognition",
                "description": "Discover hidden patterns in your airline's scheduling data to make informed bidding decisions.",
                "icon": "fas fa-route",
                "url": "/products/route-analyzer", 
                "features": ["Pattern detection", "Trend analysis", "Seasonal insights", "Preference mapping"],
                "stats": {"patterns_found": "500+", "accuracy": "92%", "airlines": "15+"}
            },
            {
                "name": "Schedule Builder",
                "tagline": "Conflict-free construction", 
                "description": "Build optimal schedules with automatic conflict detection and resolution using advanced algorithms.",
                "icon": "fas fa-calendar-alt",
                "url": "/products/schedule-builder",
                "features": ["Conflict detection", "Auto-resolution", "Legal compliance", "Multi-scenario"],
                "stats": {"conflicts_resolved": "10k+", "compliance": "100%", "efficiency": "85%"}
            },
            {
                "name": "Pattern Intelligence",
                "tagline": "Predictive analytics",
                "description": "Leverage machine learning to predict bidding outcomes and optimize your strategy over time.", 
                "icon": "fas fa-brain",
                "url": "/products/pattern-intelligence",
                "features": ["Outcome prediction", "Strategy optimization", "Learning algorithms", "Performance tracking"],
                "stats": {"prediction_accuracy": "89%", "improvement": "23%", "data_points": "1M+"}
            },
            {
                "name": "Mobile App",
                "tagline": "Bid from anywhere",
                "description": "Full-featured iOS and Android apps for managing bids, checking results, and staying connected.",
                "icon": "fas fa-mobile-alt", 
                "url": "/products/mobile",
                "features": ["Cross-platform", "Offline mode", "Push notifications", "Sync everywhere"],
                "stats": {"app_rating": "4.9", "downloads": "5k+", "platforms": "iOS & Android"}
            }
        ],
        "comparison_cta": {
            "title": "Not sure which product is right for you?",
            "description": "Compare features, pricing, and capabilities across all VectorBid products.",
            "button_text": "Compare Products",
            "button_url": "/products/comparison"
        }
    })

@router.get("/bid-optimizer", response_class=HTMLResponse)
async def bid_optimizer(request: Request):
    """Detailed Bid Optimizer product page"""
    return templates.TemplateResponse("pages/products/bid-optimizer.html", {
        "request": request,
        "page_title": "Bid Optimizer - AI-Powered Schedule Optimization",
        "page_description": "Transform your bidding strategy with AI that understands your contract and maximizes your quality of life.",
        "hero": {
            "headline": "Win the schedule you want with AI precision", 
            "subheadline": "94% of pilots get their preferred schedule using VectorBid's contract-aware optimization engine.",
            "demo_video": "/static/videos/bid-optimizer-demo.mp4",
            "cta_primary": "Start Free Trial",
            "cta_secondary": "Schedule Demo"
        },
        "key_benefits": [
            {
                "title": "Contract Intelligence",
                "description": "Understands your airline's specific PBS rules, work rules, and FAR regulations.",
                "icon": "fas fa-file-contract"
            },
            {
                "title": "Personal Optimization", 
                "description": "Learns your preferences and optimizes for what matters most to your lifestyle.",
                "icon": "fas fa-user-cog"
            },
            {
                "title": "Success Prediction",
                "description": "Predicts bid success probability and suggests alternatives for maximum efficiency.",
                "icon": "fas fa-chart-line"
            }
        ],
        "how_it_works": [
            {
                "step": 1,
                "title": "Upload Your Bid Package",
                "description": "Simply upload your airline's monthly bid package in any format (PDF, CSV, etc.)."
            },
            {
                "step": 2,
                "title": "Set Your Preferences", 
                "description": "Tell us what matters: days off, destinations, commute, family time, credit goals."
            },
            {
                "step": 3,
                "title": "Get Optimized Layers",
                "description": "Receive ranked PBS layers designed to maximize your chances of success."
            },
            {
                "step": 4,
                "title": "Export and Submit",
                "description": "One-click export to your airline's PBS system. Submit with confidence."
            }
        ],
        "features": {
            "ai_engine": [
                "Advanced optimization algorithms",
                "Machine learning from thousands of bids", 
                "Continuous model improvement",
                "Multi-objective optimization"
            ],
            "contract_awareness": [
                "Automatic rule interpretation",
                "Legality checking",
                "Compliance validation",
                "Custom contract support"
            ],
            "personalization": [
                "Preference learning",
                "Historical analysis",
                "Persona-based optimization",
                "Custom weight adjustments"
            ],
            "integration": [
                "All major PBS systems",
                "Multiple file formats",
                "API access available",
                "Mobile synchronization"
            ]
        },
        "testimonials": [
            {
                "quote": "VectorBid got me 4 weekends off in February when I typically get 2. The AI really understands pilot life.",
                "author": "Captain Jennifer L.",
                "airline": "United Airlines",
                "years_experience": 12
            },
            {
                "quote": "As a commuter, this tool is invaluable. It optimizes for commute efficiency better than I ever could manually.",
                "author": "FO David K.",
                "airline": "United Airlines", 
                "years_experience": 8
            }
        ],
        "pricing": {
            "monthly": 29,
            "annual": 24,
            "trial_days": 7,
            "money_back_days": 30
        }
    })

@router.get("/route-analyzer", response_class=HTMLResponse)
async def route_analyzer(request: Request):
    """Route Analyzer product page"""
    return templates.TemplateResponse("pages/products/route-analyzer.html", {
        "request": request,
        "page_title": "Route Analyzer - Smart Pattern Recognition",
        "page_description": "Discover hidden patterns in airline scheduling data to make informed bidding decisions.",
        "hero": {
            "headline": "Unlock hidden patterns in your airline's data",
            "subheadline": "Advanced analytics reveal scheduling trends that give you a competitive edge in bidding.",
            "features_preview": ["Seasonal patterns", "Route popularity", "Crew preferences", "Historical success rates"]
        },
        "capabilities": [
            {
                "name": "Pattern Detection",
                "description": "Automatically identifies recurring patterns in scheduling, routing, and crew assignments.",
                "use_cases": ["Peak travel seasons", "Equipment rotations", "Base assignments", "Holiday scheduling"]
            },
            {
                "name": "Trend Analysis",
                "description": "Analyzes historical data to predict future scheduling trends and opportunities.", 
                "use_cases": ["Route expansion", "Seasonal adjustments", "Fleet changes", "Market demands"]
            },
            {
                "name": "Success Metrics",
                "description": "Tracks bidding success rates across different variables to optimize your strategy.",
                "use_cases": ["Bid timing", "Layer ordering", "Preference weights", "Success probability"]
            }
        ]
    })

@router.get("/schedule-builder", response_class=HTMLResponse)
async def schedule_builder(request: Request):
    """Schedule Builder product page"""
    return templates.TemplateResponse("pages/products/schedule-builder.html", {
        "request": request,
        "page_title": "Schedule Builder - Conflict-Free Construction",
        "page_description": "Build optimal schedules with automatic conflict detection and resolution.",
        "hero": {
            "headline": "Build perfect schedules without conflicts",
            "subheadline": "Advanced algorithms automatically detect and resolve scheduling conflicts while optimizing for your preferences."
        },
        "key_features": [
            {
                "name": "Automatic Conflict Detection",
                "description": "Real-time analysis identifies potential conflicts before they become problems.",
                "benefits": ["Legal compliance", "Time savings", "Error prevention", "Stress reduction"]
            },
            {
                "name": "Smart Resolution Engine", 
                "description": "AI-powered suggestions for resolving conflicts while maintaining optimization goals.",
                "benefits": ["Multiple solutions", "Preference preservation", "Minimal disruption", "Learn from choices"]
            },
            {
                "name": "Multi-Scenario Planning",
                "description": "Create and compare multiple schedule scenarios to find the optimal solution.",
                "benefits": ["Risk assessment", "Contingency planning", "Outcome comparison", "Decision support"]
            }
        ]
    })

@router.get("/pattern-intelligence", response_class=HTMLResponse) 
async def pattern_intelligence(request: Request):
    """Pattern Intelligence product page"""
    return templates.TemplateResponse("pages/products/pattern-intelligence.html", {
        "request": request,
        "page_title": "Pattern Intelligence - Predictive Analytics",
        "page_description": "Leverage machine learning to predict bidding outcomes and optimize strategy over time.",
        "hero": {
            "headline": "Predict success before you bid",
            "subheadline": "Machine learning algorithms analyze millions of data points to predict bidding outcomes with 89% accuracy."
        },
        "intelligence_features": [
            {
                "name": "Outcome Prediction",
                "description": "Predicts the probability of getting specific pairings or schedule patterns.",
                "accuracy": "89%",
                "applications": ["Bid strategy", "Risk assessment", "Alternative planning", "Success optimization"]
            },
            {
                "name": "Learning Algorithms",
                "description": "Continuously learns from your bidding history to improve recommendations.",
                "improvement": "23% average",
                "applications": ["Preference refinement", "Strategy adaptation", "Personal optimization", "Performance tracking"]
            },
            {
                "name": "Market Intelligence",
                "description": "Analyzes airline-wide patterns to identify opportunities and trends.",
                "data_points": "1M+",
                "applications": ["Competitive analysis", "Trend identification", "Opportunity detection", "Strategic planning"]
            }
        ]
    })

@router.get("/mobile", response_class=HTMLResponse)
async def mobile_app(request: Request):
    """Mobile App product page"""
    return templates.TemplateResponse("pages/products/mobile.html", {
        "request": request,
        "page_title": "VectorBid Mobile - Bid From Anywhere",
        "page_description": "Full-featured iOS and Android apps for managing bids on the go.",
        "hero": {
            "headline": "Your bidding assistant in your pocket",
            "subheadline": "Full VectorBid functionality on iOS and Android with offline support and real-time sync.",
            "app_store_badges": True,
            "screenshots": [
                "/static/images/mobile/dashboard.png",
                "/static/images/mobile/bid-optimizer.png", 
                "/static/images/mobile/results.png"
            ]
        },
        "mobile_features": [
            {
                "name": "Complete Feature Set",
                "description": "All VectorBid features available on mobile with touch-optimized interface.",
                "details": ["Bid optimization", "Route analysis", "Schedule building", "Pattern intelligence"]
            },
            {
                "name": "Offline Capability", 
                "description": "Work on bids even without internet connection, sync when connected.",
                "details": ["Offline editing", "Local storage", "Background sync", "Conflict resolution"]
            },
            {
                "name": "Push Notifications",
                "description": "Stay informed about bid deadlines, results, and important updates.",
                "details": ["Bid reminders", "Result alerts", "System updates", "Custom preferences"]
            },
            {
                "name": "Cross-Platform Sync",
                "description": "Seamless synchronization between mobile, tablet, and desktop.",
                "details": ["Real-time sync", "Version control", "Conflict resolution", "Universal access"]
            }
        ],
        "download_stats": {
            "rating": 4.9,
            "downloads": "5,000+",
            "reviews": 847,
            "platforms": ["iOS 14+", "Android 8+"]
        }
    })

@router.get("/comparison", response_class=HTMLResponse)
async def products_comparison(request: Request):
    """Product comparison page"""
    return templates.TemplateResponse("pages/products/comparison.html", {
        "request": request,
        "page_title": "Product Comparison",
        "page_description": "Compare VectorBid products to find the right solution for your needs.",
        "comparison_matrix": {
            "products": ["Bid Optimizer", "Route Analyzer", "Schedule Builder", "Pattern Intelligence", "Mobile App"],
            "categories": [
                {
                    "name": "Core Features",
                    "features": [
                        {"name": "AI Optimization", "values": ["✓", "✓", "✓", "✓", "✓"]},
                        {"name": "Contract Awareness", "values": ["✓", "✓", "✓", "○", "✓"]},
                        {"name": "Pattern Recognition", "values": ["○", "✓", "○", "✓", "○"]},
                        {"name": "Conflict Detection", "values": ["○", "○", "✓", "○", "○"]},
                        {"name": "Mobile Access", "values": ["○", "○", "○", "○", "✓"]}
                    ]
                },
                {
                    "name": "Analytics",
                    "features": [
                        {"name": "Success Prediction", "values": ["✓", "✓", "○", "✓", "✓"]},
                        {"name": "Historical Analysis", "values": ["○", "✓", "○", "✓", "○"]},
                        {"name": "Performance Tracking", "values": ["✓", "✓", "✓", "✓", "✓"]},
                        {"name": "Market Intelligence", "values": ["○", "✓", "○", "✓", "○"]}
                    ]
                }
            ]
        }
    })

@router.get("/whats-new", response_class=HTMLResponse)
async def whats_new(request: Request):
    """What's new page with latest updates"""
    return templates.TemplateResponse("pages/products/whats-new.html", {
        "request": request,
        "page_title": "What's New",
        "page_description": "Latest features, improvements, and updates across all VectorBid products.",
        "latest_release": {
            "version": "2.1.0",
            "date": "2024-01-15",
            "title": "Enhanced AI Engine & Mobile Updates",
            "description": "Major improvements to optimization accuracy and new mobile features."
        },
        "recent_updates": [
            {
                "date": "2024-01-15",
                "title": "AI Engine 2.0",
                "category": "Bid Optimizer",
                "description": "23% improvement in optimization accuracy with new machine learning models.",
                "type": "improvement"
            },
            {
                "date": "2024-01-10", 
                "title": "Offline Mode",
                "category": "Mobile App",
                "description": "Work on bids without internet connection, sync when connected.",
                "type": "feature"
            },
            {
                "date": "2024-01-05",
                "title": "Pattern Detection Enhanced",
                "category": "Route Analyzer",
                "description": "New algorithms detect seasonal patterns with 95% accuracy.",
                "type": "improvement"
            }
        ]
    })
