# TODO_MVP.md - Full Chatbot Motion Filing System

## 📊 Implementation Status
- **Start Date**: Week 1 (Phase 1 began)
- **Current Week**: Week 7 (Memory & Learning Complete!)
- **Progress**: 92% Complete (Phases 1-7 done, Phase 8 remaining)
- **Status**: ✅ Intelligent learning chatbot with full PDF pipeline!

## 🎯 Vision
Build a conversational AI assistant that guides users through filing California family court motions via natural language chat, remembers their information, and generates ready-to-file PDFs.

## Current Status (What's Done) ✅

### Infrastructure
- [x] GCP project configured with Cloud SQL, Cloud Run, Vertex AI
- [x] Database models (User, Profile, Motion, Documents, **Chat models**)
- [x] Authentication system with JWT
- [x] Basic frontend with React + Tailwind
- [x] LLM integration with Vertex AI (text rewriting only)
- [x] **WebSocket infrastructure for real-time chat**
- [x] **Chat API endpoints and service layer**

### Features Completed
- [x] Step-by-step form wizard for RFO/Response
- [x] User profile system with data persistence
- [x] San Diego violation filing forms integrated (8 forms)
- [x] PDF generation structure (partial)
- [x] Conditional questions based on answers
- [x] **Chat interface with message bubbles and quick replies**
- [x] **Basic intent recognition and entity extraction**
- [x] **Session state management for conversations**
- [x] **LLM-powered intent classification with Vertex AI**
- [x] **Dynamic question dependency graph system**
- [x] **Conversation-to-form field mapping service**
- [x] **Enhanced entity extraction using Gemini**

---

## Phase 1: Chat Infrastructure (Week 1-2) ✅ **COMPLETED**

### Backend ✅
- [x] Create ChatSession model (session_id, user_id, state, context)
- [x] Create ChatMessage model (message_id, content, sender, metadata)
- [x] Build WebSocket handler for real-time chat
- [x] Add session management service
- [x] Implement message history storage
- [x] Create conversation state machine
- [ ] Add Redis for session caching (deferred to optimization phase)

### Frontend ✅
- [x] Build ChatInterface component with message bubbles
- [x] Add typing indicators and message status
- [x] Implement auto-scroll and message grouping
- [x] Create quick reply buttons for common responses
- [ ] Add file upload for document attachments (deferred to Phase 5)
- [x] Build session recovery on page reload
- [x] Add chat minimize/maximize functionality

### API Endpoints ✅
- [x] POST /chat/sessions - Create new chat session
- [x] GET /chat/sessions/{id}/messages - Get message history
- [x] POST /chat/messages - Send message (WebSocket alternative)
- [x] PUT /chat/sessions/{id}/state - Update session state
- [x] GET /chat/sessions/active - Get user's active sessions
- [x] WebSocket /ws - Real-time chat connection

---

## Phase 2: Conversational AI Engine (Week 3-4) ✅ **COMPLETED**

### Intent Recognition ✅
- [x] Define intent taxonomy (FILE_MOTION, RESPOND, ASK_QUESTION, etc.)
- [x] Build intent classifier using LLM (Vertex AI integrated)
- [x] Create entity extraction for:
  - [x] Motion types (custody, support, violation)
  - [x] Party names and roles (LLM-enhanced)
  - [x] Dates and deadlines
  - [x] Dollar amounts
  - [x] Children information (LLM-enhanced)
- [x] Add confidence scoring for intents
- [x] Implement fallback handling for unclear intents

### Context Management ✅
- [x] Build context aggregator (profile + history + current session)
- [x] Create context injection for LLM prompts
- [x] Implement memory summarization for long conversations
- [x] Add reference resolution ("my ex" → respondent name)
- [x] Build fact extraction and validation

### Dynamic Question Generation ✅
- [x] Create question dependency graph (QuestionGraph service)
- [x] Build dynamic question selector based on:
  - [x] What's already known from profile
  - [x] Required fields for selected forms
  - [x] Previous answers in conversation
- [x] Implement smart skip logic (dependency-based)
- [x] Add clarification question generation

### Form Field Mapping ✅
- [x] Create conversation-to-form field mapper (FormFieldMapper service)
- [x] Map extracted entities to PDF form fields
- [x] Validate field completeness
- [x] Generate questions for missing fields
- [ ] Create follow-up question chains

---

