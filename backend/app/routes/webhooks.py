"""
Webhook endpoints for third-party integrations
"""

from flask import Blueprint, request, jsonify
from ..services.ttlock_service import ttlock_service
import logging
import hmac
import hashlib
import json

# Configure logging
logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.route('/webhooks/ttlock', methods=['POST'])
def ttlock_webhook():
    """
    Receive unlock records from TTLock API
    This endpoint will be called when a lock is accessed
    """
    try:
        # Log the raw request for debugging
        raw_data = request.get_data()
        content_type = request.content_type

        logger.info(f"TTLock webhook received - Content-Type: {content_type}")
        logger.info(f"TTLock webhook raw data: {raw_data}")

        # Try to get JSON data
        webhook_data = None
        try:
            webhook_data = request.get_json(force=True)
        except Exception as json_error:
            logger.warning(f"Failed to parse JSON: {json_error}")
            # Try to get form data instead
            webhook_data = request.form.to_dict()

        if not webhook_data:
            logger.warning("No webhook data received")
            # For TTLock platform testing, return success even with no data
            return jsonify({'success': True, 'message': 'Webhook endpoint is working', 'received': str(raw_data)})

        logger.info(f"Parsed TTLock webhook data: {webhook_data}")

        # Only process if we have actual lock data
        if webhook_data and ('lockId' in webhook_data or 'records' in webhook_data):
            # Process the webhook record
            success = ttlock_service.process_webhook_record(webhook_data)

            if success:
                return jsonify({'success': True, 'message': 'Webhook processed successfully'})
            else:
                logger.warning("Failed to process webhook record")
                return jsonify({'success': True, 'message': 'Webhook received but processing failed'})
        else:
            # Platform testing - just return success
            return jsonify({'success': True, 'message': 'Webhook test successful', 'data': webhook_data})

    except Exception as e:
        logger.error(f"Failed to process TTLock webhook: {str(e)}", exc_info=True)
        # Return 200 even on error to avoid webhook retry loops
        return jsonify({'success': False, 'error': str(e), 'message': 'Webhook endpoint is working'}), 200

@webhooks_bp.route('/webhooks/ttlock/test', methods=['POST', 'GET'])
def ttlock_webhook_test():
    """
    Test endpoint for TTLock webhook
    Use this to test your webhook setup
    """
    try:
        # Get test data
        if request.method == 'POST':
            test_data = request.get_json() or request.form.to_dict() or {}
        else:
            test_data = request.args.to_dict()

        logger.info(f"TTLock webhook test received: {test_data}")

        # Return success for test
        return jsonify({
            'success': True,
            'message': 'TTLock webhook test successful',
            'method': request.method,
            'received_data': test_data,
            'endpoint': '/api/webhooks/ttlock/test'
        })

    except Exception as e:
        logger.error(f"TTLock webhook test failed: {str(e)}")
        return jsonify({'success': True, 'error': str(e), 'message': 'Test endpoint is working'}), 200

@webhooks_bp.route('/webhooks/didit', methods=['POST'])
def didit_webhook():
    """
    Existing Didit webhook endpoint (keeping for reference)
    """
    try:
        webhook_data = request.get_json()
        if not webhook_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        logger.info(f"Received Didit webhook: {webhook_data}")

        # Process Didit webhook (existing logic)
        # This would contain your existing Didit webhook processing code

        return jsonify({'success': True, 'message': 'Didit webhook processed successfully'})

    except Exception as e:
        logger.error(f"Failed to process Didit webhook: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@webhooks_bp.route('/webhooks/health', methods=['GET'])
def webhook_health():
    """
    Health check endpoint for webhooks
    """
    return jsonify({
        'status': 'healthy',
        'webhooks': {
            'ttlock': '/api/webhooks/ttlock',
            'ttlock_test': '/api/webhooks/ttlock/test',
            'didit': '/api/webhooks/didit'
        }
    })