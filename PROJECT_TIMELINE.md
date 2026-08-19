# Dashify: 19-Week Agile Project Timeline

## Project Overview
A terminal-based dashboard application built with Python, Textual framework, and TOML configuration syntax. Designed for power users and Linux warriors who need a customizable, lightweight alternative to electron-based tools like Notion and Obsidian.

**Project Duration:** 19 weeks  
**Framework:** Agile (5 sprints of ~3-4 weeks each)  
**Primary Requirements:** Python application, TOML configuration, custom widgets, Textual rendering

---

## Sprint 1: Foundation & Architecture (Weeks 1-4)

### Goals
- Establish project infrastructure and development environment
- Design and document core architecture
- Set up CI/CD pipeline
- Create foundational codebase structure

### User Stories & Tasks

#### Task 1.1: Project Setup (Week 1)
- [ ] Initialize Python project with UV/Poetry package management
- [ ] Set up project structure (src/, tests/, docs/ directories)
- [ ] Configure linting and formatting (Ruff, Black)
- [ ] Create development environment documentation
- [ ] Set up Git workflow and branch protection rules
- [ ] Initialize pre-commit hooks

**Acceptance Criteria:**
- Project builds and runs successfully
- All linter checks pass
- Contributors can follow setup documentation

#### Task 1.2: CI/CD Pipeline (Week 1-2)
- [ ] Set up GitHub Actions workflow for automated testing
- [ ] Configure linting checks in CI
- [ ] Set up code coverage reporting
- [ ] Create deployment pipeline structure (non-functional at this stage)

**Acceptance Criteria:**
- CI runs on every PR
- All checks must pass before merge
- Coverage reports available

#### Task 1.3: Architecture Design & Documentation (Week 2-3)
- [ ] Document high-level application architecture
- [ ] Design widget system architecture (inheritance/composition models)
- [ ] Plan configuration parsing pipeline (TOML → JSON → objects)
- [ ] Document data flow and state management approach
- [ ] Create API design for widget interface
- [ ] Define error handling and exception strategies

**Acceptance Criteria:**
- Architecture document complete and reviewed
- Widget interface specification finalized
- Data flow diagrams created

#### Task 1.4: Textual Framework Integration (Week 3-4)
- [ ] Add Textual dependency and verify compatibility
- [ ] Create minimal Textual application that renders
- [ ] Research and document Textual's theming/styling system
- [ ] Create basic application shell (App class, layout structure)
- [ ] Test keyboard and mouse event handling
- [ ] Document Textual-specific patterns for this project

**Acceptance Criteria:**
- Basic Textual app runs without errors
- Can capture keyboard and mouse input
- Styling system understood and documented

---

## Sprint 2: Core Widget System (Weeks 5-8)

### Goals
- Implement widget framework and base classes
- Create TOML configuration parser
- Develop basic widget rendering system
- Establish error handling and sandboxing

### User Stories & Tasks

#### Task 2.1: TOML Configuration Parser (Week 5)
- [ ] Implement TOML file parsing (using `tomllib` or similar)
- [ ] Create data validation system for configuration
- [ ] Implement parameterized configuration options (prevent code injection)
- [ ] Create configuration schema and validators
- [ ] Handle invalid configuration gracefully (reject or ignore)
- [ ] Generate helpful error messages for malformed configs

**Acceptance Criteria:**
- Parser reads and validates valid TOML files
- Rejects/ignores invalid configurations safely
- All parameter injection attempts are blocked
- Error messages are user-friendly

#### Task 2.2: Base Widget Framework (Week 5-6)
- [ ] Design and implement Widget base class
- [ ] Implement widget lifecycle methods (init, render, update)
- [ ] Create widget registry system
- [ ] Implement widget property system (attributes, flags)
- [ ] Document widget development API
- [ ] Create widget interface documentation

**Acceptance Criteria:**
- Base Widget class can be inherited
- Widget registry can store and retrieve widgets
- Properties can be set and retrieved
- API is well-documented

