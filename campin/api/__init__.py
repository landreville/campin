"""
Setup for Pyramid application.
"""
import aiopyramid
import asyncpg
import googlemaps
from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.response import Response

from campin.api import campsites


def main(global_config, **app_settings):
    """Build Pyramid application."""
    settings = global_config.copy()
    settings.update(app_settings)

    config = Configurator(settings=settings)
    # We're doing async!
    config.include(aiopyramid)
    config.add_request_method(_db_method, b'db')
    config.add_request_method(_gmaps_client, b'gmaps')
    config.add_subscriber(_add_cors_headers, NewRequest)
    config.include(campsites)
    config.add_notfound_view(_notfound)

    config.scan()

    return config.make_wsgi_app()


async def _db_method(request):
    """
    Return database connection pool. 
     
    Pool will be created if it does not exist and persisted for the application
    lifetime on the registry.
    """
    pool = request.registry.get('pool')
    if not pool:
        pool = request.registry.pool = await _setup_pool(request)

    db = await pool.acquire()

    async def release_db(_):
        await pool.release(db)

    # Put the connection back into the pool at the end of the request
    request.add_finished_callback(release_db)
    return db


async def _setup_pool(request):
    """Setup database pool based on application settings."""
    settings = request.registry.settings

    pool = await asyncpg.create_pool(
        database=settings['db.dbname'],
        user=settings['db.user'],
        password=settings['db.password'],
        host=settings['db.host'],
        min_size=1
    )

    return pool


def _notfound(exc, request):
    """
    Return the NotFound exception unless this is an OPTIONS request.
    
    OPTIONS requests will return an empty response in order to provide the 
    CORS headers.
    """
    if request.method == 'OPTIONS':
        # Used to return CORS headers that are set in NewRequest subscriber
        return Response()
    return exc


def _add_cors_headers(event):
    """
    Event subscriber that will add a response callback to add CORS headers.
    
    Use with NewRequest event::
    
        config.add_subscriber(_add_cors_headers, NewRequest)
    
    """
    def cors_headers(request, response):
        """Add cross-origin headers to the response."""
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '1728000',
        })

    event.request.add_response_callback(cors_headers)


def _gmaps_client(request):
    """Return Google Maps client."""
    return googlemaps.Client(request.registry.settings['gmaps.apikey'])

