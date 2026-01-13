# Contributing to StackWise

Thank you for your interest in contributing to StackWise! We welcome contributions from the community.

## Important Notes

**StackWise is a self-hosted project** - This project is designed to be self-hosted, not a SaaS offering. Please keep this in mind when proposing features or changes.

## How to Contribute

### Reporting Issues

- Check if the issue already exists before creating a new one
- Provide clear steps to reproduce the issue
- Include relevant environment details (OS, Python/Node versions, etc.)
- For bug reports, include error messages and stack traces if available

### Suggesting Features

- Open an issue to discuss the feature before implementing
- Explain the use case and how it fits with StackWise's self-hosted nature
- Consider backward compatibility and migration paths

### Pull Requests

1. **Fork the repository** and create a branch from `main`
2. **For large changes**, please open an issue first to discuss the approach
3. **Make your changes** following the project's code style
4. **Test your changes** locally
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description of what was changed and why

## Development Setup

### Prerequisites

- Python 3.11+ (for backend)
- Node.js 18+ (for frontend and SDK)
- PostgreSQL
- Redis
- Git

### Backend Setup

See [backend/README.md](./backend/README.md) for detailed backend setup instructions.

### Frontend Setup

See [frontend/README.md](./frontend/README.md) for detailed frontend setup instructions.

### Celery Worker Setup

See [backend/CELERY_SETUP.md](./backend/CELERY_SETUP.md) for detailed Celery setup instructions.

## Code Style

### Python (Backend)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings for public functions and classes

### TypeScript/JavaScript (Frontend & SDK)

- Use TypeScript for type safety
- Follow ESLint configuration
- Use meaningful variable and function names
- Keep components focused and reusable

## Testing

- Test your changes locally before submitting
- Ensure the backend API works correctly
- Test the frontend dashboard if UI changes were made
- Verify Celery workers process tasks correctly if you modified the AI analysis pipeline

## Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers when applicable (e.g., "Fix #123: ...")
- Keep commits focused on a single change

## Pull Request Guidelines

- **Keep PRs focused** - One feature or bug fix per PR
- **Update documentation** - If you add features or change behavior, update relevant docs
- **Add tests** if applicable
- **Ensure CI passes** (if applicable)
- **Request review** from maintainers when ready

## Areas for Contribution

We welcome contributions in these areas:

- **Bug fixes** - Help us improve stability
- **Documentation** - Improve clarity and completeness
- **New features** - Discuss first via issues
- **Performance improvements** - Optimize queries, reduce latency
- **Additional SDKs** - Python, Ruby, Go, etc.
- **UI/UX improvements** - Enhance the dashboard experience
- **Testing** - Add test coverage

## Questions?

- Open an issue for questions or discussions
- Be respectful and constructive in all interactions

## License

By contributing to StackWise, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to StackWise! 🎉
