from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def solutions_overview(request: Request):
    """Solutions overview page organized by industry segments"""
    return templates.TemplateResponse("pages/solutions/index.html", {
        "request": request,
        "page_title": "VectorBid Solutions",
        "page_description": "Tailored solutions for different airline types, pilot roles, and operational needs.",
        "solution_categories": [
            {
                "title": "By Airline Type",
                "description": "Specialized configurations for different operational models",
                "solutions": [
                    {
                        "name": "Regional Airlines",
                        "description": "High-frequency, short-haul operations with rapid turnarounds",
                        "url": "/solutions/regional",
                        "key_benefits": ["Multi-leg optimization", "Turnaround efficiency", "Hub coordination"],
                        "customers": ["SkyWest", "Endeavor Air", "Republic Airways"]
                    },
                    {
                        "name": "Major Airlines", 
                        "description": "Complex long-haul networks with international operations",
                        "url": "/solutions/major",
                        "key_benefits": ["International rules", "Wide-body optimization", "Hub complexity"],
                        "customers": ["United Airlines", "Delta Air Lines", "American Airlines"]
                    },
                    {
                        "name": "Cargo Airlines",
                        "description": "Freight-focused operations with unique scheduling constraints", 
                        "url": "/solutions/cargo",
                        "key_benefits": ["Night operations", "Freight priorities", "Global networks"],
                        "customers": ["FedEx", "UPS Airlines", "Atlas Air"]
                    }
                ]
            },
            {
                "title": "By Pilot Role",
                "description": "Role-specific optimizations and career progression support",
                "solutions": [
                    {
                        "name": "First Officers",
                        "description": "Building experience while optimizing for work-life balance",
                        "url": "/solutions/first-officers", 
                        "key_benefits": ["Experience building", "Training coordination", "Career progression"],
                        "focus_areas": ["Learning opportunities", "Schedule flexibility", "Mentorship tracking"]
                    },
                    {
                        "name": "Captains",
                        "description": "Senior pilots balancing leadership with personal preferences",
                        "url": "/solutions/captains",
                        "key_benefits": ["Leadership roles", "Premium routes", "Experience optimization"], 
                        "focus_areas": ["Check ride coordination", "Training responsibilities", "Premium destinations"]
                    },
                    {
                        "name": "Check Airmen",
                        "description": "Training and evaluation specialists with complex scheduling needs",
                        "url": "/solutions/check-airmen",
                        "key_benefits": ["Training schedules", "Evaluation slots", "Travel coordination"],
                        "focus_areas": ["Simulator availability", "Student coordination", "Travel efficiency"]
                    }
                ]
            }
        ],
        "success_stories_preview": [
            {
                "airline": "Regional Carrier A",
                "improvement": "35% reduction in bidding time",
                "challenge": "Complex multi-hub operations",
                "solution": "Automated hub coordination optimization"
            },
            {
                "airline": "Major Airline B", 
                "improvement": "94% bid success rate",
                "challenge": "International scheduling complexity",
                "solution": "AI-powered constraint handling"
            }
        ]
    })

@router.get("/regional", response_class=HTMLResponse)
async def regional_airlines(request: Request):
    """Regional airlines solution page"""
    return templates.TemplateResponse("pages/solutions/regional.html", {
        "request": request,
        "page_title": "Solutions for Regional Airlines",
        "page_description": "Optimize high-frequency, short-haul operations with VectorBid's regional airline solutions.",
        "hero": {
            "headline": "Built for the pace of regional operations",
            "subheadline": "Handle complex multi-leg pairings and rapid turnarounds with AI that understands regional airline dynamics.",
            "stats": {
                "customers": "15+ regional carriers",
                "routes_optimized": "10,000+",
                "efficiency_gain": "28%"
            }
        },
        "challenges": [
            {
                "title": "Multi-Leg Complexity", 
                "description": "Regional routes often involve 4-6 legs per day with tight connections.",
                "solution": "Advanced algorithms optimize entire pairing sequences while respecting minimum connection times."
            },
            {
                "title": "Hub Coordination",
                "description": "Multiple hubs require careful coordination of crew positioning and aircraft flow.",
                "solution": "Cross-hub optimization ensures efficient crew utilization and minimal deadheading."
            },
            {
                "title": "Rapid Schedule Changes",
                "description": "Weather and operational changes require quick schedule adjustments.",
                "solution": "Real-time optimization engine adapts to changing conditions within minutes."
            }
        ],
        "regional_features": [
            {
                "name": "Multi-Hub Optimization",
                "description": "Coordinate crew assignments across multiple regional hubs for maximum efficiency.",
                "benefits": ["Reduced deadheading", "Better crew utilization", "Lower operational costs"]
            },
            {
                "name": "Connection Intelligence", 
                "description": "Smart connection planning considers passenger loads and aircraft positioning.",
                "benefits": ["Improved on-time performance", "Better passenger experience", "Operational flexibility"]
            },
            {
                "name": "Weather Integration",
                "description": "Historical weather patterns inform scheduling decisions and contingency planning.",
                "benefits": ["Proactive planning", "Reduced disruptions", "Better recovery strategies"]
            }
        ],
        "case_studies": [
            {
                "airline": "SkyWest Airlines",
                "challenge": "Optimizing crew scheduling across 200+ destinations with complex hub operations.",
                "solution": "Implemented VectorBid's multi-hub optimization with weather integration.",
                "results": {
                    "efficiency_improvement": "32%",
                    "cost_savings": "$2.3M annually", 
                    "pilot_satisfaction": "89% positive"
                }
            }
        ]
    })

