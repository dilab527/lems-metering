from django.urls import path
from lemsquery.views import IndexView, DeviceView, DownloadView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('devices/<int:site_id>/download/<str:logical_id>', DownloadView.as_view(), name='devices_download'),
    path('devices/<int:site_id>', DeviceView.as_view(), name='devices'),
]