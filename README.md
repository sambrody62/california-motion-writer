# Family Court Helper

Generate professional California family court motions with guided Q&A and AI assistance.

## 🎯 Overview

Family Court Helper helps self-represented litigants create properly formatted family law motions without expensive legal fees. The application provides:

- **Guided intake process** with smart conditional questions
- **AI-powered rewriting** to convert plain language into formal legal writing
- **Official court forms** (FL-300, FL-320) filled programmatically
- **Cloud-based architecture** on Google Cloud Platform

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Docker (for deployment)
- GCP Project with billing enabled

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/sambrody/california-motion-writer.git
cd california-motion-writer
```

2. Run the local development setup:
```bash
./run_local.sh
```

3. Access the application:
- Web UI: http://localhost:8080
- API Docs: http://localhost:8080/docs

### Download Court Forms

Before generating PDFs, download the official California court forms:

1. Visit https://www.courts.ca.gov/forms.htm
2. Download these forms as fillable PDFs:
   - FL-300 (Request for Order)
   - FL-320 (Responsive Declaration)
   - FL-311 (Child Custody Attachment)
   - FL-150 (Income and Expense Declaration)
3. Place them in the `forms/` directory

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│  FastAPI    │────▶│  Cloud SQL  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Vertex AI  │
                    └─────────────┘
```

### Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (Cloud SQL)
- **AI/ML**: Vertex AI (Gemini 1.5)
- **PDF Generation**: ReportLab + PyPDF2
- **Hosting**: Cloud Run
- **Message Queue**: Pub/Sub

## 📁 Project Structure

```
california-motion-writer/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core configuration
│   ├── models/        # Database models
│   └── services/      # Business logic
├── forms/             # Court form PDFs (not in repo)
├── static/            # Frontend files
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container configuration
├── deploy.sh          # Deployment script
└── schema.sql         # Database schema
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for local development:

```env
PROJECT_ID=california-motion-writer
ENVIRONMENT=development
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your-secret-key
```

### GCP Setup

#### Prerequisites

1. **Create a GCP project**
```bash
gcloud projects create california-motion-writer --name="California Motion Writer"
gcloud config set project california-motion-writer
```

2. **Enable billing** (required for Cloud SQL and Vertex AI)
```bash
gcloud beta billing accounts list
gcloud beta billing projects link california-motion-writer --billing-account=YOUR_BILLING_ID
```

3. **Enable required APIs**:
```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  cloudbuild.googleapis.com
```

4. **Set up service account**:
```bash
gcloud iam service-accounts create motion-writer-sa \
  --display-name="Motion Writer Service Account"

gcloud projects add-iam-policy-binding california-motion-writer \
  --member="serviceAccount:motion-writer-sa@california-motion-writer.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding california-motion-writer \
  --member="serviceAccount:motion-writer-sa@california-motion-writer.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding california-motion-writer \
  --member="serviceAccount:motion-writer-sa@california-motion-writer.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

5. **Set up Cloud SQL instance**:
```bash
gcloud sql instances create app-sql \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --network=default
```

#### Estimated Monthly Costs (Development)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Cloud Run | 1M requests | ~$50 |
| Cloud SQL | db-f1-micro | ~$10 |
| Vertex AI | 10K API calls | ~$30 |
| Cloud Storage | 10GB | ~$2 |
| **Total** | | **~$92/month** |

*Note: Costs may vary based on usage. Set up billing alerts to monitor spending.*

## 🚢 Deployment

Deploy to Cloud Run:

```bash
./deploy.sh
```

This script will:
1. Build the Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Configure environment variables

## 📚 API Documentation

### Key Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/motions` - Create new motion
- `GET /api/v1/intake/rfo/steps` - Get intake questions
- `POST /api/v1/llm/process-motion` - Process with AI
- `POST /api/v1/documents/generate-pdf` - Generate PDF

Full API documentation available at `/docs` when running.

## 🔒 Security

### Authentication & Authorization
- **Google Identity Platform** for user authentication
- **JWT tokens** with 1-hour expiry and refresh tokens
- **Role-based access control**: user, admin, attorney roles
- **Session management** with secure HTTP-only cookies

### Data Protection
- **Encryption at rest**: Cloud SQL automatic encryption
- **Encryption in transit**: TLS 1.3 for all connections
- **PII handling**: Compliance with California Consumer Privacy Act (CCPA)
- **Secrets management**: Google Secret Manager for sensitive data
- **Input validation**: SQL injection and XSS protection

### Security Best Practices
- Regular security updates via Dependabot
- Content Security Policy (CSP) headers
- Rate limiting on API endpoints
- Audit logging for all data access
- No storage of credit card information

## 🧪 Testing

Run tests:
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run in verbose mode
pytest tests/ -v
```

## 📈 Roadmap

### Phase 1 (MVP) ✅
- [x] Basic RFO and Response motions
- [x] User authentication
- [x] Guided Q&A intake
- [x] AI rewriting
- [x] PDF generation

### Phase 2 (Enhancement)
- [ ] Additional motion types
- [ ] E-filing integration
- [ ] Document storage
- [ ] Multi-language support
- [ ] Mobile app

### Phase 3 (Scale)
- [ ] Advanced AI features
- [ ] Court deadline tracking
- [ ] Collaboration features
- [ ] Attorney marketplace

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## ⚖️ Legal Disclaimer

This application provides document preparation assistance only, NOT legal advice. Users should:
- Review all generated documents carefully
- Consult with a licensed attorney for legal advice
- Verify current court rules and requirements

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- California Judicial Council for form templates
- Google Cloud Platform for infrastructure
- FastAPI and Python communities

## 🔧 Troubleshooting

### Common Issues

#### Local Development

**Problem**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Add project root to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Problem**: Database connection errors
- **Solution**: Check `.env` file and ensure database is running:
```bash
# For local SQLite
touch test.db

# For Cloud SQL proxy
gcloud sql connect app-sql --user=appuser
```

#### Deployment Issues

**Problem**: Cloud Run deployment fails
- **Solution**: Check service account permissions:
```bash
gcloud run services describe motion-api --region=us-central1
gcloud run services logs read motion-api --region=us-central1
```

**Problem**: Vertex AI API errors
- **Solution**: Verify API is enabled and quotas:
```bash
gcloud services list --enabled | grep aiplatform
gcloud compute project-info describe --project=california-motion-writer
```

### Getting Help

## 📞 Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/sambrody/california-motion-writer/issues)
- Documentation: [Wiki](https://github.com/sambrody/california-motion-writer/wiki)
- Email: support@californiamotion.writer (coming soon)

---

Built with ❤️ to improve access to justice in California