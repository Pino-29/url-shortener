from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import URL


@csrf_exempt
@require_http_methods(["POST"])
def create_short_url(request):
    """
    Create a shortened URL.
    
    POST /api/shorten/
    Body: {"url": "https://example.com/very/long/url"}
    
    Returns: {"short_code": "aB3xY9", "short_url": "http://localhost:8000/aB3xY9", "original_url": "..."}
    """
    try:
        data = json.loads(request.body)
        original_url = data.get('url')
        
        if not original_url:
            return JsonResponse({
                'error': 'URL is required'
            }, status=400)
        
        # Check if URL already exists
        existing_url = URL.objects.filter(original_url=original_url, is_active=True).first()
        if existing_url:
            return JsonResponse({
                'short_code': existing_url.short_code,
                'short_url': request.build_absolute_uri(f'/{existing_url.short_code}'),
                'original_url': existing_url.original_url,
                'created_at': existing_url.created_at.isoformat(),
                'message': 'URL already exists'
            }, status=200)
        
        # Create new shortened URL
        url_obj = URL(original_url=original_url)
        url_obj.save()
        
        return JsonResponse({
            'short_code': url_obj.short_code,
            'short_url': request.build_absolute_uri(f'/{url_obj.short_code}'),
            'original_url': url_obj.original_url,
            'created_at': url_obj.created_at.isoformat()
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def redirect_to_original(request, short_code):
    """
    Redirect to the original URL using the short code.
    
    GET /<short_code>
    
    Redirects to the original URL and increments click counter.
    """
    url_obj = get_object_or_404(URL, short_code=short_code, is_active=True)
    
    # Increment the click counter
    url_obj.increment_clicks()
    
    # Redirect to the original URL
    # Ensure the URL has a protocol (http:// or https://)
    original_url = url_obj.original_url
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url
    
    # Redirect to the original URL
    return redirect(original_url)
