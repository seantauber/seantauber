# MVP Development Issues

## Core Infrastructure

### Issue #1: Database Setup
**Priority: High**
**Estimated Time: 2 days**
**Labels: infrastructure, database**

Set up the core SQLite database structure for the MVP.

**Tasks:**
- [x] Create SQLite database with core tables:
  - newsletters (with vector_id reference)
  - repositories (with vector_id reference)
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

### Issue #2: Embedchain Setup
**Priority: High**
**Estimated Time: 2 days**
**Labels: infrastructure, vector-storage**

Set up Embedchain for vector storage and Gmail integration.

**Tasks:**
- [x] Install and configure embedchain[gmail]
- [x] Set up vector storage collections:
  - Newsletter content
  - Repository content
- [x] Configure Gmail loader
- [x] Implement vector storage operations
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Vector storage properly configured
- [x] Gmail loader working
- [x] Vector operations tested
- [x] Test coverage > 90%

### Issue #3: Gmail Integration with Embedchain
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, external-api**

Implement Gmail integration using Embedchain.

**Tasks:**
- [x] Set up Gmail API credentials
- [x] Configure Embedchain Gmail loader
- [x] Implement newsletter filtering by label
- [x] Create content extraction pipeline
- [x] Add vector storage integration
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Successfully connects to Gmail API
- [x] Correctly filters newsletters
- [x] Stores content in vector storage
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
- [x] Integrate with vector storage
- [x] Create processing queue
- [x] Write unit tests
- [x] Implement deterministic pipeline stages:
  - [x] fetch_newsletters()
  - [x] process_newsletters()
  - [x] run() pipeline coordinator

**Acceptance Criteria:**
- [x] Component successfully polls for newsletters
- [x] Validates and truncates newsletter content
- [x] Stores content in vector storage
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

Implement the Content Extractor agent with semantic analysis.

**Tasks:**
- [x] Create repository link extraction
- [x] Implement vector-based content analysis
- [x] Add metadata collection
- [x] Create storage integration
- [x] Write unit tests
- [ ] Add LLM-based repository summarization:
  - [ ] Fetch and process README content
  - [ ] Generate structured repository summaries
  - [ ] Store summaries with vector embeddings
- [ ] Implement data migration:
  - [ ] Create migration script for existing repositories
  - [ ] Add README content to existing entries
  - [ ] Generate summaries for existing repositories
  - [ ] Update vector embeddings
- [ ] Update tests for new functionality

**Acceptance Criteria:**
- [x] Successfully extracts GitHub links
- [x] Performs semantic analysis
- [x] Stores data with vector references
- [ ] Generates meaningful repository summaries
- [ ] Successfully migrates existing data
- [x] Test coverage > 90%

### Issue #6: Topic Analyzer Agent
**Priority: High**
**Estimated Time: 3 days**
**Labels: agent, core-functionality**

Implement the Topic Analyzer agent with semantic categorization.

**Tasks:**
- [x] Create fixed category structure
- [ ] Implement LLM-based category prototype generation:
  - [ ] Generate variant summaries for each category
  - [ ] Create embeddings for category prototypes
  - [ ] Store prototype data and embeddings
- [ ] Implement semantic similarity matching:
  - [ ] Compare repository summaries to category prototypes
  - [ ] Calculate confidence scores
  - [ ] Handle parent/child relationships
- [ ] Add data migration:
  - [ ] Generate category prototypes
  - [ ] Recategorize existing repositories
  - [ ] Update category assignments
- [ ] Write unit tests
- [ ] Add prototype management:
  - [ ] Versioning for category prototypes
  - [ ] Tools for updating prototypes
  - [ ] Prototype validation

**Acceptance Criteria:**
- [ ] Generates meaningful category prototypes
- [ ] Correctly matches repositories to categories
- [ ] Maintains category structure
- [ ] Successfully migrates existing data
- [x] Test coverage > 90%

### Issue #7: Repository Curator Agent
**Priority: High**
**Estimated Time: 2 days**
**Labels: agent, core-functionality**

Implement the Repository Curator agent with semantic analysis.

**Tasks:**
- [x] Create repository metadata management
- [x] Implement vector-based categorization
- [x] Add semantic duplicate detection
- [x] Create storage integration
- [x] Write unit tests

**Acceptance Criteria:**
- [x] Manages repository metadata
- [x] Uses semantic categorization
- [x] Detects duplicates using embeddings
- [x] Test coverage > 90%

### Issue #8: README Generator Agent
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

### Issue #9: Vector Storage Integration
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, core-functionality**

Implement comprehensive vector storage integration.

**Tasks:**
- [x] Create vector storage wrapper
- [x] Implement semantic search operations
- [x] Add batch processing for embeddings
- [ ] Create backup/recovery system
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Vector operations working properly
- [x] Semantic search functional
- [ ] Backup system in place
- [x] Test coverage > 90%

### Issue #10: Agent Orchestration
**Priority: High**
**Estimated Time: 2 days**
**Labels: integration, core-functionality**

Implement the orchestration system for agent coordination.

**Tasks:**
- [x] Create hybrid orchestration system:
  - [x] Deterministic components for known workflows
  - [x] Agent-based decision making for complex tasks
