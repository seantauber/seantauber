# MVP Development Issues

## Core Infrastructure

### Issue #1: Database Setup
**Priority: High**
**Estimated Time: 2 days**
**Labels: infrastructure, database**

Set up the core SQLite database structure for the MVP.

**Tasks:**
- [x] Create SQLite database with core tables:
  - newsletters
  - repositories
  - topics
  - repository_categories
- [x] Implement basic CRUD operations
- [x] Add database migration system
- [x] Write unit tests for database operations
  - [x] Basic connection tests
  - [x] Transaction tests
  - [x] Error handling tests
  - [x] Database validation tests

**Acceptance Criteria:**
- [x] All core tables created and validated
- [x] CRUD operations working and tested
- [x] Migration system in place
- [x] Test coverage > 90%

### Issue #2: Gmail Integration
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, external-api**

Set up Gmail integration using Embedchain.

**Tasks:**
- [x] Install and configure embedchain[gmail]
- [x] Configure Gmail loader
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Gmail loader working
- [x] Integration tested
- [x] Test coverage > 90%

### Issue #3: Newsletter Processing
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, external-api**

Implement newsletter processing pipeline.

**Tasks:**
- [x] Set up Gmail API credentials
- [x] Configure Embedchain Gmail loader
- [x] Implement newsletter filtering by label
- [x] Create content extraction pipeline
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Successfully connects to Gmail API
- [x] Correctly filters newsletters
- [x] Handles API errors gracefully
- [x] Test coverage > 90%

## Core Components & Agents

### Issue #4: Newsletter Monitor Component
**Priority: High**
**Estimated Time: 2 days**
**Labels: core-functionality**

Implement the Newsletter Monitor as a deterministic pipeline component (not agent-based).

**Tasks:**
- [x] Create basic component structure
- [x] Implement newsletter polling using Gmail client
- [x] Add content validation and truncation
- [x] Create processing queue
- [x] Write unit tests
- [x] Implement deterministic pipeline stages:
  - [x] fetch_newsletters()
  - [x] process_newsletters()
  - [x] run() pipeline coordinator

**Acceptance Criteria:**
- [x] Component successfully polls for newsletters
- [x] Validates and truncates newsletter content
- [x] Processes content in batches
- [x] Handles errors with proper recovery
- [x] Test coverage > 90%

**Implementation Notes:**
- Component uses deterministic pipeline approach instead of agent-based
- Content processing happens in the pipeline without LLM involvement
- Only metadata/stats passed to orchestrator for decision making
- Proper content truncation to stay within token limits

### Issue #5: Content Extractor Agent
**Priority: High**
**Estimated Time: 3 days**
**Labels: agent, core-functionality**

Implement the Content Extractor agent with LLM-based analysis.

**Tasks:**
- [x] Create repository link extraction
- [x] Add metadata collection
- [x] Create storage integration
- [x] Write unit tests
- [x] Add LLM-based repository analysis:
  - [x] Fetch and process README content
  - [x] Generate structured repository summaries
  - [x] Categorize repositories using taxonomy
  - [x] Store summaries and categories
- [x] Implement data migration:
  - [x] Create migration script for existing repositories
  - [x] Add README content to existing entries
  - [x] Generate summaries for existing repositories
  - [x] Update categories

**Acceptance Criteria:**
- [x] Successfully extracts GitHub links
- [x] Collects repository metadata
- [x] Generates meaningful repository summaries
- [x] Correctly categorizes repositories
- [x] Successfully migrates existing data
- [x] Test coverage > 90%

### Issue #6: Repository Curator Agent
**Priority: High**
**Estimated Time: 2 days**
**Labels: agent, core-functionality**

Implement the Repository Curator agent.

**Tasks:**
- [x] Create repository metadata management
- [x] Add duplicate detection
- [x] Create storage integration
- [x] Write unit tests

**Acceptance Criteria:**
- [x] Manages repository metadata
- [x] Detects duplicates
- [x] Test coverage > 90%

### Issue #7: README Generator Agent
**Priority: High**
**Estimated Time: 2 days**
**Labels: agent, core-functionality**

Implement the README Generator agent.

**Tasks:**
- [x] Create markdown generation
- [x] Implement category organization
- [x] Add repository listing logic
- [x] Create GitHub integration
- [x] Write unit tests

**Acceptance Criteria:**
- [x] Generates valid markdown
- [x] Organizes categories correctly
- [x] Lists repositories properly
- [x] Test coverage > 90%

## Integration & Deployment

### Issue #8: Agent Orchestration
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, core-functionality**

Implement the orchestration system for agent coordination.

**Tasks:**
- [x] Create hybrid orchestration system:
  - [x] Deterministic components for known workflows
  - [x] Agent-based decision making for complex tasks
- [x] Implement processing pipeline
- [x] Create system state management
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Components and agents communicate properly
- [x] Pipeline processes correctly
- [x] Efficient token usage in LLM interactions
- [x] Test coverage > 90%