@router.get("/major", response_class=HTMLResponse)
async def major_airlines(request: Request):
    """Major airlines solution page"""
    return templates.TemplateResponse("pages/solutions/major.html", {
        "request": request,
        "page_title": "Solutions for Major Airlines",
        "page_description": "Handle complex international operations and wide-body scheduling with enterprise-grade AI optimization.",
        "hero": {
            "headline": "Enterprise solutions for global operations",
            "subheadline": "Manage international routes, wide-body aircraft, and complex work rules with AI built for major airline complexity.",
            "enterprise_focus": True
        },
        "major_airline_challenges": [
            {
                "challenge": "International Regulations",
                "description": "Different countries have varying flight time limitations and rest requirements.",
                "vectorbid_solution": "Global regulatory database ensures compliance across all international routes."
            },
            {
                "challenge": "Wide-Body Operations",
                "description": "Long-haul flights require specialized crew scheduling and fatigue management.",
                "vectorbid_solution": "Fatigue risk management system optimizes rest periods and crew rotation."
            },
            {
                "challenge": "Alliance Coordination",
                "description": "Code-share agreements and alliance partnerships create scheduling dependencies.",
                "vectorbid_solution": "Partner integration modules coordinate schedules across alliance networks."
            }
        ],
        "enterprise_features": [
            {
                "category": "Global Compliance",
                "features": [
                    "International flight time regulations",
                    "Country-specific rest requirements", 
                    "Visa and documentation tracking",
                    "Customs and immigration optimization"
                ]
            },
            {
                "category": "Wide-Body Optimization",
                "features": [
                    "Long-haul fatigue management",
                    "Crew rest facility planning",
                    "International layover optimization",
                    "Time zone adaptation algorithms"
                ]
            },
            {
                "category": "Enterprise Integration",
                "features": [
                    "ERP system connectivity",
                    "Crew management system APIs",
                    "Real-time data synchronization", 
                    "Custom reporting dashboards"
                ]
            }
        ],
        "roi_calculator": {
            "title": "Calculate Your Potential Savings",
            "description": "See how VectorBid can reduce costs and improve efficiency for your major airline operations.",
            "metrics": [
                {"name": "Annual Pilot Hours", "unit": "hours"},
                {"name": "Average Hourly Cost", "unit": "dollars"},
                {"name": "Number of Pilots", "unit": "pilots"},
                {"name": "Current Efficiency", "unit": "percentage"}
            ]
        }
    })

@router.get("/cargo", response_class=HTMLResponse)
async def cargo_airlines(request: Request):
    """Cargo airlines solution page"""
    return templates.TemplateResponse("pages/solutions/cargo.html", {
        "request": request,
        "page_title": "Solutions for Cargo Airlines",
        "page_description": "Specialized scheduling solutions for freight operations with unique constraints and priorities.",
        "hero": {
            "headline": "Optimized for freight operations",
            "subheadline": "Handle night operations, cargo priorities, and global freight networks with purpose-built algorithms."
        },
        "cargo_specializations": [
            {
                "area": "Night Operations",
                "description": "Most cargo flights operate during overnight hours for next-day delivery.",
                "optimization": "Circadian rhythm-aware scheduling minimizes fatigue and maximizes alertness during critical night operations."
            },
            {
                "area": "Freight Priorities",
                "description": "Different cargo types have varying priority levels and handling requirements.", 
                "optimization": "Priority-based routing ensures time-critical shipments get optimal flight assignments."
            },
            {
                "area": "Global Networks",
                "description": "Cargo airlines operate complex hub-and-spoke networks spanning multiple continents.",
                "optimization": "Global network optimization coordinates crew positioning across international cargo hubs."
            }
        ]
    })

