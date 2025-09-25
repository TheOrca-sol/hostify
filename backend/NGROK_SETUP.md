# Ngrok Setup for Hostify Webhooks

This document explains how to set up ngrok to handle webhooks for both Didit KYC and TTLock smart locks.

## Prerequisites

1. Install ngrok: https://ngrok.com/download
2. Sign up for ngrok account and get auth token
3. Configure ngrok authentication: `ngrok authtoken YOUR_TOKEN`

## Setup Commands

### Start Backend Server
```bash
cd backend
source venv/bin/activate
export FLASK_APP=app
flask run --port=5000
```

### Start Ngrok Tunnel
```bash
# In a separate terminal
ngrok http 5000
```

This will provide you with:
- HTTP URL: `http://abc123.ngrok.io`
- HTTPS URL: `https://abc123.ngrok.io` (use this for webhooks)

## Webhook Endpoints

### TTLock Webhook
- **URL**: `https://your-ngrok-url.ngrok.io/api/webhooks/ttlock`
- **Method**: POST
- **Purpose**: Receives unlock/lock records from TTLock API
- **Test URL**: `https://your-ngrok-url.ngrok.io/api/webhooks/ttlock/test`

### Didit KYC Webhook
- **URL**: `https://your-ngrok-url.ngrok.io/api/webhooks/didit`
- **Method**: POST
- **Purpose**: Receives KYC verification results

### Health Check
- **URL**: `https://your-ngrok-url.ngrok.io/api/webhooks/health`
- **Method**: GET
- **Purpose**: Verify webhook endpoints are working

## Configuration Steps

### 1. Configure TTLock Platform
1. Log into TTLock developer console
2. Navigate to your application settings
3. Set callback URL to: `https://your-ngrok-url.ngrok.io/api/webhooks/ttlock`
4. Save settings

### 2. Configure Didit KYC
1. Log into Didit dashboard
2. Navigate to webhook settings
3. Set webhook URL to: `https://your-ngrok-url.ngrok.io/api/webhooks/didit`
4. Save settings

## Testing Webhooks

### TTLock Webhook Test
```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/webhooks/ttlock/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Didit Webhook Test
```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/webhooks/didit \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Health Check
```bash
curl https://your-ngrok-url.ngrok.io/api/webhooks/health
```

## Production Considerations

### For Production Deployment:
1. **Use a proper domain**: Replace ngrok with your production domain
2. **SSL Certificate**: Ensure HTTPS is properly configured
3. **Webhook Security**: Add signature verification for production
4. **Rate Limiting**: Implement rate limiting on webhook endpoints
5. **Monitoring**: Set up logging and monitoring for webhook calls

### Production URLs would be:
- TTLock: `https://yourdomain.com/api/webhooks/ttlock`
- Didit: `https://yourdomain.com/api/webhooks/didit`

## Troubleshooting

### Common Issues:

1. **Ngrok tunnel not accessible**
   - Check if ngrok is running
   - Verify port 5000 is correct
   - Check firewall settings

2. **Webhooks not received**
   - Verify ngrok URL is correct in platform settings
   - Check ngrok web interface at http://127.0.0.1:4040
   - Review Flask application logs

3. **SSL/HTTPS issues**
   - Always use HTTPS URLs for webhooks
   - Most platforms require HTTPS for security

### Monitoring Webhooks:
- Ngrok web interface: http://127.0.0.1:4040
- Flask application logs
- Platform webhook delivery logs (TTLock/Didit dashboards)

## Example Workflow

1. Start backend: `flask run --port=5000`
2. Start ngrok: `ngrok http 5000`
3. Copy HTTPS URL from ngrok
4. Update .env file with ngrok URL
5. Configure webhook URLs in TTLock and Didit platforms
6. Test webhooks using curl commands above
7. Monitor in ngrok web interface

## Security Notes

- **Development Only**: This setup is for development/testing
- **Ngrok tunnels expire**: Free ngrok URLs change on restart
- **No authentication**: Add proper authentication for production
- **Logging**: Monitor all webhook traffic carefully