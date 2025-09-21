# Telefonchi Bot

A FastAPI-based Telegram bot for electronics marketplace with SOLID architecture principles.

## Features

- 🤖 **Telegram Bot Integration**: Full Telegram Bot API support with webhooks
- 📱 **Mini App Support**: Telegram Web App integration for modern user experience
- 🏗️ **SOLID Architecture**: Clean, maintainable code following SOLID principles
- 🗄️ **Database Integration**: MySQL database with proper ORM
- 🔐 **Moderation System**: Built-in admin and moderation capabilities
- 📸 **File Upload**: Support for image uploads with proper storage
- 🌐 **API Endpoints**: RESTful API for mini app integration
- 🐳 **Docker Support**: Containerized deployment ready

## Architecture

The project follows SOLID principles with clear separation of concerns:

```
app/
├── api/           # API routes and endpoints
├── core/          # Core configuration and dependencies
├── handlers/      # Business logic handlers
├── repositories/  # Data access layer
├── schemas/       # Pydantic models
├── services/      # Business logic services
└── utils/         # Utility functions
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- MySQL database
- Telegram Bot Token (from @BotFather)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AkbarIOS/telefonchi_oka_bot.git
   cd telefonchi_oka_bot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

### Configuration

Edit the `.env` file with your settings:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database Configuration
DB_HOST=mysql
DB_PORT=3306
DB_NAME=telegram_bot
DB_USER=root
DB_PASSWORD=your_password_here

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
WEBHOOK_URL=https://your-domain.com/api/v1/webhook
MINI_APP_URL=https://your-miniapp-domain.com
```

## API Endpoints

- `GET /` - Service status
- `GET /health` - Health check with component status
- `POST /api/v1/webhook` - Telegram webhook endpoint
- `GET /api/advertisements` - Get advertisements with filters
- `POST /api/advertisements` - Create new advertisement
- `GET /api/categories` - Get all categories
- `GET /api/brands` - Get all brands

## Development

### Local Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run database migrations**
   ```bash
   # Set up your database schema
   ```

3. **Start development server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Project Structure

- **Controllers**: Handle HTTP requests and responses
- **Services**: Contain business logic
- **Repositories**: Handle data persistence
- **Models**: Define data structures
- **Dependencies**: Manage dependency injection

## Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Production Considerations

- Set `DEBUG=false` in production
- Use strong database passwords
- Configure proper logging levels
- Set up monitoring and health checks
- Use HTTPS for webhook URLs

## Features in Detail

### Moderation System
- User ID 162099531 has admin privileges
- Approve/reject advertisements
- Admin-only commands and interfaces

### File Upload System
- Supports image uploads for advertisements
- Automatic file storage and URL generation
- CORS-enabled for web app integration

### Multi-language Support
- Russian and Uzbek language support
- Localized user interface
- Dynamic language switching

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support, please open an issue in the GitHub repository.# Fixed database configuration for Railway