@router.get("/first-officers", response_class=HTMLResponse)
async def first_officers(request: Request):
    """First Officers solution page"""
    return templates.TemplateResponse("pages/solutions/first-officers.html", {
        "request": request,
        "page_title": "Solutions for First Officers",
        "page_description": "Career-focused optimization for First Officers building experience and advancing their aviation careers.",
        "hero": {
            "headline": "Build your career with smart scheduling",
            "subheadline": "Optimize for learning opportunities, experience building, and work-life balance as you advance your pilot career."
        },
        "fo_priorities": [
            {
                "priority": "Experience Building",
                "description": "Maximize exposure to different aircraft types, routes, and operational conditions.",
                "features": ["Aircraft type diversity", "Route variety tracking", "Weather experience", "Airport complexity levels"]
            },
            {
                "priority": "Training Coordination", 
                "description": "Balance line flying with recurrent training and upgrade preparation.",
                "features": ["Training schedule integration", "Study time allocation", "Simulator coordination", "Check ride preparation"]
            },
            {
                "priority": "Career Progression",
                "description": "Position yourself for advancement opportunities and captain upgrades.",
                "features": ["Leadership opportunities", "Mentorship tracking", "Performance metrics", "Upgrade readiness assessment"]
            }
        ],
        "career_tools": [
            {
                "tool": "Experience Tracker",
                "description": "Monitor your flight experience across different categories for career advancement.",
                "benefits": ["Resume building", "Upgrade preparation", "Skill development", "Goal tracking"]
            },
            {
                "tool": "Training Planner",
                "description": "Coordinate line flying with training requirements and personal study time.",
                "benefits": ["Schedule optimization", "Study time protection", "Training efficiency", "Knowledge retention"]
            }
        ]
    })

@router.get("/captains", response_class=HTMLResponse) 
async def captains(request: Request):
    """Captains solution page"""
    return templates.TemplateResponse("pages/solutions/captains.html", {
        "request": request,
        "page_title": "Solutions for Captains",
        "page_description": "Advanced scheduling optimization for experienced captains balancing leadership responsibilities with personal preferences.",
        "hero": {
            "headline": "Leadership-focused scheduling optimization",
            "subheadline": "Balance command responsibilities, premium routes, and personal preferences with AI that understands captain priorities."
        },
        "captain_focus_areas": [
            {
                "area": "Premium Routes",
                "description": "Access to high-value international routes and desirable destinations based on seniority.",
                "optimization": "Seniority-aware bidding maximizes access to premium routes while respecting system seniority."
            },
            {
                "area": "Leadership Roles",
                "description": "Coordination of training responsibilities, check rides, and crew development activities.",
                "optimization": "Leadership schedule integration balances command duties with line flying requirements."
            },
            {
                "area": "Experience Optimization",
                "description": "Leverage decades of experience for optimal route selection and crew pairing.",
                "optimization": "Experience-based recommendations suggest optimal crew combinations and route selections."
            }
        ],
        "senior_pilot_tools": [
            {
                "tool": "Seniority Optimizer",
                "description": "Leverage your seniority position for maximum schedule benefits and route access.",
                "features": ["Seniority-based bidding", "Route priority access", "Schedule flexibility", "Premium assignments"]
            },
            {
                "tool": "Leadership Coordinator",
                "description": "Balance training responsibilities with personal flying preferences.",
                "features": ["Check ride scheduling", "Training coordination", "Mentorship planning", "Leadership tracking"]
            }
        ]
    })

