from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import User, Category, AuctionListing, Comment, Bid

def listing_view(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    check_listing_in_watchlist = request.user in listing_data.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_data)
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "check_listing_in_watchlist": check_listing_in_watchlist,
        "all_comments": all_comments
    })

def add_bid(request, id):
    new_bid = request.POST.get('starting_bid')
    listing_data = AuctionListing.objects.get(pk=id)
    
    if new_bid and int(new_bid) > listing_data.starting_bid.bid:
        updated_bid = Bid(user=request.user, bid=int(new_bid))
        updated_bid.save()
        listing_data.starting_bid = updated_bid
        listing_data.save()
        
        return render(request, "auctions/listing.html", {
            "listing": listing_data,
            "message": "Bid was updated successfully",
            "updated": True
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listing_data,
            "message": "Bid update failed",
            "updated": False
        })


def add_comment(request, id):
    current_user = request.user
    listing_data = AuctionListing.objects.get(pk=id)
    message = request.POST['new_comment']

    new_comment = Comment(
        author = current_user,
        listing = listing_data,
        message = message
    )

    new_comment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist_view(request):
    if request.user.is_authenticated:
        listings = request.user.listing_watchlist.all()
        return render(request, "auctions/watchlist.html", {
            "listings": listings
        })
    else:
        return HttpResponseRedirect(reverse("login"))

def remove_watchlist(request, id):
    listing_data = AuctionListing.objects.get(pk=id)  
    current_user = request.user
    listing_data.watchlist.remove(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def add_watchlist(request, id):
    listing_data = AuctionListing.objects.get(pk=id)  
    current_user = request.user
    listing_data.watchlist.add(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def index(request):
    active_listings = AuctionListing.objects.filter(is_active=True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listings,
        "categories": all_categories,
    })

def display(request):
    if request.method == "POST":
        category_id = request.POST.get('category')
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            active_listings = AuctionListing.objects.filter(is_active=True, category=category)
        else:
            active_listings = AuctionListing.objects.filter(is_active=True)

        all_categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": active_listings,
            "categories": all_categories,
        })


def create_listing(request):
    if request.method == "GET":
        all_categories = Category.objects.all()
        return render(request, "auctions/create_listing.html", {
            "categories": all_categories
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        image_url = request.POST["image_url"]
        price = request.POST["starting_bid"]
        category_id = request.POST["category"]
        
        current_user = request.user

        category_data = get_object_or_404(Category, id=category_id)

        bid = Bid(bid=int(price), user=current_user)
        bid.save()

        new_listing = AuctionListing(
            title=title,
            description=description,
            image_url=image_url,
            starting_bid=bid,
            category=category_data,
            owner=current_user,
        )
        new_listing.save()

        return HttpResponseRedirect(reverse("index"))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "validation_error": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "password_error": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "username_error": "Username already exist."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
        
# 1:08:22 / 1:15:02

