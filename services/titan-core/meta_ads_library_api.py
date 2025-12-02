"""
Meta Ads Library API Server - Agent 26 Integration
Provides HTTP endpoints for the Ad Spy Dashboard to access Meta Ads Library data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from typing import Dict, List, Any
import traceback

from meta.ads_library_scraper import (
    RealAdsLibraryScraper,
    AdLibraryAd,
    AdPlatform,
    AdActiveStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize Meta Ads Library scraper
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
if not META_ACCESS_TOKEN:
    logger.warning('META_ACCESS_TOKEN not set. Meta Ads Library API will not function.')
    scraper = None
else:
    scraper = RealAdsLibraryScraper(META_ACCESS_TOKEN)
    logger.info('✅ Meta Ads Library scraper initialized')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'meta-ads-library-api',
        'scraper_initialized': scraper is not None
    })


@app.route('/meta/ads-library/search', methods=['POST'])
def search_ads():
    """
    POST /meta/ads-library/search
    Search Meta Ads Library with filters.

    Request body:
    {
        "search_terms": "weight loss",
        "countries": ["US", "GB"],
        "platforms": ["facebook", "instagram"],
        "media_type": "VIDEO",  // "ALL", "VIDEO", "IMAGE"
        "active_status": "ACTIVE",  // "ALL", "ACTIVE", "INACTIVE"
        "limit": 100
    }
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        data = request.get_json()

        search_terms = data.get('search_terms', '')
        countries = data.get('countries', ['US'])
        platforms = data.get('platforms', [])
        media_type = data.get('media_type', 'ALL')
        active_status_str = data.get('active_status', 'ACTIVE')
        limit = data.get('limit', 100)

        # Convert platforms to enum
        platform_enums = []
        for platform in platforms:
            try:
                platform_enums.append(AdPlatform(platform))
            except ValueError:
                logger.warning(f'Invalid platform: {platform}')

        # Convert active status to enum
        try:
            active_status = AdActiveStatus[active_status_str]
        except (KeyError, ValueError):
            active_status = AdActiveStatus.ACTIVE

        logger.info(f'Searching ads: terms="{search_terms}", countries={countries}, limit={limit}')

        # Perform search
        ads = scraper.search_ads(
            search_terms=search_terms if search_terms else None,
            ad_reached_countries=countries,
            ad_active_status=active_status,
            publisher_platforms=platform_enums if platform_enums else None,
            media_type=media_type if media_type != 'ALL' else None,
            limit=limit
        )

        # Convert to dict
        ads_data = [ad.to_dict() for ad in ads]

        logger.info(f'Found {len(ads_data)} ads')

        return jsonify(ads_data)

    except Exception as e:
        logger.error(f'Search error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/page/<page_id>', methods=['GET'])
def get_page_ads(page_id: str):
    """
    GET /meta/ads-library/page/:page_id
    Get all ads from a specific Facebook/Instagram page.

    Query params:
    - limit: int (default 100)
    - active_only: bool (default true)
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        limit = int(request.args.get('limit', 100))
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        logger.info(f'Fetching ads for page: {page_id}, limit={limit}, active_only={active_only}')

        ads = scraper.get_page_ads(
            page_id=page_id,
            limit=limit,
            active_only=active_only
        )

        ads_data = [ad.to_dict() for ad in ads]

        logger.info(f'Found {len(ads_data)} ads for page {page_id}')

        return jsonify(ads_data)

    except Exception as e:
        logger.error(f'Page ads fetch error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/ad/<ad_archive_id>', methods=['GET'])
def get_ad_details(ad_archive_id: str):
    """
    GET /meta/ads-library/ad/:ad_archive_id
    Get detailed information for a specific ad.
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        logger.info(f'Fetching details for ad: {ad_archive_id}')

        ad = scraper.get_ad_details(ad_archive_id)

        logger.info(f'Successfully fetched ad details for {ad_archive_id}')

        return jsonify(ad.to_dict())

    except Exception as e:
        logger.error(f'Ad details fetch error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/analyze', methods=['POST'])
