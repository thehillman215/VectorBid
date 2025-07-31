# Overview

VectorBid is a Flask-based web application designed to help airline pilots analyze and rank trip bids. It allows pilots to upload schedule files, input natural language preferences, and receive AI-powered trip rankings utilizing OpenAI's GPT-4o model. The system now includes a comprehensive drag-and-drop trip preference ranking feature that allows pilots to visually reorder their trip preferences by dragging items up and down in their preferred priority order. The project aims to provide pilots with an intelligent tool for optimizing their monthly bid selections based on personal preferences, streamlining a complex and critical aspect of their profession.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: PostgreSQL via SQLAlchemy ORM (for core data) and Replit DB (for user profiles)
- **Authentication**: Replit Auth integration with OAuth support
- **AI Integration**: OpenAI GPT-4o for intelligent trip ranking
- **File Processing**: Multi-format schedule parsing (PDF via PyMuPDF, CSV, TXT)
- **Admin Features**: Secure administrative endpoint for uploading monthly bid packet PDFs with Bearer token authentication and PostgreSQL bytea storage.

## Frontend Architecture
- **Template Engine**: Jinja2 templates
- **Styling**: Bootstrap with dark theme, Font Awesome for icons
- **Responsive Design**: Mobile-first approach
- **Interactive Elements**: HTMX for dynamic content loading in the user onboarding wizard
- **Drag-and-Drop Interface**: Native HTML5 drag-and-drop API with visual feedback, real-time rank updates, and smooth animations for trip preference reordering.

## Data Storage
- **Primary Database**: PostgreSQL for main application data (e.g., ScheduleData, BidPacket).
- **User Profiles**: Replit DB for user profiles (airline, fleet, seat, base, seniority, personas, onboard status).
- **ORM**: SQLAlchemy for PostgreSQL interaction.

## Key Architectural Decisions
- **Database Design**: Uses PostgreSQL for robust, complex data and Replit DB for simplified user profile management.
- **Authentication Strategy**: Leverages Replit Auth for secure user authentication and session management.
- **AI Integration Approach**: Utilizes OpenAI GPT-4o for natural language processing and intelligent trip analysis, enabling flexible preference input and human-like reasoning.
- **Enhanced File Processing**: Implements a multi-layered parsing system with block detection and pattern matching for complex airline bid packages (e.g., United Airlines format), including deferred PyMuPDF import for robustness.
- **User Onboarding & Profile Management**: Features a streamlined 3-step HTMX-powered onboarding wizard to collect pilot preferences, including predefined and custom flying style personas, stored in Replit DB. This system automatically redirects new users to complete their profile before accessing main features.
- **Automated Bid Package Matching**: Eliminates manual bid package selection; the system automatically matches pilots to appropriate bid packages based on their profile attributes (month, airline, aircraft, base, position), converting profile preferences into AI-ready strings for analysis.

# External Dependencies

## Core Services
- **OpenAI API**: GPT-4o model for trip ranking.
- **Replit Auth**: Authentication service integration.
- **PostgreSQL**: Database service (configured via DATABASE_URL).
- **Replit DB**: Built-in key-value database for user profiles.

## Python Libraries
- **Flask**: Web framework and extensions (SQLAlchemy, Login).
- **PyMuPDF**: PDF processing (lazy loaded).
- **OpenAI**: Official OpenAI Python client.
- **Flask-Dance**: OAuth integration for Replit Auth.

## Frontend Dependencies
- **Bootstrap**: CSS framework.
- **Font Awesome**: Icon library.
- **HTMX**: For dynamic UI interactions, particularly in the onboarding wizard.