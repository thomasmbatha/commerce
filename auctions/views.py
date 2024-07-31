from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import User, Category, AuctionListing, Comment, Bid

def listing_view(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    check_listing_in_watchlist = request.user.is_authenticated and request.user in listing_data.watchlist.all()
    all_comments = Comment.objects.filter(listing=listing_data)
    is_owner = request.user.is_authenticated and request.user == listing_data.owner
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "check_listing_in_watchlist": check_listing_in_watchlist,
        "all_comments": all_comments,
        "is_owner": is_owner,
    })


def close_auction(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated and request.user.username == listing_data.owner.username:
        # Remove listing from all users' watchlists
        for user in listing_data.watchlist.all():
            user.listing_watchlist.remove(listing_data)
        
        # Optionally delete the listing or just mark it as inactive
        listing_data.is_active = False
        listing_data.save()
        
        messages.success(request, "Congratulations! You have closed this auction.")
    else:
        messages.error(request, "You do not have permission to close this auction.")
    
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def add_bid(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    is_owner = request.user.is_authenticated and request.user.username == listing_data.owner.username
    new_bid = request.POST.get('starting_bid')
    
    if new_bid and int(new_bid) > listing_data.starting_bid.bid:
        updated_bid = Bid(user=request.user, bid=int(new_bid))
        updated_bid.save()
        listing_data.starting_bid = updated_bid
        listing_data.save()
        messages.success(request, "Bid was updated successfully.")
    else:
        messages.error(request, "Bid update failed. Ensure your bid is higher than the current bid.")
    
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def add_comment(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    message = request.POST.get('new_comment')
    
    if message:
        new_comment = Comment(author=request.user, listing=listing_data, message=message)
        new_comment.save()
        messages.success(request, "Comment added successfully.")
    else:
        messages.error(request, "Comment cannot be empty.")
    
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist_view(request):
    if request.user.is_authenticated:
        # Fetch only active listings for the current user
        listings = request.user.listing_watchlist.filter(is_active=True)
        return render(request, "auctions/watchlist.html", {
            "listings": listings
        })
    else:
        return HttpResponseRedirect(reverse("login"))


def remove_watchlist(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.remove(request.user)
        messages.success(request, "Removed from watchlist.")
    else:
        messages.error(request, "You need to be logged in to remove from watchlist.")
    
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def add_watchlist(request, id):
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.add(request.user)
        messages.success(request, "Added to watchlist.")
    else:
        messages.error(request, "You need to be logged in to add to watchlist.")
    
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
    else:
        return HttpResponseRedirect(reverse("index"))

def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        image_url = request.POST.get("image_url")
        price = request.POST.get("starting_bid")
        category_id = request.POST.get("category")
        
        if not all([title, description, image_url, price, category_id]):
            messages.error(request, "All fields are required.")
            return render(request, "auctions/create_listing.html", {
                "categories": Category.objects.all()
            })
        
        category_data = get_object_or_404(Category, id=category_id)
        bid = Bid(bid=int(price), user=request.user)
        bid.save()
        
        new_listing = AuctionListing(
            title=title,
            description=description,
            image_url=image_url,
            starting_bid=bid,
            category=category_data,
            owner=request.user,
        )
        new_listing.save()
        messages.success(request, "Listing created successfully.")
        return HttpResponseRedirect(reverse("index"))
    
    return render(request, "auctions/create_listing.html", {
        "categories": Category.objects.all()
    })

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, "Invalid username and/or password.")
    
    return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        
        if password != confirmation:
            messages.error(request, "Passwords must match.")
            return render(request, "auctions/register.html")
        
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return HttpResponseRedirect(reverse("index"))
        except IntegrityError:
            messages.error(request, "Username already exists.")
    
    return render(request, "auctions/register.html")
