# Overview

This is a Flask-based web application that helps airline pilots analyze and rank their trip bids based on personal preferences. The application allows pilots to upload their schedule files (PDF, CSV, or TXT format), input their preferences in natural language, and receive AI-powered rankings of available trips using OpenAI's GPT-4o model.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLAlchemy ORM with PostgreSQL (configured via environment variable)
- **Authentication**: Replit Auth integration with OAuth support
- **AI Integration**: OpenAI GPT-4o for intelligent trip ranking
- **File Processing**: Multi-format schedule parsing (PDF via PyMuPDF, CSV, TXT)

## Frontend Architecture
- **Template Engine**: Jinja2 templates
- **Styling**: Bootstrap with dark theme
- **Icons**: Font Awesome
- **Responsive Design**: Mobile-first approach

## Data Storage
- **Primary Database**: PostgreSQL with connection pooling
- **ORM**: SQLAlchemy with declarative base
- **Session Management**: Flask sessions with permanent sessions
- **File Storage**: Temporary file processing (files are parsed and discarded)

# Key Components

## Models
- **User**: Core user model for authentication (required for Replit Auth)
- **OAuth**: OAuth token storage for authentication sessions
- **ScheduleData**: Stores user's schedule analysis history including preferences, trip data, and AI rankings

## Authentication System
- **Replit Auth**: Integrated OAuth authentication
- **Session Management**: Persistent user sessions with browser session keys
- **Access Control**: Login-required decorators for protected routes

## File Processing Pipeline
- **Multi-format Support**: PDF (PyMuPDF), CSV, and TXT file parsing
- **Data Extraction**: Extracts trip ID, duration, dates, routing, credit hours, and weekend information
- **Error Handling**: Comprehensive error handling for file processing failures

## AI Ranking Service
- **OpenAI Integration**: Uses GPT-4o model for intelligent trip analysis
- **Natural Language Processing**: Processes user preferences in plain English
- **Contextual Analysis**: Considers factors like trip duration, layovers, weekends, and route preferences

# Data Flow

1. **User Authentication**: User logs in via Replit Auth
2. **File Upload**: User uploads schedule file and enters preferences
3. **File Processing**: Schedule parser extracts trip data based on file format
4. **AI Analysis**: OpenAI service ranks trips based on user preferences
5. **Results Display**: Ranked trips are presented to user with AI commentary
6. **Data Persistence**: Analysis results are saved to database for future reference

# External Dependencies

## Core Services
- **OpenAI API**: GPT-4o model for trip ranking (API key required)
- **Replit Auth**: Authentication service integration
- **PostgreSQL**: Database service (DATABASE_URL environment variable)

## Python Libraries
- **Flask**: Web framework and extensions (SQLAlchemy, Login)
- **PyMuPDF**: PDF processing capability
- **OpenAI**: Official OpenAI Python client
- **Flask-Dance**: OAuth integration for Replit Auth

## Frontend Dependencies
- **Bootstrap**: CSS framework with dark theme
- **Font Awesome**: Icon library
- **JavaScript**: Bootstrap components for interactive elements

# Deployment Strategy

## Environment Configuration
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: PostgreSQL connection string
- **OPENAI_API_KEY**: OpenAI API authentication

## Application Structure
- **Entry Point**: main.py runs the Flask application
- **Database Initialization**: Automatic table creation on startup
- **Proxy Configuration**: ProxyFix middleware for HTTPS URL generation
- **Debug Mode**: Enabled for development environment

## Key Architectural Decisions

### Database Design
- **Problem**: Need to store user data, OAuth tokens, and schedule analysis history
- **Solution**: SQLAlchemy ORM with PostgreSQL for robust data persistence
- **Rationale**: Provides strong consistency, complex querying capabilities, and integrates well with Flask

### Authentication Strategy
- **Problem**: Secure user authentication and session management
- **Solution**: Replit Auth integration with OAuth token storage
- **Rationale**: Leverages existing Replit infrastructure for seamless authentication

### AI Integration Approach
- **Problem**: Intelligent ranking of trips based on subjective preferences
- **Solution**: OpenAI GPT-4o with structured prompting for trip analysis
- **Rationale**: Natural language processing allows flexible preference input and provides human-like reasoning

### Enhanced File Processing Architecture (Updated: July 28, 2025)
- **Problem**: Support real airline bid packages with complex formatting from airlines like United
- **Solution**: Multi-layered parsing system with block detection, pattern matching, and robust fallbacks
- **Features**:
  - Block-based trip extraction for structured documents
  - Enhanced regex patterns for United Airlines and similar formats
  - Support for date ranges (12NOV-15NOV), routing codes (IAH-SFO-IAH), and time formats (18:30)
  - Multiple parsing strategies with intelligent fallbacks
  - Improved weekend detection and duration calculation
- **Rationale**: Real airline schedules require sophisticated parsing to handle varied formatting, multi-line data, and airline-specific conventions