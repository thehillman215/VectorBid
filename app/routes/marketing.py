from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Professional home page with comprehensive value proposition"""
    return templates.TemplateResponse("pages/home.html", {
        "request": request,
        "page_title": "AI-Powered Pilot Bidding Assistant",
        "page_description": "Transform your bidding strategy with AI that understands your contract and maximizes time at home.",
        "meta_keywords": "pilot bidding, PBS optimization, airline scheduling, AI assistant",
        "featured_testimonials": [
            {
                "quote": "VectorBid saved me 4 hours and got me the perfect schedule. The AI really understands pilot life.",
                "author": "Captain Jennifer L.",
                "company": "United Airlines",
                "avatar": "JL"
            },
            {
                "quote": "94% success rate speaks for itself. Game changer for commuters.",
                "author": "FO David K.", 
                "company": "United Airlines",
                "avatar": "DK"
            }
        ],
        "stats": {
            "pilots_served": "2,000+",
            "success_rate": "94%",
            "time_saved": "3.2 hours",
            "days_gained": "2.5"
        }
    })

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About VectorBid - company story and mission"""
    return templates.TemplateResponse("pages/about.html", {
        "request": request,
        "page_title": "About VectorBid",
        "page_description": "Learn about our mission to transform pilot bidding with AI-powered optimization.",
        "team": [
            {
                "name": "Sarah Chen",
                "role": "CEO & Co-Founder",
                "background": "Former United Airlines pilot with 15 years experience",
                "image": "/static/images/team/sarah-chen.jpg"
            },
            {
                "name": "Marcus Rodriguez",
                "role": "CTO & Co-Founder", 
                "background": "Ex-Google AI researcher specializing in optimization algorithms",
                "image": "/static/images/team/marcus-rodriguez.jpg"
            }
        ],
        "milestones": [
            {"year": "2022", "event": "Founded by airline pilots"},
            {"year": "2023", "event": "First AI model deployed"},
            {"year": "2024", "event": "2,000+ pilots using VectorBid"}
        ]
    })

@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Pricing plans with transparent comparison"""
    return templates.TemplateResponse("pages/pricing.html", {
        "request": request,
        "page_title": "Simple, Transparent Pricing",
        "page_description": "Choose the plan that fits your flying schedule. All plans include our core optimization engine.",
        "plans": [
            {
                "name": "Free Trial",
                "price": 0,
                "period": "7 days",
                "description": "Perfect for trying VectorBid",
                "features": [
                    "1 optimized bid",
                    "Basic preferences",
                    "Email support",
                    "All core features"
                ],
                "cta": "Start Free Trial",
                "cta_url": "/signup",
                "popular": False
            },
            {
                "name": "Professional",
                "price": 29,
                "period": "month",
                "description": "For active pilots who bid monthly",
                "features": [
                    "Unlimited optimized bids",
                    "Advanced pilot personas",
                    "Priority support",
                    "Schedule analytics",
                    "Export to all PBS systems",
                    "Mobile app access"
                ],
                "cta": "Get Started",
                "cta_url": "/signup?plan=pro",
                "popular": True
            },
            {
                "name": "Enterprise",
                "price": "Custom",
                "period": "contact us",
                "description": "For airlines and large pilot groups",
                "features": [
                    "Everything in Professional",
                    "Custom contract integration",
                    "Team analytics dashboard",
                    "Dedicated support",
                    "API access",
                    "White-label options"
                ],
                "cta": "Contact Sales",
                "cta_url": "/contact?type=enterprise",
                "popular": False
            }
        ],
        "faq": [
            {
                "question": "Can I cancel anytime?",
                "answer": "Yes, you can cancel your subscription at any time. No long-term contracts or cancellation fees."
            },
            {
                "question": "Is there a refund policy?",
                "answer": "We offer a 30-day money-back guarantee. If you're not satisfied, we'll refund your payment."
            },
            {
                "question": "Do you offer discounts for annual plans?",
                "answer": "Yes, annual plans receive a 20% discount. Contact us for details."
            }
        ]
    })

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact information and support options"""
    return templates.TemplateResponse("pages/contact.html", {
        "request": request,
        "page_title": "Contact VectorBid",
        "page_description": "Get in touch with our team. We're here to help you optimize your bidding strategy.",
        "contact_options": [
            {
                "type": "General Support",
                "email": "support@vectorbid.com",
                "description": "Questions about features, billing, or technical issues",
                "response_time": "< 4 hours"
            },
            {
                "type": "Sales Inquiries", 
                "email": "sales@vectorbid.com",
                "description": "Enterprise plans, custom integrations, partnerships",
                "response_time": "< 2 hours"
            },
            {
                "type": "Media & Press",
                "email": "press@vectorbid.com", 
                "description": "Press inquiries, interviews, company information",
                "response_time": "< 24 hours"
            }
        ],
        "office": {
            "address": "123 Aviation Way, Suite 500",
            "city": "San Francisco, CA 94102",
            "phone": "+1 (555) 123-4567"
        }
    })

