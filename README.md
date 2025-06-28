## WhatsApp Router (wa_router)

A Django-based routing service designed to efficiently handle and forward Meta WhatsApp webhook requests based on configurable routing rules.

## Overview

The WhatsApp Router acts as an intelligent middleware between Meta's WhatsApp Business API and multiple backend environments. It receives webhook notifications from WhatsApp and routes them to the appropriate destination based on the sender's WhatsApp ID, vendor configuration, and environment settings.

## Core Architecture

### Models

The routing system is built around three main models that work together to provide flexible request routing:

#### 1. Vendor
- **Purpose**: Represents a client or organization using the routing service
- **Key Fields**:
  - `name`: Human-readable vendor name
  - `code`: Unique, URL-safe identifier used in webhook URLs
  - `secure_variables`: Encrypted JSON field storing API keys and other sensitive data
- **Example**: A vendor with code "acme-corp" would receive webhooks at `/webhook/meta/acme-corp/`

#### 2. Environment
- **Purpose**: Defines different deployment environments for each vendor
- **Key Fields**:
  - `vendor`: Foreign key linking to the vendor
  - `name`: Environment name (e.g., "Production", "Staging")
  - `code`: Environment identifier (e.g., "prod", "dev")
  - `target_url`: The destination URL where requests should be forwarded
  - `is_default`: Boolean flag indicating the default environment for fallback routing
- **Constraint**: Each vendor can have multiple environments, but only one can be marked as default

#### 3. RoutingRule
- **Purpose**: Maps specific WhatsApp IDs to particular environments
- **Key Fields**:
  - `environment`: Foreign key to the target environment
  - `wa_id`: WhatsApp ID (phone number) of the sender
  - `name`: Descriptive name for the rule
- **Constraint**: Each WhatsApp ID can only be mapped to one environment per vendor

## Routing Logic

The system follows a hierarchical routing strategy:

### 1. Webhook Reception
```
POST /webhook/meta/<vendor_code>/
```
- Receives WhatsApp webhook payload
- Extracts vendor code from URL path
- Validates WhatsApp verification tokens for GET requests

### 2. WhatsApp ID Extraction
```python
def get_wa_id_from_payload(payload):
    return payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
```
- Parses the webhook payload to extract the sender's WhatsApp ID
- Uses nested dictionary access with proper error handling

### 3. Routing Decision Process

1. **Cache Lookup**: First checks if routing information is cached
2. **Specific Rule Matching**: Looks for a `RoutingRule` matching the WhatsApp ID and vendor
3. **Default Environment Fallback**: If no specific rule exists, uses the vendor's default environment
4. **Error Handling**: Returns appropriate error responses if no routing configuration is found

### 4. Request Forwarding

- Constructs new HTTP headers including secure variables from vendor configuration
- Forwards the original webhook payload to the determined target URL
- Handles timeouts and HTTP errors gracefully
- Returns the upstream response back to WhatsApp

## Key Features

### Caching
- Uses Django's caching framework to store routing decisions
- Cache key format: `rule:{vendor_code}:{wa_id}`
- 5-minute cache timeout to balance performance and configuration flexibility

### Security
- Encrypted storage of sensitive vendor variables using `django-encrypted-model-fields`
- CSRF exemption for webhook endpoints (required for external API calls)
- Environment variable configuration for secrets

### Logging
- Comprehensive logging with different levels for various components
- Structured logging using custom `log_object` utility
- Error logging to rotating file handlers
- Console logging for general information

### Admin Interface
- Django admin integration for managing vendors, environments, and routing rules
- List views with filtering and search capabilities
- Proper field display and relationships

#### Dozzle Integration
The system includes **Dozzle** for real-time Docker container log monitoring:

**Features:**
- Real-time log streaming from all containers (Django, PostgreSQL, Dozzle)
- Web-based interface with file-based authentication
- Search and filter capabilities across all container logs
- Auto-refresh functionality for continuous monitoring
- Secure access through `users.yml` configuration

**Authentication:**
The logging system uses Dozzle's simple file-based authentication configured in `./dozzle/users.yml`. Users and passwords are managed through this file rather than environment variables.

**Authentication Setup:**
Create `./dozzle/users.yml` file with your user credentials:
```yaml
users:
  admin:
    name: "Administrator"
    password: "your_secure_password"
```

All log access is protected by this authentication system, ensuring secure monitoring of your WhatsApp Router infrastructure.

## Use Cases

### Multi-Environment Deployment
```
Vendor: "acme-corp"
├── Environment: "production" (target: https://api.acme.com/webhook)
├── Environment: "staging" (target: https://staging.acme.com/webhook)
└── Environment: "development" (target: https://dev.acme.com/webhook)
```

### Customer-Specific Routing
```
Routing Rules for vendor "acme-corp":
├── WhatsApp ID "+1234567890" → staging environment
├── WhatsApp ID "+9876543210" → development environment
└── All other IDs → production environment (default)
```

### API Key Management
```json
{
  "Authorization": "Bearer abc123...",
  "X-API-Key": "secret-key",
  "X-Custom-Header": "value"
}
```

## Technical Stack

- **Framework**: Django 5.2.3
- **Database**: PostgreSQL with psycopg2
- **Encryption**: django-encrypted-model-fields
- **HTTP Client**: requests library
- **Deployment**: Docker with Gunicorn
- **Environment Management**: python-dotenv

## Configuration

The system uses environment variables for configuration:
- Database connection settings
- Django secret keys
- WhatsApp verification tokens
- Allowed hosts and debug settings

This architecture provides a scalable, secure, and maintainable solution for routing WhatsApp webhook traffic across multiple environments and customers.