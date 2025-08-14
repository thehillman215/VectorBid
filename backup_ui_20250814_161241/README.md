# VectorBid Modern UI System

## Overview
This is the modern UI system for VectorBid, featuring a clean, responsive design optimized for airline pilots.

## Structure
```
src/ui/
├── static/
│   ├── css/
│   │   └── vectorbid-modern.css    # Main stylesheet
│   └── js/
│       └── main.js                 # Core JavaScript
└── templates/
    ├── base.html                   # Base layout
    ├── index.html                  # Dashboard
    ├── results.html                # PBS results
    ├── admin_dashboard.html        # Admin panel
    └── components/                 # Reusable components
        ├── trip_card.html
        └── metric_card.html
```

## Features
- Clean, modern design with sky blue accent color
- Fully responsive (mobile, tablet, desktop)
- Drag-and-drop trip ranking
- Real-time form validation
- Toast notifications
- Modal system
- Smooth animations

## Customization
Edit CSS variables in `vectorbid-modern.css`:
```css
:root {
    --vb-primary: #0ea5e9;  /* Change primary color */
    --vb-font-family: 'Inter'; /* Change font */
}
```

## Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License
Copyright 2025 VectorBid. All rights reserved.
