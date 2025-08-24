# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial MVP implementation
- FastAPI backend with authentication system
- Guided RFO intake flow with conditional questions
- Vertex AI integration for legal text rewriting
- PDF generation for official CA court forms (FL-300, FL-320)
- Basic web UI for testing the application flow
- PostgreSQL database schema for users, profiles, motions, and documents
- Cloud Run deployment configuration
- Pub/Sub integration for async processing
- GitHub Actions CI/CD pipeline

### Security
- JWT-based authentication
- Secret Manager integration for sensitive data
- Input validation and sanitization

## [0.1.0] - 2024-08-23

### Added
- Project initialization
- Basic repository structure
- Core documentation (README, LICENSE, CONTRIBUTING)
- GitHub repository setup with proper branching strategy
- Development, staging, and production environment configuration

[Unreleased]: https://github.com/sambrody62/california-motion-writer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sambrody62/california-motion-writer/releases/tag/v0.1.0