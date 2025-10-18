---
inclusion: always
---

# Code Quality Standards

## General Principles

- Write clean, readable code
- Follow language-specific conventions (PEP 8 for Python, ESLint for TypeScript)
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Comment complex logic, not obvious code

## TypeScript (CDK)

- Use strict mode
- Define interfaces for all data structures
- Use const for immutable values
- Avoid any type - use proper typing
- Use async/await over promises

## Python (Lambda)

- Use type hints for function parameters and returns
- Follow PEP 8 naming conventions
- Use f-strings for string formatting
- Use context managers for resource handling
- Avoid global variables

## Error Messages

- Be specific about what went wrong
- Include context (function name, input values)
- Suggest remediation steps when possible
- Use structured logging for easier debugging

## Configuration

- Use environment variables for runtime config
- Use Parameter Store for shared config
- Use Secrets Manager for sensitive data
- Never commit secrets to git
- Document all configuration options

## Testing (Optional for MVP)

- Write tests for critical business logic
- Mock external services
- Test error paths
- Use descriptive test names

## Git Practices

- Write clear commit messages
- Commit frequently with logical changes
- Use feature branches for major changes
- Keep commits focused on single changes

## Documentation

- Document all API endpoints
- Include request/response examples
- Document environment variables
- Keep README up to date
- Add inline comments for complex logic

## Hackathon Speed Tips

- Use code generation tools when appropriate
- Copy-paste-modify similar components
- Focus on working code over perfect code
- Refactor only if time permits
- Prioritize demo-critical features