**Implementation Notes:**
- Use deterministic pipelines for predictable workflows
- Reserve agent-based decisions for complex tasks
- Minimize LLM token usage by keeping content in pipeline
- Pass only necessary metadata to LLM for decisions

### Issue #9: Testing & Documentation
**Priority: High**
**Estimated Time: 3 days**
**Labels: testing, documentation**

Complete testing suite and documentation for MVP, with focus on README updating system.

**Tasks:**
- [x] Create comprehensive integration tests for README updating system
  - [x] Test agent interactions
  - [x] Test data flow through pipeline
  - [x] Test error handling and recovery
- [x] Implement end-to-end tests for complete workflow
  - [x] Test newsletter processing to README generation
  - [x] Test repository categorization
  - [x] Test topic analysis and organization
- [x] Add setup instructions
- [x] Create troubleshooting guide
- [x] Review and update all tests

**Acceptance Criteria:**
- [x] Integration tests passing for README system
- [x] End-to-end tests passing for complete workflow
- [x] Documentation complete and verified
- [x] Setup instructions tested
- [x] Overall test coverage > 90%
- [x] README updates working properly in test environment

### Issue #10: Component Testing Implementation
**Priority: High**
**Estimated Time: 5 days**
**Labels: testing, core-functionality**

Implement independent tests for each pipeline component to verify correct functionality with live external dependencies.

**Tasks:**
1. Gmail/Newsletter Component Test ✅
   - [x] Test with live Gmail account
   - [x] Verify actual newsletter fetching
   - [x] Confirm real-time database storage
   - [x] Test with new incoming newsletters
   - [x] Verify historical tracking works
   - [x] Evidence collection:
     - [x] Show fetched newsletters in database
     - [x] Demonstrate duplicate prevention
     - [x] Log processing timestamps
   - [x] Add human-readable verification:
     - [x] Display newsletter content samples
     - [x] Show processing statistics
     - [x] Present timeline information
     - [x] Summarize ingestion results

2. Content Extraction Component Test ✅
   - [x] Process actual newsletter content
   - [x] Extract live GitHub repository links
   - [x] Make real API calls for repository metadata
   - [x] Store in production database
   - [x] Generate repository summaries with LLM
   - [x] Categorize repositories using taxonomy
   - [x] Add human-readable verification:
     - [x] Show extracted links vs source content
     - [x] Display GitHub API responses
     - [x] Show metadata collection results
     - [x] Display repository summaries and categories
     - [x] Summarize processing statistics

3. Repository Curation Component Test
   - [x] Test with live repository data
   - [x] Make real GitHub API calls
   - [x] Verify duplicate detection
   - [x] Update actual metadata
   - [x] Add human-readable verification:
     - [x] Show metadata updates
     - [x] Display duplicate detection results
     - [x] Summarize curation decisions

4. README Generation Component Test
   - [ ] Use live database content
   - [ ] Generate actual markdown
   - [ ] Test with real categories
   - [ ] Create production README
   - [ ] Add human-readable verification:
     - [ ] Show category organization
     - [ ] Display repository grouping
     - [ ] Present markdown formatting
     - [ ] Summarize generation process

**Acceptance Criteria:**
- Each component successfully processes live data
- External API calls (Gmail, GitHub, LLM) work correctly
- Data flows properly through production database
- Clear evidence of successful processing
- Proper error handling with live services
- Documentation of test procedures
- Reproducible test process
- Human-readable verification output for all components

**Implementation Notes:**
- Use production API credentials
- Test with real-world data volumes
- Monitor API rate limits
- Track processing times
- Log all external service interactions
- Document any service-specific limitations
- Maintain error recovery procedures
- Implement clear, formatted output for verification

### Issue #11: GitHub Actions Setup
**Priority: High**
**Estimated Time: 1 day**
**Labels: deployment, automation**

Set up GitHub Actions for automated execution. Requires Issue #10 to be completed first.

**Tasks:**
- [ ] Create GitHub Actions workflow
- [ ] Implement scheduled execution
- [ ] Create deployment configuration
- [ ] Write workflow tests

**Acceptance Criteria:**
- All integration and end-to-end tests passing in CI environment
- Workflow runs on schedule
- Executes successfully
- Configuration is secure

## Development Guidelines

1. Create feature branch for each issue
2. Follow Python best practices and PEP 8
3. Write tests before implementation
4. Update documentation as you go
5. Regular code reviews required
6. Consider token usage and LLM interaction efficiency
7. Use deterministic pipelines where workflow is predictable
8. Reserve agent-based approaches for complex decision making

## Success Metrics

- All tests passing
- Code coverage > 90%
- Documentation complete
- GitHub Actions workflow successful
- README updates working properly
- Efficient token usage in LLM interactions

## Implementation Strategy

1. Phase 1: Infrastructure Updates ✅
- [x] Add new database fields
- [x] Create migration scripts

2. Phase 2: Content Enhancement ✅
- [x] Fetch README content
- [x] Generate repository summaries
- [x] Categorize repositories

3. Phase 3: Validation
- [ ] Test all components
- [ ] Verify data integrity
- [ ] Document changes
