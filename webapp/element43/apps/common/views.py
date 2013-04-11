# Utils
import ujson as ujson

# Imports for memcache
import pylibmc
from apps.common.util import get_memcache_client, dictfetchall

# Template and context-related imports
from django.db import connection
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages

# JSON for the live search
from django.utils import simplejson

# Models
from eve_db.models import InvType, StaStation
from apps.market_data.models import Orders, ItemRegionStat, ItemRegionStatHistory, EmdrStats, OrderHistory

"""
Those are our views. We have to use the RequestContext for CSRF protection,
since we have a form (search) in every single of our views, as they extend 'base.haml'.
"""


def home(request):

    """
    Returns our static home template with a CSRF protection for our search as well as the stats layout.
    """

    type_ids = [34, 35, 36, 37, 38, 39, 40, 29668]
    region = 10000002

    types = InvType.objects.filter(id__in=type_ids)

    # Create context for CSRF protection
    rcontext = RequestContext(
        request, {'type_ids': type_ids, 'types': types, 'region': region})

    return render_to_response('home.haml', rcontext)


def about_page(request):

    """
    Returns the about page with information about the site and contact information
    """

    rcontext = RequestContext(request, {})

    return render_to_response('about_page.haml', rcontext)


def api_docs(request):

    """
    Returns the about page with information about the API
    """

    rcontext = RequestContext(request, {})

    return render_to_response('api_docs.haml', rcontext)


def stats_json(request, region_id):

    """
    Returns stat JSON for the front page
    """

    # Connect to memcache
    mc = get_memcache_client()

    # Cursor for faster counting
    cursor = connection.cursor()

    # Collect stats

    # 1. Platform stats
    # these is a disconnect between history and history messages/min -- history is orderhistory table which is all rows
    # message per min is based on emdr which is multiple rows in one message.

    if (mc.get("e43-stats-activeorders") is not None):
        active_orders = mc.get("e43-stats-activeorders")
    else:
        active_orders = Orders.active.count()
        mc.set("e43-stats-activeorders", active_orders, time=3600)

    if (mc.get("e43-stats-archivedorders") is not None):
        archived_orders = mc.get("e43-stats-archivedorders")
    else:
        cursor.execute("SELECT reltuples::bigint AS estimate FROM pg_class WHERE relname='market_data_archivedorders'")
        archived_orders = dictfetchall(cursor)[0]['estimate']
        mc.set("e43-stats-archivedorders", archived_orders, time=3600)

    if (mc.get("e43-stats-history") is not None):
        history = mc.get("e43-stats-history")
    else:
        cursor.execute("SELECT reltuples::bigint AS estimate FROM pg_class WHERE relname='market_data_orderhistory'")
        history = dictfetchall(cursor)[0]['estimate']
        mc.set("e43-stats-history", history, time=3600)

    new_orders_per_minute = EmdrStats.objects.filter(
        status_type=1).order_by("-message_timestamp")[:1][0].status_count / 5
    updated_orders_per_minute = EmdrStats.objects.filter(
        status_type=2).order_by("-message_timestamp")[:1][0].status_count / 5
    old_orders_per_minute = EmdrStats.objects.filter(
        status_type=3).order_by("-message_timestamp")[:1][0].status_count / 5
    history_messages_per_minute = EmdrStats.objects.filter(
        status_type=4).order_by("-message_timestamp")[:1][0].status_count / 5

    # 2. Minerals and PLEX
    types = request.GET.getlist('type')
    new_types = []

    for item in types:
        new_types.append(int(item))

    types = new_types
    typestats = {}
    cache_item = {}
    buymedian = 0
    sellmedian = 0

    for item in types:

        # Still works if we have no data for that item
        try:
            # check to see if it's in the cache, if so use those values
            if (mc.get("e43-stats" + str(item)) is not None):
                cache_item = ujson.loads(mc.get("e43-stats" + str(item)))
                buymedian = cache_item['buymedian']
                sellmedian = cache_item['sellmedian']
            # otherwise go to the DB for it
            else:

                # Catch error if we don't have any data for that type
                try:
                    region_stats = ItemRegionStat.objects.filter(
                                        mapregion_id=region_id, invtype_id=item)[:2][1]
                    buymedian = region_stats.buymedian
                    sellmedian = region_stats.sellmedian

                except:
                    buymedian = 0
                    sellmedian = 0

            region_stats_history = ItemRegionStatHistory.objects.filter(mapregion_id=region_id, invtype_id=item).order_by("-date")[:1][0]

            # Get Jita prices
            buy = Orders.active.filter(mapsolarsystem=30000142, invtype=item, is_bid=True).order_by("-price")[:1][0].price
            sell = Orders.active.filter(mapsolarsystem=30000142, invtype=item, is_bid=False).order_by("price")[:1][0].price

            stats = {'bid_max': buy,
                     'ask_min': sell,
                     'bid_median': buymedian,
                     'bid_median_move': region_stats_history.buymedian - buymedian,
                     'ask_median': sellmedian,
                     'ask_median_move': region_stats_history.sellmedian - sellmedian}

            if stats:
                typestats[item] = stats

        except pylibmc.Error as e:
            print e

    # Create JSON
    stat_json = simplejson.dumps({'active_orders': active_orders,
                                  'archived_orders': archived_orders,
                                  'history_records': history,
                                  'new_orders': new_orders_per_minute,
                                  'updated_orders': updated_orders_per_minute,
                                  'old_orders': old_orders_per_minute,
                                  'history_messages': history_messages_per_minute,
                                  'typestats': typestats})

    # Return JSON without using any template
    return HttpResponse(stat_json, mimetype='application/json')