def analyze_patterns():
    """
    POST /meta/ads-library/analyze
    Analyze patterns across multiple ads.

    Request body:
    {
        "ads": [<AdLibraryAd objects>]
    }
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        data = request.get_json()
        ads_data = data.get('ads', [])

        if not ads_data:
            return jsonify({'error': 'No ads provided'}), 400

        # Convert dict data back to AdLibraryAd objects
        ads = []
        for ad_dict in ads_data:
            try:
                ad = AdLibraryAd(**ad_dict)
                ads.append(ad)
            except Exception as e:
                logger.warning(f'Failed to parse ad: {e}')

        logger.info(f'Analyzing patterns for {len(ads)} ads')

        analysis = scraper.analyze_ad_patterns(ads)

        logger.info(f'Analysis complete')

        return jsonify(analysis)

    except Exception as e:
        logger.error(f'Pattern analysis error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/batch', methods=['POST'])
def batch_scrape():
    """
    POST /meta/ads-library/batch
    Batch scrape multiple search terms.

    Request body:
    {
        "queries": ["query1", "query2", ...],
        "countries": ["US"],
        "limit_per_query": 50
    }
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        data = request.get_json()

        queries = data.get('queries', [])
        countries = data.get('countries', ['US'])
        limit_per_query = data.get('limit_per_query', 50)

        if not queries:
            return jsonify({'error': 'No queries provided'}), 400

        logger.info(f'Batch scraping {len(queries)} queries')

        results = scraper.batch_scrape(
            queries=queries,
            countries=countries,
            limit_per_query=limit_per_query
        )

        # Convert ads to dict
        results_dict = {}
        for query, ads in results.items():
            results_dict[query] = [ad.to_dict() for ad in ads]

        total_ads = sum(len(ads) for ads in results.values())
        logger.info(f'Batch scrape complete: {total_ads} total ads')

        return jsonify(results_dict)

    except Exception as e:
        logger.error(f'Batch scrape error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/competitor/<page_ids>', methods=['GET'])
def get_competitor_ads(page_ids: str):
    """
    GET /meta/ads-library/competitor/:page_ids
    Get competitor ads for multiple pages.

    page_ids: Comma-separated list of page IDs
    Query params:
    - days_back: int (default 30)
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        page_id_list = page_ids.split(',')
        days_back = int(request.args.get('days_back', 30))

        logger.info(f'Fetching competitor ads for {len(page_id_list)} pages, {days_back} days back')

        ads = scraper.get_competitor_ads(
            competitor_page_ids=page_id_list,
            days_back=days_back
        )

        ads_data = [ad.to_dict() for ad in ads]

        logger.info(f'Found {len(ads_data)} competitor ads')

        return jsonify(ads_data)

    except Exception as e:
        logger.error(f'Competitor ads fetch error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/meta/ads-library/export', methods=['POST'])
def export_ads():
    """
    POST /meta/ads-library/export
    Export ads to JSON file.

    Request body:
    {
        "ads": [<AdLibraryAd objects>],
        "output_path": "/path/to/output.json"
    }
    """
    if not scraper:
        return jsonify({
            'error': 'Meta Ads Library scraper not initialized. Check META_ACCESS_TOKEN.'
        }), 503

    try:
        data = request.get_json()
        ads_data = data.get('ads', [])
        output_path = data.get('output_path', '/tmp/ads_export.json')

        # Convert dict data back to AdLibraryAd objects
        ads = []
        for ad_dict in ads_data:
            try:
                ad = AdLibraryAd(**ad_dict)
                ads.append(ad)
            except Exception as e:
                logger.warning(f'Failed to parse ad: {e}')

        logger.info(f'Exporting {len(ads)} ads to {output_path}')

        file_path = scraper.export_to_json(ads, output_path)

        logger.info(f'Export complete: {file_path}')

        return jsonify({
            'message': 'Export successful',
            'file_path': file_path,
            'total_ads': len(ads)
        })

    except Exception as e:
        logger.error(f'Export error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8004))
    logger.info(f'Starting Meta Ads Library API server on port {port}')
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')