#### Task 2.3: Configuration-to-Widget Mapping (Week 6)
- [ ] Implement configuration loading pipeline
- [ ] Create widget factory pattern
- [ ] Map TOML widget definitions to Python widget instances
- [ ] Implement widget property injection from config
- [ ] Test with sample configuration files

**Acceptance Criteria:**
- Widgets instantiate correctly from TOML config
- All properties map correctly
- Sample configs load without errors

#### Task 2.4: Error Handling & Sandboxing (Week 7)
- [ ] Implement exception handling framework
- [ ] Create widget error isolation (widgets don't crash app)
- [ ] Implement error logging and display system
- [ ] Design error recovery strategies
- [ ] Test error scenarios for robustness

**Acceptance Criteria:**
- Widget errors don't cascade to other widgets
- All errors are caught and logged
- App continues running after widget failure
- Error information is accessible to user

#### Task 2.5: System Information Access (Week 7-8)
- [ ] Identify and implement system information providers
- [ ] Create system info module (CPU, memory, disk, network, etc.)
- [ ] Implement cross-platform compatibility (UNIX-like systems)
- [ ] Create caching system for expensive system calls
- [ ] Document available system variables for widget use

**Acceptance Criteria:**
- System info accessible and accurate
- Works on Linux, macOS, BSD
- Performance is acceptable (caching in place)
- All available system variables documented

---

## Sprint 3: Widget Rendering & Arrangement (Weeks 9-12)

### Goals
- Implement widget rendering pipeline
- Create layout and tiling system
- Develop basic built-in widgets
- Ensure aesthetic appearance

### User Stories & Tasks

#### Task 3.1: Widget Rendering Pipeline (Week 9)
- [ ] Implement widget render method in Textual
- [ ] Create rendering refresh mechanism
- [ ] Implement partial updates (only re-render changed widgets)
- [ ] Handle text wrapping and truncation
- [ ] Create widget styling system integration

**Acceptance Criteria:**
- Widgets render to terminal output correctly
- Rendering is performant (minimal flickering)
- Widgets update without full redraw when possible

#### Task 3.2: Layout & Tiling System (Week 9-10)
- [ ] Design flexible layout system
- [ ] Implement grid-based widget positioning
- [ ] Create responsive sizing options
- [ ] Implement widget spacing and padding
- [ ] Create layout configuration in TOML
- [ ] Support multiple layout strategies (grid, flex, absolute)

**Acceptance Criteria:**
- Widgets position correctly according to config
- Layout responds to terminal resizing
- Configuration is intuitive and documented

#### Task 3.3: Built-in Widget Implementations (Week 10-11)
- [ ] Implement Todo widget
  - [ ] Parse todo list format
  - [ ] Display with formatting
  - [ ] Support completion status
- [ ] Implement System Stats widget
  - [ ] Display CPU, memory, disk usage
  - [ ] Use system info module
  - [ ] Real-time updates
- [ ] Implement Clock/Time widget
  - [ ] Display current time
  - [ ] Support multiple formats
- [ ] Implement Text/Notes widget
  - [ ] Display static or dynamic text
  - [ ] Support markdown or plain text

**Acceptance Criteria:**
- All 4 widgets render correctly
- Data updates in real-time
- Widgets can be configured from TOML
- Sample configurations provided

#### Task 3.4: Theming & Aesthetics (Week 11-12)
- [ ] Design color schemes
- [ ] Create theme configuration system
- [ ] Implement light and dark themes
- [ ] Support custom color schemes
- [ ] Document theming for users
- [ ] Test aesthetic appearance on various terminals

**Acceptance Criteria:**
- Default themes look polished
- Custom themes can be created and applied
- Works on different terminal color schemes
- Documentation includes theme customization guide

---

## Sprint 4: Advanced Features & Interactivity (Weeks 13-16)

### Goals
- Implement interactive features
- Add async/API support
- Create hot-reloading system
- Enhance user experience

### User Stories & Tasks

#### Task 4.1: Mouse Integration & Interactivity (Week 13)
- [ ] Implement mouse event handlers in Textual
- [ ] Create clickable widget elements
- [ ] Implement focus management
- [ ] Add hover effects
- [ ] Support right-click context menus
- [ ] Test mouse behavior across terminal emulators

**Acceptance Criteria:**
- Mouse clicks register correctly
- Widget focus changes work properly
- UI responds visually to mouse input
- Works in most modern terminal emulators

#### Task 4.2: Async/API Request System (Week 13-14)
- [ ] Design async widget update mechanism
- [ ] Implement HTTP request capability for widgets
- [ ] Create async-await wrapper for widget methods
- [ ] Handle network errors gracefully
- [ ] Implement request caching/throttling
- [ ] Create API request widget (for dynamic data)

**Acceptance Criteria:**
- Widgets can make async API calls
- Long-running requests don't block UI
- Network errors are handled gracefully
- Sample API widget demonstrates functionality

#### Task 4.3: Hot Reloading System (Week 14-15)
- [ ] Implement configuration file watching
- [ ] Create reload mechanism without restarting app
- [ ] Preserve widget state during reload
- [ ] Handle reload errors gracefully
- [ ] Document hot-reload functionality

**Acceptance Criteria:**
- Configuration changes reload without restart
- Existing state preserved where possible
- Errors during reload don't crash app
- User receives feedback on reload status

#### Task 4.4: Preset Configuration Recipes (Week 15-16)
- [ ] Create 3-5 preset dashboard configurations
- [ ] Include configurations for:
  - [ ] Sysadmin/DevOps dashboard
  - [ ] Developer dashboard
  - [ ] Minimalist dashboard
  - [ ] Information-rich dashboard
- [ ] Document how to use and customize presets
- [ ] Create installation/discovery system for presets

**Acceptance Criteria:**
- Presets load and display correctly
- All presets are documented
- Users can easily select and modify presets
- Presets serve as good examples

---

## Sprint 5: Testing, Packaging & Polish (Weeks 17-19)

### Goals
- Comprehensive testing coverage
- PyPI packaging
- Documentation finalization
- Release preparation

### User Stories & Tasks

#### Task 5.1: Comprehensive Testing Suite (Week 17)
- [ ] Write unit tests for core modules
- [ ] Create integration tests for widget system
- [ ] Test configuration parsing with edge cases
- [ ] Test error handling scenarios
- [ ] Create UI/rendering tests
- [ ] Achieve minimum 70% code coverage
- [ ] Document testing procedures

**Acceptance Criteria:**
- Test suite passes completely
- Coverage meets minimum threshold
- Tests cover critical paths and edge cases
- Testing documentation provided

#### Task 5.2: PyPI Package & Distribution (Week 17-18)
- [ ] Configure package metadata
- [ ] Create installation script
- [ ] Test installation from PyPI
- [ ] Create wheel distribution
- [ ] Document installation instructions
- [ ] Support installation via `pip install dashify` and UV

**Acceptance Criteria:**
- Package installable from PyPI
- All dependencies resolve correctly
- Installation works on different systems
- Package installation documented

#### Task 5.3: Documentation & User Guide (Week 18)
- [ ] Complete user configuration guide
- [ ] Create widget development guide for custom widgets
- [ ] Write API reference documentation
- [ ] Create troubleshooting section
- [ ] Document system requirements
- [ ] Create quick-start guide

**Acceptance Criteria:**
- All user-facing features documented
- Examples provided for common use cases
- Developer guide enables custom widget creation
- Documentation is clear and accessible

#### Task 5.4: Code Quality & Polish (Week 18-19)
- [ ] Final linting and code format pass
- [ ] Code review and refactoring
- [ ] Performance optimization
- [ ] Security audit
- [ ] Final testing pass
- [ ] Dependency updates and pinning

**Acceptance Criteria:**
- All linters pass without warnings
- Code is performant
- No security vulnerabilities identified
- All tests pass
- Ready for release

#### Task 5.5: Release & Project Cleanup (Week 19)
- [ ] Create release notes
- [ ] Tag final version in Git
- [ ] Create GitHub release
- [ ] Update documentation for release
- [ ] Archive this timeline
- [ ] Plan for future maintenance

**Acceptance Criteria:**
- Version released on GitHub and PyPI
- Release notes are comprehensive
- Project is in stable, maintainable state
- Clear path for future updates documented

---

## Key Milestones

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 4 | Architecture Complete | Design documents, CI/CD pipeline |
| 8 | Widget Framework Ready | Base widget system, TOML parser, error handling |
| 12 | Core Features Working | Rendering, layout, 4 built-in widgets, theming |
| 16 | Enhanced Features Done | Mouse support, async API, hot-reload, presets |
| 19 | Release Ready | Tests, documentation, PyPI package |

---

## Risk Mitigation

### Identified Risks from Problem Statement

1. **Schedule Deviation (Late)**
   - Mitigation: Regular sprint reviews, clear prioritization, buffer time in later sprints
   - Monitor: Weekly progress tracking

2. **Tech Stack Bugs (Beyond Control)**
   - Mitigation: Use stable Textual versions, extensive testing
   - Fallback: Maintain communication with Textual maintainers, alternative rendering approaches researched in Sprint 1

3. **System Limitations**
   - Mitigation: Design with cross-platform compatibility from the start (Sprint 1)
   - Testing: Regular testing on multiple platforms during development

---

## Non-Functional Requirements Tracking

### Essential Non-Functional Requirements
- [ ] Support all major UNIX-like operating systems (Sprint 3)
- [ ] Parameterized configuration options prevent code injection (Sprint 2)
- [ ] Code formatted consistently and passes linting (All sprints)
- [ ] Clear, comprehensible configuration options (All sprints)

### Desirable Non-Functional Requirements
- [ ] PyPI packaging (Sprint 5)
- [ ] Accessibility options and color schemes (Sprint 3-4)
- [ ] Widget failure isolation/sandboxing (Sprint 2)
- [ ] Expanded platform support beyond UNIX-like (Sprint 5)

### Discretionary Non-Functional Requirements
- [ ] Homebrew formula packaging (Post-release)
- [ ] GitHub Actions CI/CD (Sprint 1) ✓

---

## Dependencies & Prerequisites

### External Dependencies
- **Textual**: >=7.5.0, <8.0.0 (Textual framework)
- **Python**: >=3.14, <4.0
- **Standard Library**: tomllib (TOML parsing)

### Development Dependencies
- **Ruff**: Linting and formatting
- **pytest**: Testing framework
- **build**: PyPI package building

---

## Success Criteria

The project will be considered successful upon completion if:

1. ✓ Application reads and parses TOML configuration files
2. ✓ Users can create custom widgets via configuration
3. ✓ System information accessible to widgets
4. ✓ Widget framework with arrangement system working
5. ✓ Textual rendering functioning properly
6. ✓ Error handling prevents widget failures from cascading
7. ✓ Mouse integration and interactivity working
8. ✓ Async API requests supported
9. ✓ At least 3-5 preset configurations included
10. ✓ Comprehensive testing suite with good coverage
11. ✓ Packaged and available on PyPI
12. ✓ Complete user and developer documentation
13. ✓ All code passes linting and formatting checks
14. ✓ Supports major UNIX-like operating systems

---

## Notes for Project Manager

- **Review Cadence**: Sprint reviews at the end of each 3-4 week period
- **Stakeholder Updates**: Bi-weekly progress updates recommended
- **Buffer Time**: Each sprint includes ~10% buffer for unexpected issues
- **Parallel Work**: Sprints 3 and 4 can have some parallel streams (e.g., testing can begin earlier)
- **Flexibility**: This timeline is based on estimated task complexity; actual progress may require adjustments

---

*Timeline created: 2026-05-14*  
*Project Status: Planning Phase*
