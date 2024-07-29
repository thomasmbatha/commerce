from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create_listing"),
    path("display", views.display, name="display"),
    path("listing/<int:id>", views.listing_view, name="listing"),
    path("remove_watchlist/<int:id>", views.remove_watchlist, name="remove_watchlist"),
    path("add_watchlist/<int:id>", views.add_watchlist, name="add_watchlist"),
    path("watchlist", views.watchlist_view, name="watchlist"),
]