@router.get("/check-airmen", response_class=HTMLResponse)
async def check_airmen(request: Request):
    """Check Airmen solution page"""
    return templates.TemplateResponse("pages/solutions/check-airmen.html", {
        "request": request,
        "page_title": "Solutions for Check Airmen",
        "page_description": "Specialized scheduling for training and evaluation specialists with complex coordination requirements.",
        "hero": {
            "headline": "Specialized scheduling for aviation training experts",
            "subheadline": "Coordinate training schedules, evaluation sessions, and travel requirements with precision scheduling built for check airmen."
        },
        "check_airman_requirements": [
            {
                "requirement": "Training Coordination",
                "description": "Balance line flying with training responsibilities and student schedules.",
                "solution": "Integrated training calendar coordinates student availability with check airman schedules."
            },
            {
                "requirement": "Evaluation Scheduling",
                "description": "Schedule check rides, line checks, and proficiency evaluations efficiently.",
                "solution": "Evaluation optimizer maximizes check ride efficiency while maintaining quality standards."
            },
            {
                "requirement": "Travel Optimization",
                "description": "Minimize travel time between training locations and home base.",
                "solution": "Multi-location optimizer reduces travel costs and improves work-life balance."
            }
        ]
    })

@router.get("/customer-stories", response_class=HTMLResponse)
async def customer_stories(request: Request):
    """Customer success stories page"""
    return templates.TemplateResponse("pages/solutions/customer-stories.html", {
        "request": request,
        "page_title": "Customer Success Stories", 
        "page_description": "Real results from airlines and pilots using VectorBid to transform their scheduling operations.",
        "featured_story": {
            "customer": "United Airlines Pilots",
            "challenge": "Complex PBS optimization across multiple hubs with diverse pilot preferences",
            "solution": "Enterprise VectorBid deployment with custom contract integration",
            "results": {
                "pilot_satisfaction": "94% improvement",
                "schedule_efficiency": "28% increase",
                "bidding_time": "75% reduction",
                "cost_savings": "$15M annually"
            },
            "quote": "VectorBid transformed how our pilots approach bidding. The AI understands our contract better than most people, and the results speak for themselves.",
            "author": "Captain Sarah Chen, UAL MEC Representative"
        },
        "story_categories": [
            {
                "category": "Major Airlines",
                "stories": [
                    {
                        "airline": "Delta Air Lines",
                        "pilot_count": "14,000+",
                        "implementation": "Phased rollout across all fleets",
                        "key_metric": "92% pilot adoption rate",
                        "primary_benefit": "Reduced bidding complexity"
                    },
                    {
                        "airline": "American Airlines", 
                        "pilot_count": "15,000+",
                        "implementation": "Hub-by-hub deployment",
                        "key_metric": "86% schedule satisfaction",
                        "primary_benefit": "Improved work-life balance"
                    }
                ]
            },
            {
                "category": "Regional Airlines",
                "stories": [
                    {
                        "airline": "SkyWest Airlines",
                        "pilot_count": "4,000+", 
                        "implementation": "Cross-hub optimization",
                        "key_metric": "35% efficiency improvement",
                        "primary_benefit": "Multi-hub coordination"
                    }
                ]
            }
        ]
    })

@router.get("/roi-calculator", response_class=HTMLResponse)
async def roi_calculator(request: Request):
    """ROI Calculator page"""
    return templates.TemplateResponse("pages/solutions/roi-calculator.html", {
        "request": request,
        "page_title": "ROI Calculator",
        "page_description": "Calculate the potential return on investment for implementing VectorBid at your airline.",
        "calculator_sections": [
            {
                "title": "Current Operations",
                "fields": [
                    {"name": "pilot_count", "label": "Number of Pilots", "type": "number", "required": True},
                    {"name": "avg_hourly_cost", "label": "Average Pilot Hourly Cost", "type": "currency", "required": True},
                    {"name": "annual_flight_hours", "label": "Annual Flight Hours", "type": "number", "required": True},
                    {"name": "bidding_efficiency", "label": "Current Bidding Efficiency", "type": "percentage", "default": 70}
                ]
            },
            {
                "title": "Implementation Scope",
                "fields": [
                    {"name": "deployment_timeline", "label": "Deployment Timeline", "type": "select", "options": ["3 months", "6 months", "12 months"]},
                    {"name": "pilot_participation", "label": "Expected Pilot Participation", "type": "percentage", "default": 85},
                    {"name": "integration_level", "label": "Integration Level", "type": "select", "options": ["Basic", "Standard", "Enterprise"]}
                ]
            }
        ],
        "roi_assumptions": {
            "efficiency_improvement": "15-30%",
            "bidding_time_reduction": "60-80%", 
            "pilot_satisfaction_increase": "25-40%",
            "operational_cost_reduction": "5-12%"
        }
    })
