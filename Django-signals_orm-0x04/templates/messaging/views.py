from django.core.cache import cache
from django.http import HttpResponse

@login_required
def clear_cache(request):
    """
    View to clear cache (for testing purposes).
    Only allow for superusers in production.
    """
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to clear cache.")
        return redirect('messaging:conversation_list')
    
    cache.clear()
    messages.success(request, "Cache cleared successfully.")
    return redirect('messaging:conversation_list')

@login_required
def cache_stats(request):
    """
    View to show cache statistics (for testing purposes).
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Note: LocMemCache doesn't have detailed stats, but we can show some info
    cache_info = {
        'backend': str(cache._cache),
        'cache_size': len(cache._cache) if hasattr(cache, '_cache') else 'N/A',
    }
    
    return JsonResponse(cache_info)
