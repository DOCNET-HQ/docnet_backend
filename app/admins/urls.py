from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path(
        '',
        views.AdminListView.as_view(),
        name='admin-list'
    ),
    path(
        '<uuid:id>/',
        views.AdminDetailView.as_view(),
        name='admin-detail'
    ),
    path(
        '<uuid:id>/update/',
        views.AdminUpdateView.as_view(),
        name='admin-update'
    ),
    path(
        '<uuid:id>/delete/',
        views.AdminDeleteView.as_view(),
        name='admin-delete'
    ),
    path(
        'my-profile/',
        views.MyAdminProfileView.as_view(),
        name='my-admin-profile'
    ),
    path(
        'my-basic-profile/',
        views.MyBasicAdminProfileView.as_view(),
        name='admin-basic-info'
    )
]
