---
name: feature-scaffolder
description: Scaffold new features with complete structure including tests, documentation, and boilerplate. Use when user wants to create a new feature, add a new module, or scaffold a new component with all supporting files.
allowed-tools: Read, Write, Glob, Bash
---

# Feature Scaffolder

Creates complete feature structure with tests, documentation, and boilerplate code.

## Instructions

This is a multi-step workflow that creates a fully scaffolded feature.

### Step 1: Gather Requirements

Ask user:
- Feature name
- Feature type (API endpoint, UI component, data model, etc.)
- Programming language/framework
- Location in codebase

### Step 2: Analyze Existing Structure

Use Glob and Read to understand project structure:
```bash
# Find similar features
find . -name "*similar_feature*"

# Read project conventions
cat README.md
cat CONTRIBUTING.md
```

### Step 3: Create Directory Structure

Based on project conventions, create appropriate structure:

**For API endpoint:**
```
feature-name/
├── __init__.py
├── routes.py
├── models.py
├── services.py
├── schemas.py
├── tests/
│   ├── __init__.py
│   ├── test_routes.py
│   └── test_services.py
└── README.md
```

**For UI component:**
```
FeatureName/
├── FeatureName.tsx
├── FeatureName.test.tsx
├── FeatureName.styles.ts
├── FeatureName.stories.tsx
├── index.ts
└── README.md
```

### Step 4: Generate Boilerplate

Create files with appropriate boilerplate:

1. **Main feature file** - Basic structure following project patterns
2. **Test file** - Test scaffolding with common test cases
3. **Documentation** - README explaining feature purpose and usage
4. **Type definitions** - Interfaces, types, or schemas
5. **Export/import statements** - Proper module exports

### Step 5: Integrate with Existing Code

- Update relevant index files to export new feature
- Add to routing configuration if applicable
- Update documentation table of contents
- Add to test suite configuration

### Step 6: Create TODO Checklist

Generate implementation checklist for user:
```markdown
## Implementation Checklist

- [ ] Implement core feature logic
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Add error handling
- [ ] Add logging
- [ ] Update API documentation
- [ ] Add usage examples
- [ ] Perform code review
```

### Step 7: Report Results

Summarize what was created:
- List all files created with paths
- Explain structure and purpose
- Provide next steps
- Offer to help with implementation

## Examples

### Example 1: API Endpoint

```
User: "Create a new user authentication endpoint"

Actions:
1. Create /api/auth/ directory
2. Generate routes.py with authentication stubs
3. Create models.py with User model
4. Generate schemas.py with LoginSchema, RegisterSchema
5. Create comprehensive test files
6. Generate API documentation
7. Update main router to include auth routes

Output: "Created authentication endpoint at /api/auth/ with:
- Routes: login, logout, register, refresh
- Models: User, Token
- Tests: 15 test cases scaffolded
- Documentation: README.md with usage examples
Ready for implementation."
```

### Example 2: React Component

```
User: "Scaffold a new UserProfile component"

Actions:
1. Create components/UserProfile/ directory
2. Generate UserProfile.tsx with component structure
3. Create UserProfile.test.tsx with test scaffolding
4. Generate UserProfile.stories.tsx for Storybook
5. Create UserProfile.styles.ts with styled-components
6. Update components/index.ts to export UserProfile

Output: "Created UserProfile component with:
- Main component file with props interface
- Test file with 5 test cases
- Storybook stories for all variants
- Styled components file
- Proper TypeScript types
Ready for implementation."
```

## Best Practices

1. **Always analyze existing patterns first** - Don't impose structure, follow project conventions
2. **Generate meaningful boilerplate** - Not just empty files, but useful starting points
3. **Include comprehensive tests** - Test file should guide implementation
4. **Document as you scaffold** - README explains purpose and usage
5. **Provide clear next steps** - User knows exactly what to implement
6. **Follow naming conventions** - Match project's existing naming patterns
7. **Update integration points** - Don't leave feature isolated

## Troubleshooting

**Unclear project structure:**
- Ask user to specify or clarify structure
- Offer multiple options based on common patterns

**Missing conventions:**
- Look for similar features in codebase
- Fall back to framework best practices
- Ask user for guidance

**Complex integrations:**
- Create TODO comments where manual intervention needed
- Document integration steps in README
- Offer to help with specific integration after scaffold