def search(request):

    """
    This adds a basic search view to element43.
    The names in the invTypes table are searched with a case insensitive LIKE query.
    """

    # Get query from request
    query = request.POST.get('query', '')

    # Prepare list
    types = []

    # Only if the string is longer than 2 characters start looking in the DB
    if len(query) > 2:

        # Load published type objects matching the name
        types = InvType.objects.filter(name__icontains=query, is_published=True, market_group__isnull=False)

        # Load stations
        stations = StaStation.objects.filter(name__icontains=query)

    # If there is only one hit, directly redirect to quicklook
    if len(types) == 1 and len(stations) == 0:
        type_id = str(types[0].id)
        return HttpResponseRedirect(reverse('quicklook', kwargs={'type_id': type_id}))

    # If there is only one hit, directly redirect to import
    if len(stations) == 1 and len(types) == 0:
        station_id = str(stations[0].id)
        return HttpResponseRedirect(reverse('station', kwargs={'station_id': station_id}))

    # Create Context
    rcontext = RequestContext(request, {'types': types, 'stations': stations})

    # Render template
    return render_to_response('search.haml', rcontext)


def live_search(request):

    """
    This adds a basic live search view to element43.
    The names in the invTypes table are searched with a case insensitive LIKE query and the result is returned as a JSON array of matching names.
    """

    if request.GET.get('query'):
        query = request.GET.get('query')
    else:
        query = ""

    # Prepare lists
    names = []
    ids = []

    # Default to empty array
    json = "{query:'" + query + "', suggestions:[], data:[]}"

    # Only if the string is longer than 2 characters start looking in the DB
    if len(query) > 2:

        # Load published type objects matching the name
        types = InvType.objects.filter(name__icontains=query, is_published=True, market_group__isnull=False)

        for single_type in types:
            names.append(single_type.name)
            ids.append('type_' + str(single_type.id))

        # Load station
        stations = StaStation.objects.filter(name__icontains=query)

        for station in stations:
            names.append(station.name)
            ids.append('station_' + str(station.id))

        # Add additional data for Ajax AutoComplete
        json = {'query': query, 'suggestions': names, 'data': ids}

        # Turn names into JSON
        json = simplejson.dumps(json)

    # Return JSON without using any template
    return HttpResponse(json, mimetype='application/json')


def handler_403(request):

    """
    Redirects user home with an error message.
    """

    messages.warning(request, '403 - Forbidden. You were not supposed to access the page you tried to look at.')
    return HttpResponseRedirect(reverse('home'))


def handler_404(request):

    """
    Redirects user home with an error message.
    """

    messages.warning(
        request, '404 - The page you were looking for could not be found.')
    return HttpResponseRedirect(reverse('home'))


def handler_500(request):

    """
    Redirects user home with an error message.
    """

    messages.error(request, '500 - Internal server error. Looks like there is a bug in Element43. The error was logged and we will try to fix it soon.')
    return HttpResponseRedirect(reverse('home'))
