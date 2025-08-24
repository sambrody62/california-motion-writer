# California Motion Writer

Generate professional California family court motions with guided Q&A and AI assistance.

## 🎯 Overview

California Motion Writer helps self-represented litigants create properly formatted family law motions without expensive legal fees. The application provides:

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
git clone https://github.com/yourusername/california-motion-writer.git
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

1. Create a GCP project
2. Enable required APIs:
   - Cloud Run
   - Cloud SQL
   - Vertex AI
   - Secret Manager
   - Pub/Sub

3. Set up Cloud SQL instance:
```bash
gcloud sql instances create app-sql \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

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

## 🧪 Testing

Run tests:
```bash
pytest tests/
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

## 📞 Support

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/yourusername/california-motion-writer/issues)
- Documentation: [Wiki](https://github.com/yourusername/california-motion-writer/wiki)

---

Built with ❤️ to improve access to justice in California