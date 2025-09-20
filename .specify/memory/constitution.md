<!--
SYNC IMPACT REPORT
===================
Version change: 1.2.0 → 1.3.0
Modified principles: N/A
Added sections: Python Development Standards (Code Quality, Testing, Package Structure, Dependencies, Build/Distribution)
Removed sections: N/A
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (Constitution version updated)
  ✅ .specify/templates/spec-template.md (requirements format compatible)
  ✅ .specify/templates/tasks-template.md (TDD and task categorization aligns)
  ✅ .specify/templates/agent-file-template.md (compatible structure)
Follow-up TODOs: None
-->

# V-Mount Constitution

## Core Principles

### I. Specification-First Development
Every feature MUST begin with a clear specification defining user value and functional requirements before any implementation planning. Specifications MUST be written for business stakeholders, avoid implementation details, and mark all ambiguities with [NEEDS CLARIFICATION] markers. No development work proceeds until specifications pass the completeness checklist and all clarifications are resolved.

**Rationale**: Prevents scope creep, ensures alignment on requirements, and establishes testable acceptance criteria before technical decisions are made.

### II. Test-Driven Development (NON-NEGOTIABLE)
All implementation MUST follow strict TDD: write failing tests, get user approval, then implement to make tests pass. Contract tests MUST be written for all API endpoints, integration tests for all user scenarios, and unit tests for all business logic. Tests MUST fail before any implementation code is written.

**Rationale**: Ensures code meets requirements, prevents regression, provides living documentation, and forces consideration of edge cases upfront.

### III. Constitutional Design Review
All technical designs MUST pass constitutional compliance checks before implementation. Any deviations from simplicity principles MUST be explicitly justified in the Complexity Tracking section with evidence that simpler alternatives were evaluated and rejected for specific technical reasons.

**Rationale**: Maintains architectural consistency, prevents unnecessary complexity, and ensures technical decisions align with project values.

### IV. Library-First Architecture
Every feature MUST be implemented as a standalone library with clear interfaces before integration. Libraries MUST be self-contained, independently testable, and have explicit purposes beyond mere code organization. CLI interfaces are required for all libraries to enable standalone testing and debugging.

**Rationale**: Promotes modularity, enables independent testing, facilitates reuse, and maintains clear separation of concerns.

### V. Simplicity and YAGNI
Start with the simplest possible implementation that meets current requirements. Do not build for anticipated future needs without concrete user stories. Complex patterns (repositories, factories, observers) MUST be justified against simpler direct approaches. Prefer composition over inheritance, explicit over implicit, and clear over clever.

**Rationale**: Reduces maintenance burden, accelerates development, and ensures code remains understandable and modifiable.

### VI. Gang Image Integrity
All gang image validation MUST be deterministic and reproducible across different environments. Tools MUST support multiple embedded platforms (Qualcomm MBN, Broadcom CFE, MediaTek Android-style, Marvell U-Boot) with automatic format detection. Filesystem analysis MUST handle ext2/3/4, SquashFS, UBIFS, JFFS2, and YAFFS2 with proper superblock validation. Partition extraction and mounting capabilities are required for manual verification workflows.

**Rationale**: Ensures reliable embedded system deployment across diverse chipset platforms, prevents costly field failures, and maintains production line efficiency in manufacturing environments.

## Development Workflow

### Planning Process
1. Feature specification MUST be written and approved before planning
2. Implementation plan MUST include constitutional compliance check
3. Technical research MUST resolve all [NEEDS CLARIFICATION] markers
4. Design phase MUST produce failing tests and clear contracts
5. Task generation follows TDD ordering: tests before implementation

### Quality Gates
- All phases require constitutional compliance verification
- Implementation cannot proceed with failing compliance checks
- Code review MUST verify adherence to all five core principles
- Performance and integration testing required before feature completion

### Documentation Standards
- Specifications focus on user value and business requirements
- Technical documentation generated from implementation plans
- Agent context files maintained automatically from active technologies
- Decision rationale preserved in research.md files

## Quality Standards

### Code Quality
- Linting and type checking MUST pass before commits
- All public interfaces MUST have comprehensive tests
- Error handling MUST be explicit and documented
- Performance targets MUST be defined and measured

### Testing Requirements
- Contract tests for all external interfaces
- Integration tests for all user workflows
- Unit tests for all business logic
- Manual testing scenarios for UI/UX validation

### Security and Compliance
- No secrets or credentials in source control
- Input validation on all external data
- Structured logging for debugging and auditing
- Dependency scanning and updates

## Domain Requirements (Embedded Systems)

### Gang Image Validation Standards
- Partition table validation MUST verify boot sector integrity and partition boundaries
- Filesystem checks MUST validate superblock, inode tables, and directory structures for ext2/3/4, SquashFS, UBIFS, JFFS2, YAFFS2
- Manufacturing metadata MUST be preserved and validated (serial numbers, checksums, build info)
- Validation MUST handle multiple image formats (raw, compressed, encrypted)
- Performance targets: <10 seconds validation time per 8GB image on standard hardware
- Memory efficiency: Process files in chunks to minimize RAM usage for large images

