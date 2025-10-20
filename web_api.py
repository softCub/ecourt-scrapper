#!/usr/bin/env python3
"""
eCourts Scraper Web API
Simple Flask-based REST API for the eCourts scraper
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from ecourts_scraper import ECourtsScraper
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize scraper
scraper = ECourtsScraper()


@app.route('/')
def home():
    """API documentation page"""
    return jsonify({
        'name': 'eCourts India Scraper API',
        'version': '1.0.0',
        'endpoints': {
            '/api/search/cnr': 'POST - Search by CNR number',
            '/api/search/case': 'POST - Search by case details',
            '/api/listing/check': 'POST - Check case listing',
            '/api/causelist': 'GET - Download cause list',
            '/health': 'GET - Health check'
        },
        'documentation': '/docs'
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/search/cnr', methods=['POST'])
def search_by_cnr():
    """
    Search case by CNR number
    
    Request Body:
    {
        "cnr": "DLNC01234567890",
        "state_code": "DL",
        "district_code": "1"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'cnr' not in data:
            return jsonify({
                'error': 'CNR number is required'
            }), 400
        
        # Update scraper config if provided
        if 'state_code' in data:
            scraper.state_code = data['state_code']
        if 'district_code' in data:
            scraper.district_code = data['district_code']
        
        # Fetch case details
        case_details = scraper.get_case_by_cnr(data['cnr'])
        
        if not case_details:
            return jsonify({
                'error': 'Case not found or error fetching details'
            }), 404
        
        return jsonify({
            'success': True,
            'data': case_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/search/case', methods=['POST'])
def search_by_case():
    """
    Search case by case details
    
    Request Body:
    {
        "case_type": "CS",
        "case_number": "123",
        "case_year": "2024",
        "state_code": "DL",
        "district_code": "1"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['case_type', 'case_number', 'case_year']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Update scraper config if provided
        if 'state_code' in data:
            scraper.state_code = data['state_code']
        if 'district_code' in data:
            scraper.district_code = data['district_code']
        
        # Fetch case details
        case_details = scraper.get_case_by_details(
            data['case_type'],
            data['case_number'],
            data['case_year']
        )
        
        if not case_details:
            return jsonify({
                'error': 'Case not found or error fetching details'
            }), 404
        
        return jsonify({
            'success': True,
            'data': case_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/listing/check', methods=['POST'])
def check_listing():
    """
    Check if case is listed
    
    Request Body:
    {
        "cnr": "DLNC01234567890",  // OR case_type, case_number, case_year
        "check_today": true,
        "check_tomorrow": true,
        "state_code": "DL",
        "district_code": "1"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Request body is required'
            }), 400
        
        # Update scraper config if provided
        if 'state_code' in data:
            scraper.state_code = data['state_code']
        if 'district_code' in data:
            scraper.district_code = data['district_code']
        
        # Get case details first
        case_details = None
        if 'cnr' in data:
            case_details = scraper.get_case_by_cnr(data['cnr'])
        elif all(k in data for k in ['case_type', 'case_number', 'case_year']):
            case_details = scraper.get_case_by_details(
                data['case_type'],
                data['case_number'],
                data['case_year']
            )
        else:
            return jsonify({
                'error': 'Provide either CNR or case details (type, number, year)'
            }), 400
        
        if not case_details:
            return jsonify({
                'error': 'Case not found'
            }), 404
        
        # Check listings
        results = {
            'case_details': case_details,
            'listings': []
        }
        
        if data.get('check_today', False):
            today = datetime.now()
            listing = scraper.check_listing(case_details, today)
            if listing:
                results['listings'].append({
                    'day': 'today',
                    **listing
                })
        
        if data.get('check_tomorrow', False):
            tomorrow = datetime.now() + timedelta(days=1)
            listing = scraper.check_listing(case_details, tomorrow)
            if listing:
                results['listings'].append({
                    'day': 'tomorrow',
                    **listing
                })
        
        return jsonify({
            'success': True,
            'data': results,
            'is_listed': len(results['listings']) > 0,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/causelist', methods=['GET'])
def get_cause_list():
    """
    Get cause list for a date
    
    Query Parameters:
    - date: today or tomorrow (default: today)
    - state_code: State code
    - district_code: District code
    """
    try:
        date_param = request.args.get('date', 'today').lower()
        
        if date_param == 'today':
            date = datetime.now()
        elif date_param == 'tomorrow':
            date = datetime.now() + timedelta(days=1)
        else:
            return jsonify({
                'error': 'Invalid date parameter. Use "today" or "tomorrow"'
            }), 400
        
        # Update scraper config if provided
        if request.args.get('state_code'):
            scraper.state_code = request.args.get('state_code')
        if request.args.get('district_code'):
            scraper.district_code = request.args.get('district_code')
        
        # Download cause list
        filename = scraper.download_cause_list(date, output_dir='downloads')
        
        if not filename:
            return jsonify({
                'error': 'Failed to download cause list'
            }), 500
        
        # Read and return the cause list
        with open(filename, 'r', encoding='utf-8') as f:
            import json
            cause_list = json.load(f)
        
        return jsonify({
            'success': True,
            'data': cause_list,
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/docs')
def documentation():
    """API documentation"""
    docs = {
        'title': 'eCourts India Scraper API Documentation',
        'version': '1.0.0',
        'base_url': request.host_url,
        'endpoints': [
            {
                'path': '/api/search/cnr',
                'method': 'POST',
                'description': 'Search case by CNR number',
                'request_body': {
                    'cnr': 'string (required)',
                    'state_code': 'string (optional)',
                    'district_code': 'string (optional)'
                },
                'example': {
                    'cnr': 'DLNC01234567890',
                    'state_code': 'DL',
                    'district_code': '1'
                }
            },
            {
                'path': '/api/search/case',
                'method': 'POST',
                'description': 'Search case by case details',
                'request_body': {
                    'case_type': 'string (required)',
                    'case_number': 'string (required)',
                    'case_year': 'string (required)',
                    'state_code': 'string (optional)',
                    'district_code': 'string (optional)'
                },
                'example': {
                    'case_type': 'CS',
                    'case_number': '123',
                    'case_year': '2024',
                    'state_code': 'DL'
                }
            },
            {
                'path': '/api/listing/check',
                'method': 'POST',
                'description': 'Check if case is listed today/tomorrow',
                'request_body': {
                    'cnr': 'string (required if no case details)',
                    'case_type': 'string (required if no CNR)',
                    'case_number': 'string (required if no CNR)',
                    'case_year': 'string (required if no CNR)',
                    'check_today': 'boolean (optional)',
                    'check_tomorrow': 'boolean (optional)',
                    'state_code': 'string (optional)',
                    'district_code': 'string (optional)'
                },
                'example': {
                    'cnr': 'DLNC01234567890',
                    'check_today': True,
                    'check_tomorrow': True
                }
            },
            {
                'path': '/api/causelist',
                'method': 'GET',
                'description': 'Get entire cause list for a date',
                'query_params': {
                    'date': 'today or tomorrow (default: today)',
                    'state_code': 'string (optional)',
                    'district_code': 'string (optional)'
                },
                'example': '/api/causelist?date=today&state_code=DL'
            }
        ]
    }
    
    return jsonify(docs)


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Run the Flask app
    print("🚀 Starting eCourts Scraper API...")
    print("📝 API Documentation: http://localhost:5000/docs")
    print("❤️  Health Check: http://localhost:5000/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)