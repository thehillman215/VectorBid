#!/usr/bin/env python3
"""
save_landing.py - Saves the world-class landing page HTML
Run this first: python save_landing.py
Then run: python setup_world_class_landing.py
"""


def save_world_class_landing():
    """Save the complete world-class landing page HTML"""

    # The complete HTML content
    landing_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="VectorBid - AI-powered PBS bidding that saves pilots hours every month. Get your perfect schedule with 90% less effort.">
    <title>VectorBid - Never Lose Another PBS Bid | AI-Powered Schedule Optimization</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

    <!-- Custom Styles -->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .floating {
            animation: floating 3s ease-in-out infinite;
        }

        @keyframes floating {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .testimonial-card {
            background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
            border: 1px solid rgba(102, 126, 234, 0.1);
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .feature-card {
            transition: all 0.3s ease;
        }

        html {
            scroll-behavior: smooth;
        }
    </style>
</head>
<body class="bg-gray-50">

    <!-- Copy the FULL HTML content from the world-class landing page artifact here -->
    <!-- This is a placeholder - the actual content is much longer -->

    <div style="padding: 40px; text-align: center;">
        <h1 style="font-size: 48px; margin-bottom: 20px;">
            ⚠️ Please use the complete HTML
        </h1>
        <p style="font-size: 20px; color: #666;">
            This script needs to be updated with the full world-class landing page HTML.<br>
            Copy the entire content from the "VectorBid - World-Class Landing Page" artifact<br>
            and replace this placeholder content.
        </p>
        <p style="margin-top: 40px;">
            <a href="/start-trial" style="background: #7c3aed; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-size: 18px;">
                Get Started Anyway
            </a>
        </p>
    </div>

    <!-- FastAPI Smart Routing Integration for VectorBid -->
    <script>
        // Integration script is included here
        console.log('Landing page needs complete HTML content');
    </script>
</body>
</html>'''

    # Save the file
    with open('landing.html', 'w', encoding='utf-8') as f:
        f.write(landing_html)

    print("✅ Saved landing.html")
    print("\n⚠️  IMPORTANT: This is a placeholder!")
    print("\n📝 To get the complete world-class landing page:")
    print(
        "   1. Look for the artifact titled 'VectorBid - World-Class Landing Page'"
    )
    print("   2. Copy ALL the HTML from that artifact")
    print("   3. Replace the content in landing.html")
    print("\n   The complete version includes:")
    print("   • Hero section with floating dashboard preview")
    print("   • Trust indicators (2,500+ pilots, 15+ airlines)")
    print("   • Problem/Solution comparison")
    print("   • 6 feature cards with icons")
    print("   • 3-step how it works")
    print("   • Testimonials from pilots")
    print("   • Pricing tiers")
    print("   • FAQ section")
    print("   • Footer with links")
    print(
        "\nOnce you have the complete HTML, run: python setup_world_class_landing.py"
    )


if __name__ == "__main__":
    save_world_class_landing()
