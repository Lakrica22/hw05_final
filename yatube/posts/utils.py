from django.core.paginator import Paginator

POSTS_ON_LIST: int = 10


def paginator_view(request, queryset):
    paginator = Paginator(queryset, POSTS_ON_LIST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