## Phase 3: LLM Orchestration (Week 4) ✅ **COMPLETED**

### Conversation Management ✅
- [x] Expand LLMService for multi-turn conversation (llm_chat_service.py)
- [x] Create conversation prompt templates:
  - [x] Greeting and onboarding
  - [x] Information gathering
  - [x] Clarification requests
  - [x] Confirmation and summary
  - [x] Error recovery
- [x] Implement conversation flow controller
- [x] Add personality and tone consistency
- [x] Build context window management

### Response Generation ✅
- [x] Create response formatter with:
  - [x] Natural language generation (LLM-based)
  - [x] Legal term explanations
  - [x] Example providing
  - [x] Option suggestions (quick replies)
- [x] Add response validation
- [x] Implement length control
- [x] Add citation for legal requirements

### Form Mapping ✅
- [x] Build conversation-to-form data mapper (form_field_mapper.py)
- [x] Create validation for form completeness
- [x] Add missing information detector
- [x] Implement data transformation rules
- [x] Build review and confirmation flow

---

## Phase 4: Form Integration (Week 4) ✅ **COMPLETED**

### Motion Type Detection ✅
- [x] Build situation analyzer from conversation (chat_to_pdf_service.py)
- [x] Create form recommendation engine
- [x] Implement multi-form detection (when multiple forms needed)
- [x] Add track selection for violations (emergency/regular/contempt)
- [x] Build prerequisite checker

### Chat to PDF Pipeline ✅
- [x] Connect conversation data to PDF generation
- [x] Create motion records from chat sessions
- [x] Map extracted entities to form fields
- [x] Generate individual form PDFs
- [x] Create combined document packets

### Document Assembly
- [ ] Implement intelligent form ordering
- [ ] Create attachment detector
- [ ] Build exhibit reference system
- [ ] Add page numbering and formatting
- [ ] Generate table of contents

---

## Phase 5: Enhanced PDF Generation (Week 8) 📄 ✅ **COMPLETED**

### Form Filling ✅
- [x] Complete FL-300 field mappings
- [x] Complete FL-320 field mappings
- [x] Add all San Diego violation forms (8 forms total)
- [x] Implement multi-page text flow
- [x] Add checkbox and radio button handling
- [x] Create signature block placement

### Advanced Features ✅
- [x] Add barcode generation for filing
- [x] Implement form validation
- [x] Create draft watermarking
- [x] Add version tracking
- [x] Build diff comparison for edits

### Output Options ✅
- [x] Generate individual form PDFs
- [x] Create combined packet PDF
- [x] Add cover sheet generation
- [x] Build filing checklist
- [x] Generate service copies

---

## Phase 6: User Experience Polish (Week 9) ✨ 🔄 **IN PROGRESS**

### Chat Enhancements 🔄
- [ ] Add voice input option (SKIPPED per request)
- [x] Implement auto-save every message
- [x] Create conversation templates for common scenarios
- [x] Add progress indicator for long operations
- [x] Build help system with examples
- [ ] Add language detection and basic translation (SKIPPED per request)

### Guidance Features 🔄
- [ ] Create interactive tutorials
- [ ] Add contextual help bubbles
- [x] Build legal term glossary
- [x] Implement deadline reminders
- [x] Add filing tips and best practices
- [ ] Create video walkthroughs

### Error Handling
- [ ] Add graceful fallbacks for LLM failures
- [ ] Implement retry mechanisms
- [ ] Create error explanation system
- [ ] Add manual override options
- [ ] Build support ticket integration

---

## Phase 7: Memory and Learning (Week 10-11) 🧠 ✅ **COMPLETED**

### User Memory ✅
- [x] Build long-term memory storage
- [x] Create profile learning system
- [x] Implement preference detection
- [x] Add correction learning
- [x] Build pattern recognition for user needs

### System Improvements ✅
- [x] Add conversation analytics
- [ ] Implement A/B testing framework
- [x] Create feedback collection
- [x] Build quality scoring
- [ ] Add automated testing from conversations

### Knowledge Base
- [ ] Create FAQ system from common questions
- [ ] Build automatic documentation generation
- [ ] Add case law reference system
- [ ] Implement rule update notifications
- [ ] Create community knowledge sharing

---

## Phase 8: Production Readiness (Week 12) 🚀

### Security
- [ ] Add rate limiting per user
- [ ] Implement conversation encryption
- [ ] Create audit logging
- [ ] Add PII detection and masking
- [ ] Build compliance reporting

