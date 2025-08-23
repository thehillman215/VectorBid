#!/usr/bin/env python3
"""
VectorBid Phase 1 Foundation Testing Script
Tests all routes, assets, and core functionality
"""

import requests
import time
import sys

def test_foundation():
    print('🧪 VECTORBID FOUNDATION TESTING')
    print('=' * 60)
    
    base_url = 'http://localhost:8000'
    
    # Test server availability
    print('\n🚀 TESTING SERVER...')
    try:
        response = requests.get(base_url, timeout=5)
        print(f'✅ Server running at {base_url}')
        print(f'✅ Response time: {response.elapsed.total_seconds():.3f}s')
    except Exception as e:
        print(f'❌ Server not accessible: {e}')
        print('\n💡 Start server with:')
        print('   python -m uvicorn app.main:app --reload --port 8000')
        return False
    
    # Test all major routes
    routes = [
        ('/', 'Home Page'),
        ('/products', 'Products Overview'),
        ('/products/bid-optimizer', 'Bid Optimizer'),
        ('/solutions', 'Solutions Overview'),
        ('/solutions/regional', 'Regional Airlines'),
        ('/pricing', 'Pricing'),
        ('/about', 'About'),
        ('/contact', 'Contact')
    ]
    
    print(f'\n🌐 TESTING {len(routes)} ROUTES:')
    print('-' * 50)
    
    route_success = 0
    total_load_time = 0
    
    for route, name in routes:
        try:
            start_time = time.time()
            response = requests.get(f'{base_url}{route}', timeout=10)
            load_time = time.time() - start_time
            total_load_time += load_time
            
            if response.status_code == 200:
                # Check for key content
                content = response.text.lower()
                has_navigation = 'products' in content and 'solutions' in content
                has_vectorbid = 'vectorbid' in content
                has_proper_html = '<!doctype html>' in content
                
                quality_indicators = [has_navigation, has_vectorbid, has_proper_html]
                quality_score = sum(quality_indicators)
                
                status = '✅' if quality_score >= 2 else '⚠️'
                print(f'{status} {route:25} {name:20} ({load_time:.3f}s) Q:{quality_score}/3')
                
                if quality_score >= 2:
                    route_success += 1
            else:
                print(f'❌ {route:25} {name:20} (Status {response.status_code})')
                
        except Exception as e:
            print(f'❌ {route:25} {name:20} (Error: {str(e)[:30]})')
    
    # Test static assets
    assets = [
        '/static/css/design-system.css',
        '/static/css/components/buttons.css',
        '/static/css/components/cards.css',
        '/static/css/components/forms.css',
        '/static/css/components/navigation.css',
        '/static/js/navigation.js'
    ]
    
    print(f'\n🎨 TESTING {len(assets)} STATIC ASSETS:')
    print('-' * 50)
    
    asset_success = 0
    for asset in assets:
        try:
            response = requests.get(f'{base_url}{asset}', timeout=5)
            if response.status_code == 200:
                size_kb = len(response.content) / 1024
                print(f'✅ {asset:45} ({size_kb:.1f}KB)')
                asset_success += 1
            else:
                print(f'❌ {asset:45} (Status {response.status_code})')
        except Exception as e:
            print(f'❌ {asset:45} (Error)')
    
    # Performance analysis
    avg_load_time = total_load_time / len(routes) if routes else 0
    route_success_rate = (route_success / len(routes)) * 100
    asset_success_rate = (asset_success / len(assets)) * 100
    
    print(f'\n' + '=' * 60)
    print('📊 TEST RESULTS SUMMARY:')
    print('-' * 30)
    print(f'   Routes Working: {route_success}/{len(routes)} ({route_success_rate:.1f}%)')
    print(f'   Assets Working: {asset_success}/{len(assets)} ({asset_success_rate:.1f}%)')
    print(f'   Avg Load Time:  {avg_load_time:.3f}s')
    print(f'   Performance:    {"✅ Excellent" if avg_load_time < 0.5 else "⚠️ Needs optimization"}')
    
    # Overall assessment
    overall_success = (route_success_rate + asset_success_rate) / 2
    
    print(f'\n🎯 OVERALL SCORE: {overall_success:.1f}%')
    
    if overall_success >= 90:
        print('🎉 FOUNDATION TEST: EXCELLENT!')
        print('✅ Ready for production deployment')
        print('✅ All core systems operational')
    elif overall_success >= 80:
        print('👍 FOUNDATION TEST: GOOD!')
        print('✅ Most systems working well')
        print('⚠️ Minor issues to address')
    elif overall_success >= 70:
        print('⚠️ FOUNDATION TEST: NEEDS ATTENTION')
        print('❌ Several issues need fixing')
    else:
        print('❌ FOUNDATION TEST: FAILED')
        print('❌ Major issues detected')
    
    print(f'\n🌐 Manual Testing: {base_url}/')
    print('📱 Test responsive: Resize browser window')
    print('🧭 Test navigation: Click dropdown menus')
    print('🎨 Test interactions: Hover over buttons/cards')
    print('=' * 60)
    
    return overall_success >= 80

if __name__ == '__main__':
    success = test_foundation()
    sys.exit(0 if success else 1)