### Production Integration Requirements
- Output formats MUST include JSON for MES (Manufacturing Execution System) integration
- Exit codes MUST follow manufacturing standards (0=pass, 1=fail, 2=warning, 3=error)
- All validation errors MUST include actionable remediation guidance
- Batch processing MUST support parallel validation of multiple images
- Progress reporting required for long-running validations

### Hardware Compatibility
- MUST support USB 2.0/3.0 storage devices and SD cards
- MUST handle various partition schemes (MBR, GPT, custom embedded layouts)
- MUST work across Linux, Windows, and macOS development environments
- MUST detect and report device/media errors vs image content errors

## Platform-Specific Requirements

### Chipset Support Matrix
Tools MUST support the following embedded platforms with their specific characteristics:

#### Qualcomm Platform (Primary Support)
- MBN (Multi-Boot Image) format parsing with ELF support
- TrustZone security architecture validation
- Memory layout: SBL (0x40000000), TZ (0x86000000), RPM (0x60000000), APPSBL (0x8F600000)
- Automatic partition type detection based on load addresses
- Support for QFIL programming format

#### Broadcom Platform (Next Priority)
- CFE (Common Firmware Environment) bootloader detection
- TRX header format validation
- NVRAM configuration area analysis
- Memory layout: CFE (0x00000000), NVRAM (0x00010000), Kernel (0x00020000)
- SquashFS + JFFS2 filesystem combination support

#### MediaTek Platform (Planned)
- Preloader + U-Boot dual bootloader structure
- Android-style partition layout (boot, recovery, system, userdata)
- SP Flash Tool format compatibility
- Support for ext4, F2FS, UBIFS filesystems

#### Marvell Platform (Planned)
- U-Boot based bootloader analysis
- Network processor specific features
- Multi-CPU core layout validation
- Standard Linux filesystem support (ext2/3/4, SquashFS)

### CLI Standards
- Zero external dependencies (Python standard library only)
- Consistent command-line interface across all platform modules
- Verbose and quiet modes for different use cases
- Partition extraction with automatic filesystem type detection
- Support for batch processing and scripting integration

## Python Development Standards

### Code Quality Requirements
- Python 3.8.1+ compatibility MUST be maintained (updated for flake8 compatibility)
- Type hints MUST be used for all public interfaces
- Docstrings MUST follow Google style for all public functions and classes
- Code MUST pass mypy static type checking with strict settings
- All code MUST be formatted with Black (line length: 100)
- Import sorting MUST follow isort configuration
- uv MUST be used for development environment management and execution

### Testing Standards
- Test coverage MUST be ≥90% for all core modules
- Unit tests MUST be independent and not require external files
- Integration tests MUST use fixture data for gang image samples
- Performance tests MUST verify <10 second analysis time for 8GB images
- Tests MUST run on Python 3.8, 3.9, 3.10, 3.11, and 3.12

### Package Structure Requirements
- MUST follow src-layout: `src/vmount/` contains all source code
- Platform-specific analyzers MUST be in `src/vmount/platforms/`
- Core functionality MUST be in `src/vmount/core/`
- Utilities MUST be in `src/vmount/utils/` and `src/vmount/analyzers/`
- CLI entry point MUST be `src/vmount/cli.py`

### Dependency Management
- Runtime dependencies MUST be zero (standard library only)
- Development dependencies MUST be specified in pyproject.toml [project.optional-dependencies]
- uv MUST be the preferred dependency management and execution tool
- Version pinning MUST use compatible release specifiers (~=)
- Pre-commit hooks MUST enforce code quality standards

### Build and Distribution
- MUST use pyproject.toml for modern Python packaging
- MUST provide console script entry point: `vmount`
- MUST include comprehensive Makefile for development workflows
- MUST support uv-based development: `uv sync` and `uv pip install -e .`
- MUST support traditional pip installation as fallback: `pip install -e .`
- CLI execution MUST work with: `uv run python -m vmount.cli`

## Governance

### Amendment Process
Constitutional changes require:
1. Documented rationale for the change
2. Impact assessment on existing templates and workflows
3. Version bump following semantic versioning
4. Update of all dependent artifacts and templates
5. Migration plan for existing features if applicable

### Version Management
- MAJOR: Backward incompatible governance/principle changes
- MINOR: New principles or materially expanded guidance
- PATCH: Clarifications, wording improvements, non-semantic changes

### Compliance Review
- All feature planning MUST include constitutional compliance check
- Code reviews MUST verify adherence to core principles
- Quarterly review of constitutional effectiveness and needed updates
- Template synchronization required after any constitutional changes

### Enforcement
Constitution supersedes all other development practices and guidelines. Non-compliance blocks feature progression through quality gates. Complexity deviations require explicit justification and approval. Use CLAUDE.md for runtime development guidance within constitutional bounds.

**Version**: 1.3.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20