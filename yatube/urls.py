from django.contrib import admin
from django.contrib.flatpages.views import flatpage
from django.conf import settings
from django.conf.urls import handler404, handler500 # noqa
from django.conf.urls.static import static
from django.urls import include, path

handler404 = 'posts.views.page_not_found' # noqa
handler500 = 'posts.views.server_error' # noqa

urlpatterns = [
    path('auth/',
         include('users.urls')),
    path('auth/',
         include('django.contrib.auth.urls')),
    path('admin/',
         admin.site.urls),
    path('about/',
         include('django.contrib.flatpages.urls')),
    path('',
         include('posts.urls')),
]

urlpatterns += [
    path('about/about-us/',
         flatpage,
         {'url': 'about/about-us/'},
         name='about'),
    path('about/terms/',
         flatpage,
         {'url': 'about/terms/'},
         name='terms'),
    path('about/about-author/',
         flatpage,
         {'url': 'about/about-author/'},
         name='about-author'),
    path('about/about-spec/',
         flatpage,
         {'url': 'about/about-spec/'},
         name='about-spec'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += (
        path('__debug__/', include(debug_toolbar.urls)),
    )
