def generate_pbs_compliant_bid_layers(preferences_text, pilot_profile=None, trip_data=None):
    """Generate complete 20-layer PBS bidding strategy compliant with PBS 2.0 systems."""
    prefs = parse_pilot_preferences(preferences_text, pilot_profile)
    bid_layers = []
    
    # LAYERS 1-5: IDEAL CONDITIONS
    bid_layers.extend(create_ideal_layers_20(prefs))
    # LAYERS 6-10: GOOD CONDITIONS  
    bid_layers.extend(create_good_layers_20(prefs))
    # LAYERS 11-15: ACCEPTABLE CONDITIONS
    bid_layers.extend(create_acceptable_layers_20(prefs))
    # LAYERS 16-20: FALLBACK CONDITIONS
    bid_layers.extend(create_fallback_layers_20(prefs))
    
    return bid_layers

def parse_pilot_preferences(preferences_text, pilot_profile=None):
    """Parse pilot preferences into structured data."""
    prefs = {
        'weekends_off': False, 'no_early_am': False, 'no_redeyes': False,
        'home_every_night': False, 'max_days_off': False, 'short_trips': False,
        'long_trips': False, 'international_ok': False, 'commuter_friendly': False,
        'high_credit': False,
        'base': pilot_profile.get('base', 'DEN') if pilot_profile else 'DEN',
        'fleet': pilot_profile.get('fleet', ['737']) if pilot_profile else ['737'],
        'seniority': pilot_profile.get('seniority', 5000) if pilot_profile else 5000
    }
    
    if not preferences_text:
        return prefs
        
    text_lower = preferences_text.lower()
    
    prefs['weekends_off'] = any(phrase in text_lower for phrase in [
        'weekends off', 'weekend off', 'no weekends', 'avoid weekends'
    ])
    prefs['no_early_am'] = any(phrase in text_lower for phrase in [
        'no early', 'avoid early', 'late start', 'no morning'
    ])
    prefs['no_redeyes'] = any(phrase in text_lower for phrase in [
        'no redeye', 'avoid redeye', 'no red-eye', 'no overnight flying'
    ])
    prefs['max_days_off'] = any(phrase in text_lower for phrase in [
        'maximum days off', 'max days off', 'most days off', 'days off'
    ])
    prefs['home_every_night'] = any(phrase in text_lower for phrase in [
        'home every night', 'home daily', 'no overnights'
    ])
    prefs['commuter_friendly'] = any(phrase in text_lower for phrase in [
        'commuter', 'commute', 'easy commute', 'commutable'
    ])
    prefs['high_credit'] = any(phrase in text_lower for phrase in [
        'high credit', 'maximum credit', 'max credit', 'credit hours'
    ])
    prefs['international_ok'] = ('international' in text_lower and 
                                'avoid' not in text_lower and 'no' not in text_lower)
    
    return prefs