- [x] Implement processing pipeline
- [x] Add vector storage coordination
- [x] Create system state management
- [x] Write integration tests

**Acceptance Criteria:**
- [x] Components and agents communicate properly
- [x] Pipeline processes correctly
- [x] Vector storage properly integrated
- [x] Efficient token usage in LLM interactions
- [x] Test coverage > 90%

**Implementation Notes:**
- Use deterministic pipelines for predictable workflows
- Reserve agent-based decisions for complex tasks
- Minimize LLM token usage by keeping content in pipeline
- Pass only necessary metadata to LLM for decisions

### Issue #11: Testing & Documentation
**Priority: High**
**Estimated Time: 3 days**
**Labels: testing, documentation**

Complete testing suite and documentation for MVP, with focus on README updating system.

**Tasks:**
- [x] Create comprehensive integration tests for README updating system
  - [x] Test agent interactions
  - [x] Test data flow through pipeline
  - [x] Test vector storage integration
  - [x] Test error handling and recovery
- [x] Implement end-to-end tests for complete workflow
  - [x] Test newsletter processing to README generation
  - [x] Test repository categorization
  - [x] Test topic analysis and organization
- [x] Write vector storage documentation
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

### Issue #13: Component Testing Implementation
**Priority: High**
**Estimated Time: 5 days**
**Labels: testing, core-functionality**

Implement independent tests for each pipeline component to verify correct functionality with live external dependencies.

**Tasks:**
1. Gmail/Newsletter Component Test
   - [x] Test with live Gmail account
   - [x] Verify actual newsletter fetching
   - [x] Confirm real-time database storage
   - [x] Validate vector embeddings creation
   - [x] Test with new incoming newsletters
   - [x] Verify historical tracking works
   - [x] Evidence collection:
     - [x] Show fetched newsletters in database
     - [x] Display vector embeddings
     - [x] Demonstrate duplicate prevention
     - [x] Log processing timestamps

2. Content Extraction Component Test
   - [x] Process actual newsletter content
   - [x] Extract live GitHub repository links
   - [x] Make real API calls for repository metadata
   - [x] Create embeddings with live LLM service
   - [x] Store in production database
   - [ ] Generate repository summaries with LLM
   - [ ] Validate summary quality and structure
   - [x] Add human-readable verification:
     - [x] Show extracted links vs source content
     - [x] Display GitHub API responses
     - [x] Show metadata collection results
     - [ ] Display repository summaries
     - [x] Summarize processing statistics

3. Topic Analysis Component Test
   - [ ] Generate and validate category prototypes
   - [ ] Test prototype versioning and updates
   - [ ] Process real repository descriptions
   - [ ] Generate repository summaries
   - [ ] Test similarity matching
   - [ ] Update production database
   - [ ] Add human-readable verification:
     - [ ] Display category prototypes
     - [ ] Show repository summaries
     - [ ] Present similarity scores
     - [ ] Display categorization rationale
     - [ ] Summarize analysis decisions

4. Repository Curation Component Test
   - [ ] Test with live repository data
   - [ ] Make real GitHub API calls
   - [ ] Use LLM for duplicate detection
   - [ ] Update actual metadata
   - [ ] Add human-readable verification:
     - [ ] Show metadata updates
     - [ ] Display duplicate detection results
     - [ ] Present similarity scores
     - [ ] Summarize curation decisions

5. README Generation Component Test
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
- Vector operations work with real embeddings
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

### Issue #12: GitHub Actions Setup
**Priority: High**
**Estimated Time: 1 day**
**Labels: deployment, automation**

Set up GitHub Actions for automated execution. Requires Issue #11 to be completed first.

**Tasks:**
- [ ] Create GitHub Actions workflow
- [ ] Implement scheduled execution
- [ ] Add vector storage management
- [ ] Create deployment configuration
- [ ] Write workflow tests

**Acceptance Criteria:**
- All integration and end-to-end tests passing in CI environment
- Workflow runs on schedule
- Executes successfully
- Vector storage properly managed
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
- Vector operations performing within targets
- GitHub Actions workflow successful
- README updates working properly
- Efficient token usage in LLM interactions

## Data Migration Notes

1. Content Extractor Migration:
- Existing repositories need README content fetched
- LLM summaries must be generated
- New vector embeddings created
- Maintain existing metadata

2. Topic Analyzer Migration:
- Generate category prototypes before migration
- Create prototype embeddings
- Recategorize all existing repositories
- Validate new categorizations

3. Database Considerations:
- Add new columns for summaries
- Version control for category prototypes
- Backup existing data before migration
- Rollback plan if needed

4. Testing Requirements:
- Verify data integrity after migration
- Compare old vs new categorizations
- Validate embedding quality
- Test system performance with new data structure

## Implementation Strategy

1. Phase 1: Infrastructure Updates
- Add new database fields
- Implement prototype storage
- Create migration scripts

2. Phase 2: Content Enhancement
- Fetch README content
- Generate repository summaries
- Update vector embeddings

3. Phase 3: Categorization
- Generate category prototypes
- Implement new matching logic
- Migrate existing categorizations

4. Phase 4: Validation
- Test all components
- Verify data integrity
- Document changes