@router.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    """Blog listing page with latest articles"""
    return templates.TemplateResponse("pages/blog/index.html", {
        "request": request,
        "page_title": "VectorBid Blog",
        "page_description": "Insights, tips, and updates from the VectorBid team and aviation industry experts.",
        "featured_post": {
            "title": "How AI is Revolutionizing Pilot Scheduling",
            "excerpt": "Explore the latest advances in artificial intelligence and their impact on airline operations and pilot quality of life.",
            "author": "Sarah Chen",
            "date": "2024-01-15",
            "image": "/static/images/blog/ai-scheduling.jpg",
            "url": "/blog/ai-revolutionizing-pilot-scheduling"
        },
        "recent_posts": [
            {
                "title": "5 Tips for Better PBS Bidding",
                "excerpt": "Proven strategies from experienced pilots to improve your schedule success rate.",
                "author": "Marcus Rodriguez",
                "date": "2024-01-10", 
                "category": "Tips",
                "url": "/blog/5-tips-better-pbs-bidding"
            },
            {
                "title": "Understanding Contract Rules in Modern PBS",
                "excerpt": "A deep dive into how collective bargaining agreements shape scheduling systems.",
                "author": "Captain Jennifer L.",
                "date": "2024-01-05",
                "category": "Education",
                "url": "/blog/understanding-contract-rules-pbs"
            }
        ]
    })

@router.get("/careers", response_class=HTMLResponse)
async def careers(request: Request):
    """Careers page with open positions"""
    return templates.TemplateResponse("pages/careers.html", {
        "request": request,
        "page_title": "Careers at VectorBid",
        "page_description": "Join our mission to transform aviation technology. Work with a team of pilots and engineers building the future of airline scheduling.",
        "open_positions": [
            {
                "title": "Senior AI Engineer",
                "department": "Engineering",
                "location": "San Francisco, CA / Remote",
                "type": "Full-time",
                "description": "Lead development of our AI optimization algorithms",
                "url": "/careers/senior-ai-engineer"
            },
            {
                "title": "Product Manager - Aviation",
                "department": "Product",
                "location": "San Francisco, CA",
                "type": "Full-time", 
                "description": "Drive product strategy for pilot-facing features",
                "url": "/careers/product-manager-aviation"
            }
        ],
        "benefits": [
            "Competitive salary and equity",
            "Comprehensive health benefits",
            "Unlimited PTO",
            "Remote-friendly culture",
            "Professional development budget",
            "Free lunch and snacks"
        ],
        "culture": {
            "mission": "To give every pilot the schedule they deserve",
            "values": ["Safety First", "Data-Driven", "Pilot-Focused", "Innovation"]
        }
    })

@router.get("/press", response_class=HTMLResponse)
async def press(request: Request):
    """Press page with media kit and news"""
    return templates.TemplateResponse("pages/press.html", {
        "request": request,
        "page_title": "Press & Media",
        "page_description": "Latest news, press releases, and media resources from VectorBid.",
        "recent_news": [
            {
                "title": "VectorBid Raises $5M Series A to Transform Pilot Scheduling",
                "date": "2024-01-20",
                "publication": "TechCrunch",
                "url": "/press/series-a-announcement"
            },
            {
                "title": "How AI is Solving the Pilot Scheduling Crisis",
                "date": "2024-01-15", 
                "publication": "Aviation Week",
                "url": "/press/aviation-week-feature"
            }
        ],
        "media_kit": {
            "logo_package": "/static/press/vectorbid-logos.zip",
            "fact_sheet": "/static/press/vectorbid-fact-sheet.pdf",
            "founder_photos": "/static/press/founder-photos.zip"
        }
    })

@router.get("/security", response_class=HTMLResponse) 
async def security(request: Request):
    """Security and compliance information"""
    return templates.TemplateResponse("pages/security.html", {
        "request": request,
        "page_title": "Security & Compliance",
        "page_description": "Learn about VectorBid's security practices and compliance certifications.",
        "certifications": [
            {"name": "SOC 2 Type II", "status": "Certified", "year": "2024"},
            {"name": "ISO 27001", "status": "Certified", "year": "2024"}, 
            {"name": "GDPR", "status": "Compliant", "year": "2024"}
        ],
        "security_features": [
            "End-to-end encryption",
            "Multi-factor authentication",
            "Regular security audits",
            "Data backup and recovery",
            "Access logging and monitoring"
        ]
    })

@router.get("/status", response_class=HTMLResponse)
async def status(request: Request):
    """System status page"""
    return templates.TemplateResponse("pages/status.html", {
        "request": request,
        "page_title": "System Status",
        "page_description": "Real-time status of VectorBid systems and services.",
        "overall_status": "Operational",
        "services": [
            {"name": "Web Application", "status": "Operational", "uptime": "99.9%"},
            {"name": "API", "status": "Operational", "uptime": "99.95%"},
            {"name": "Mobile App", "status": "Operational", "uptime": "99.8%"},
            {"name": "Database", "status": "Operational", "uptime": "99.99%"}
        ],
        "incidents": []
    })

@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Privacy policy"""
    return templates.TemplateResponse("pages/legal/privacy.html", {
        "request": request,
        "page_title": "Privacy Policy",
        "last_updated": "January 1, 2024"
    })

@router.get("/terms", response_class=HTMLResponse)  
async def terms(request: Request):
    """Terms of service"""
    return templates.TemplateResponse("pages/legal/terms.html", {
        "request": request,
        "page_title": "Terms of Service", 
        "last_updated": "January 1, 2024"
    })

@router.get("/cookies", response_class=HTMLResponse)
async def cookies(request: Request):
    """Cookie policy"""
    return templates.TemplateResponse("pages/legal/cookies.html", {
        "request": request,
        "page_title": "Cookie Policy",
        "last_updated": "January 1, 2024"
    })