### Performance
- [ ] Add response caching
- [ ] Implement conversation pagination
- [ ] Create message compression
- [ ] Add CDN for static assets
- [ ] Build database indexing strategy

### Monitoring
- [ ] Add conversation metrics
- [ ] Create LLM usage tracking
- [ ] Implement error alerting
- [ ] Build performance dashboards
- [ ] Add user satisfaction tracking

### Deployment
- [ ] Create staging environment
- [ ] Build CI/CD pipeline
- [ ] Add feature flags
- [ ] Implement gradual rollout
- [ ] Create rollback procedures

---

## MVP Definition (Minimum Viable Chatbot)

### Core Features (Must Have)
1. **Chat Interface** - Basic conversation UI
2. **Intent Recognition** - Understand "I need custody modification"
3. **Dynamic Questions** - Ask only what's needed
4. **Form Selection** - Pick right forms automatically
5. **PDF Generation** - Create filled forms
6. **Session Memory** - Remember within conversation
7. **Profile Integration** - Use saved information

### Nice to Have (Phase 2)
- Voice input
- Multi-language support
- Video tutorials
- Community features
- Advanced analytics

### Out of Scope (Future)
- E-filing integration
- Attorney matching
- Court date scheduling
- Document scanning/OCR
- Payment processing

---

## Success Metrics

### User Experience
- [ ] Complete motion filing in < 30 minutes
- [ ] < 5% abandonment rate
- [ ] > 90% form accuracy
- [ ] < 3 clarification requests per session

### Technical
- [ ] < 2 second response time
- [ ] > 99% uptime
- [ ] < $0.10 per conversation cost
- [ ] > 95% intent recognition accuracy

### Business
- [ ] 100 successful filings in first month
- [ ] 4.5+ star user rating
- [ ] 50% return user rate
- [ ] 10% conversion to paid features

---

## Risk Mitigation

### High Risk Items
1. **LLM Hallucination** - Validate all generated content
2. **Legal Accuracy** - Attorney review of all templates
3. **Data Loss** - Auto-save every interaction
4. **Cost Overrun** - Token limits and caching
5. **User Privacy** - Encryption and compliance

### Mitigation Strategies
- Implement fallback to forms if chat fails
- Add human review option for complex cases
- Create test suite with edge cases
- Monitor LLM costs in real-time
- Regular security audits

---

## Timeline Summary

- **Weeks 1-2**: ✅ Chat Infrastructure **COMPLETED**
- **Weeks 3-4**: 🔄 AI Engine **IN PROGRESS**
- **Weeks 5-6**: LLM Orchestration
- **Week 7**: Form Intelligence
- **Week 8**: PDF Generation
- **Week 9**: UX Polish
- **Weeks 10-11**: Memory & Learning
- **Week 12**: Production Ready

**Total: 12 weeks to full chatbot system**

**Quick MVP: 4 weeks** (Basic chat + intent + forms) - **On Track!**

---

## Next Immediate Steps (Updated)

### ✅ Completed
1. [x] Choose architecture: Hybrid approach (chat guides, forms validate)
2. [x] Build WebSocket infrastructure
3. [x] Design and implement chat UI
4. [x] Create basic intent taxonomy
5. [x] Build session management system

### ✅ Week 3 Completed
1. [x] Integrate Vertex AI for better NLP understanding
2. [x] Expand intent classifier from patterns to LLM-based
3. [x] Build dynamic question dependency graph
4. [x] Create conversation-to-form field mapper
5. [x] Implement context injection for multi-turn conversations
6. [x] Build validation layer for extracted entities

### 🎯 Week 4 Goals (Next Priority)
1. [ ] Complete Phase 2 remaining items:
   - [ ] Memory summarization for long conversations
   - [ ] Reference resolution ("my ex" → actual name)
2. [ ] Start Phase 3: LLM Orchestration
   - [ ] Expand LLMService for multi-turn conversation
   - [ ] Create conversation prompt templates
   - [ ] Build context window management
3. [ ] Begin Phase 4: Form Integration
   - [ ] Connect chat flow to PDF generation
   - [ ] Test end-to-end: chat → form data → PDF
   - [ ] Create confirmation and summary flows

The goal: Transform the current form-based system into an intelligent conversational assistant that makes filing court documents as easy as having a conversation with a knowledgeable friend.insp