def create_ideal_layers_20(prefs):
    """Create layers 1-5: Ideal conditions."""
    layers = []
    
    # Layer 1: Perfect scenario
    filters_1 = []
    if prefs['weekends_off']:
        filters_1.extend([
            "AWARD IF TRIP.DAYS_OFF_AFTER >= 2 AND DAY(TRIP.END_DATE + 1) = SAT",
            "AVOID IF TRIP.DUTY_DAYS OVERLAP (SAT,SUN)"
        ])
    if prefs['no_early_am']:
        filters_1.extend([
            "AWARD IF TRIP.FIRST_DEPARTURE_TIME >= 1000",
            "AVOID IF TRIP.ANY_DEPARTURE_TIME < 0800"
        ])
    if prefs['max_days_off']:
        filters_1.append("AWARD IF TRIP.TOTAL_DAYS_OFF >= 15")
    if prefs['no_redeyes']:
        filters_1.append("AVOID IF TRIP.ANY_DEPARTURE_TIME BETWEEN 2200 AND 0559")
    
    if prefs['fleet']:
        filters_1.append(f"AWARD IF TRIP.EQUIPMENT IN ({','.join(prefs['fleet'])})")
    filters_1.append(f"AWARD IF TRIP.ORIGIN = {prefs['base']}")
    
    if not filters_1:
        filters_1 = ["AWARD IF TRIP.CREDIT_HOURS >= 5.0 PER DAY", f"AWARD IF TRIP.ORIGIN = {prefs['base']}"]
    
    layers.append({
        'layer': 1,
        'description': build_description(prefs, 'perfect'),
        'strategy': 'All preferences exactly met',
        'probability': 'Low (5-10%) - Perfect scenario',
        'filters': filters_1,
        'category': 'IDEAL'
    })
    
    # Layer 2: Nearly perfect
    filters_2 = filters_1.copy()
    if prefs['no_early_am']:
        filters_2 = [f for f in filters_2 if "FIRST_DEPARTURE_TIME >= 1000" not in f]
        filters_2.append("AWARD IF TRIP.FIRST_DEPARTURE_TIME >= 0900")
    
    layers.append({
        'layer': 2,
        'description': build_description(prefs, 'nearly_perfect'),
        'strategy': 'Minor timing compromise',
        'probability': 'Low (10-15%)',
        'filters': filters_2,
        'category': 'IDEAL'
    })
    
    # Layer 3: Base optimized
    filters_3 = [
        f"AWARD IF TRIP.ORIGIN = {prefs['base']}",
        f"AWARD IF TRIP.DESTINATION = {prefs['base']}",
        "AWARD IF TRIP.DEADHEAD_LEGS = 0",
        "AWARD IF TRIP.CREDIT_HOURS >= 4.5 PER DAY"
    ]
    if prefs['weekends_off']:
        filters_3.append("AWARD IF TRIP.WEEKEND_DUTY_DAYS <= 1")
    
    layers.append({
        'layer': 3,
        'description': f"High-quality trips from {prefs['base']} base",
        'strategy': 'Base optimization with preferences',
        'probability': 'Low-Medium (15-20%)',
        'filters': filters_3,
        'category': 'IDEAL'
    })
    
    # Layer 4: Equipment focus
    filters_4 = [
        "AWARD IF TRIP.CREDIT_HOURS >= 5.0 PER DAY",
        "AWARD IF TRIP.DUTY_PERIOD <= 12_HOURS",
        "AWARD IF TRIP.EFFICIENCY_RATING >= 80"
    ]
    if prefs['fleet']:
        filters_4.append(f"AWARD IF TRIP.EQUIPMENT IN ({','.join(prefs['fleet'])})")
    
    layers.append({
        'layer': 4,
        'description': "Premium trips with preferred equipment",
        'strategy': 'Equipment and productivity focus',
        'probability': 'Low-Medium (18-25%)',
        'filters': filters_4,
        'category': 'IDEAL'
    })
    
    # Layer 5: Route preferences
    filters_5 = [
        "AWARD IF TRIP.LAYOVER_QUALITY >= ADEQUATE",
        "AWARD IF TRIP.CREDIT_HOURS >= 4.8 PER DAY"
    ]
    if prefs['international_ok']:
        filters_5.extend([
            "AWARD IF TRIP.ROUTE_TYPE = INTERNATIONAL",
            "AWARD IF TRIP.LAYOVER_HOURS >= 18"
        ])
    else:
        filters_5.append("AWARD IF TRIP.ROUTE_TYPE = DOMESTIC_PREMIUM")
    
    layers.append({
        'layer': 5,
        'description': "Preferred routes with good quality",
        'strategy': 'Route optimization',
        'probability': 'Medium (20-30%)',
        'filters': filters_5,
        'category': 'IDEAL'
    })
    
    return layers

def create_good_layers_20(prefs):
    """Create layers 6-10: Good conditions with compromises."""
    layers = []
    
    # Layer 6-10 implementation
    for i in range(6, 11):
        if i == 6:
            filters = ["AWARD IF TRIP.CREDIT_HOURS >= 4.0 PER DAY", "AWARD IF TRIP.LEGAL_REST_COMPLIANCE = TRUE"]
            if prefs['weekends_off']:
                filters.append("AWARD IF TRIP.WEEKEND_DUTY_DAYS <= 1")
            desc = "Good schedule with one major compromise"
            strategy = 'One compromise for better probability'
            prob = 'Medium (25-35%)'
        elif i == 7:
            filters = ["AWARD IF TRIP.CREDIT_HOURS >= 4.8 PER DAY", "AWARD IF TRIP.DUTY_PERIOD <= 13_HOURS"]
            desc = "High-credit efficient trips"
            strategy = 'Productivity optimization'
            prob = 'Medium (30-40%)'
        elif i == 8:
            filters = [f"AWARD IF TRIP.STARTS_AT_BASE = {prefs['base']}", "AWARD IF TRIP.DEADHEAD_LEGS <= 1"]
            desc = f"Commuter-optimized from {prefs['base']}"
            strategy = 'Commute optimization'
            prob = 'Medium-High (35-45%)'
        elif i == 9:
            filters = ["AWARD IF TRIP.CREDIT_HOURS >= 4.2 PER DAY", "AWARD IF TRIP.LAYOVER_QUALITY >= ADEQUATE"]
            desc = "Quality trips with multiple minor compromises"
            strategy = 'Multiple small compromises'
            prob = 'Medium-High (40-50%)'
        else:  # i == 10
            filters = ["AWARD IF TRIP.CREDIT_HOURS >= 4.5 PER DAY", "AVOID IF TRIP.DUTY_PERIOD > 14_HOURS"]
            desc = "Good credit with relaxed preferences"
            strategy = 'Credit focus with flexibility'
            prob = 'High (45-55%)'
        
        layers.append({
            'layer': i,
            'description': desc,
            'strategy': strategy,
            'probability': prob,
            'filters': filters,
            'category': 'GOOD'
        })
    
    return layers

def create_acceptable_layers_20(prefs):
    """Create layers 11-15: Acceptable conditions."""
    layers = []
    
    for i in range(11, 16):
        if i == 11:
            filters = ["AWARD IF TRIP.LEGAL_REST_COMPLIANCE = TRUE"]
            if prefs['weekends_off']:
                filters.append("AWARD IF TRIP.WEEKEND_DUTY_DAYS <= 1")
            desc = f"Focus on: {'weekends_off' if prefs['weekends_off'] else 'basic quality'}"
            strategy = 'Priority focus on top preferences'
            prob = 'High (50-60%)'
        elif i == 12:
            filters = ["AWARD IF TRIP.LEGAL_REST_COMPLIANCE = TRUE", "AVOID IF TRIP.DUTY_PERIOD > 14_HOURS"]
            desc = "Single focus with safety minimums"
            strategy = 'Single priority with safety'
            prob = 'High (55-65%)'
        elif i == 13:
            filters = ["AWARD IF TRIP.TOTAL_DUTY_TIME <= 100_HOURS", "AVOID IF TRIP.CONSECUTIVE_DUTY_DAYS > 6"]
            desc = "Basic quality of life protection"
            strategy = 'Minimum QOL standards'
            prob = 'High (60-70%)'
        elif i == 14:
            filters = [f"AWARD IF TRIP.ORIGIN = {prefs['base']}", "AWARD IF TRIP.CREDIT_HOURS >= 4.0 PER DAY"]
            desc = f"Credit optimization from {prefs['base']} base"
            strategy = 'Base and credit focus'
            prob = 'High (65-75%)'
        else:  # i == 15
            filters = ["AWARD IF TRIP.EQUIPMENT_QUALIFIED = TRUE", "AWARD IF TRIP.LEGAL_COMPLIANCE = TRUE"]
            desc = "Preferred equipment with broad acceptance"
            strategy = 'Equipment focus with flexibility'
            prob = 'Very High (70-80%)'
        
        layers.append({
            'layer': i,
            'description': desc,
            'strategy': strategy,
            'probability': prob,
            'filters': filters,
            'category': 'ACCEPTABLE'
        })
    
    return layers

def create_fallback_layers_20(prefs):
    """Create layers 16-20: Fallback conditions."""
    layers = []
    
    fallback_configs = [
        (16, "Any reasonable quality trip", "Quality with minimal restrictions", "Very High (75-85%)", 
         ["AWARD IF TRIP.REASONABLE_QUALITY = TRUE", "AVOID IF TRIP.DUTY_PERIOD > 15_HOURS"]),
        (17, "Legal compliance with safety standards", "Safety and legal minimums", "Very High (80-90%)", 
         ["AWARD IF TRIP.FAR_117_COMPLIANT = TRUE", "AVOID IF TRIP.DUTY_PERIOD > 16_HOURS"]),
        (18, "Any trip on qualified equipment", "Equipment qualification only", "Very High (85-93%)", 
         ["AWARD IF TRIP.EQUIPMENT_QUALIFIED = TRUE"]),
        (19, "Any contractually legal assignment", "Contract compliance only", "Very High (90-97%)", 
         ["AWARD IF TRIP.CONTRACTUALLY_LEGAL = TRUE"]),
        (20, "Final safety net - any legal assignment", "Guarantee assignment", "Maximum (95-99%)", 
         ["AWARD ANY_LEGAL_TRIP"])
    ]
    
    for layer_num, desc, strategy, prob, filters in fallback_configs:
        layers.append({
            'layer': layer_num,
            'description': desc,
            'strategy': strategy,
            'probability': prob,
            'filters': filters,
            'category': 'FALLBACK'
        })
    
    return layers

def build_description(prefs, scenario_type):
    """Build human-readable description."""
    parts = []
    
    if scenario_type == 'perfect':
        desc = "Perfect schedule: "
        if prefs['weekends_off']:
            parts.append("weekends free")
        if prefs['no_early_am']:
            parts.append("no early AMs")
        if prefs['max_days_off']:
            parts.append("maximum days off")
        if prefs['no_redeyes']:
            parts.append("no red-eyes")
    elif scenario_type == 'nearly_perfect':
        desc = "Nearly perfect: "
        if prefs['weekends_off']:
            parts.append("weekends free")
        if prefs['no_early_am']:
            parts.append("minimal early AMs (after 9am)")
        if prefs['max_days_off']:
            parts.append("excellent days off")
    
    return (desc + " + ".join(parts)) if parts else "Quality schedule with preferences"
