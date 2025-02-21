from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import User, Category, AuctionListing, Comment, Bid

# View to display a specific auction listing
def listing_view(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user has the listing in their watchlist
    check_listing_in_watchlist = request.user.is_authenticated and request.user in listing_data.watchlist.all()
    # Get all comments for the listing
    all_comments = Comment.objects.filter(listing=listing_data)
    # Check if the current user is the owner of the listing
    is_owner = request.user.is_authenticated and request.user == listing_data.owner
    # Render the listing page with the relevant context
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "check_listing_in_watchlist": check_listing_in_watchlist,
        "all_comments": all_comments,
        "is_owner": is_owner,
    })

# View to close an auction listing
def close_auction(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user is the owner of the listing
    if request.user.is_authenticated and request.user.username == listing_data.owner.username:
        # Remove the listing from all users' watchlists
        for user in listing_data.watchlist.all():
            user.listing_watchlist.remove(listing_data)
        
        # Mark the listing as inactive
        listing_data.is_active = False
        listing_data.save()
        
        messages.success(request, "Congratulations! You have ended this auction.")
    else:
        messages.error(request, "You do not have permission to close this auction.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add a new bid to an auction listing
def add_bid(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user is the owner of the listing
    is_owner = request.user.is_authenticated and request.user.username == listing_data.owner.username
    # Get the new bid amount from the POST request
    new_bid = request.POST.get('starting_bid')
    
    # Check if the new bid is valid and higher than the current bid
    if new_bid and int(new_bid) > listing_data.starting_bid.bid:
        updated_bid = Bid(user=request.user, bid=int(new_bid))
        updated_bid.save()
        listing_data.starting_bid = updated_bid
        listing_data.save()
        messages.success(request, "Bid was updated successfully.")
    else:
        messages.error(request, "Bid update failed. Ensure your bid is higher than the current bid.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add a new comment to an auction listing
def add_comment(request, id):
    # Retrieve the auction listing based on the provided id
    listing_data = get_object_or_404(AuctionListing, pk=id)
    
    # Get the new comment from the POST request
    message = request.POST.get('new_comment')
    
    # Check if the message is not empty
    if message:
        # Create a new Comment object with the current user, listing, and message
        new_comment = Comment(author=request.user, listing=listing_data, message=message)
        # Save the new comment to the database
        new_comment.save()
        # Display a success message to the user
        messages.success(request, "Comment added successfully.")
    else:
        # Display an error message if the comment is empty
        messages.error(request, "Comment cannot be empty.")
    
    # Redirect to the listing page after adding the comment
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to display the current user's watchlist
def watchlist_view(request):
    if request.user.is_authenticated:
        # Fetch only active listings for the current user
        listings = request.user.listing_watchlist.filter(is_active=True)
        return render(request, "auctions/watchlist.html", {
            "listings": listings
        })
    else:
        # Redirect to login page if the user is not authenticated
        return HttpResponseRedirect(reverse("login"))

# View to remove an auction listing from the current user's watchlist
def remove_watchlist(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.remove(request.user)
        messages.success(request, "Removed from watchlist.")
    else:
        messages.error(request, "You need to be logged in to remove from watchlist.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add an auction listing to the current user's watchlist
def add_watchlist(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.add(request.user)
        messages.success(request, "Added to watchlist.")
    else:
        messages.error(request, "You need to be logged in to add to watchlist.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to display all active auction listings and categories on the homepage
def index(request):
    active_listings = AuctionListing.objects.filter(is_active=True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listings,
        "categories": all_categories,
    })


# View to filter auction listings based on category
def display(request):
    selected_category = None
    if request.method == "POST":
        category_id = request.POST.get('category')
        if category_id:
            selected_category = category_id
            category = get_object_or_404(Category, id=category_id)
            active_listings = AuctionListing.objects.filter(is_active=True, category=category)
        else:
            active_listings = AuctionListing.objects.filter(is_active=True)
    else:
        active_listings = AuctionListing.objects.filter(is_active=True)

    all_categories = Category.objects.all()
    return render(request, "auctions/display.html", {
        "listings": active_listings,
        "categories": all_categories,
        "selected_category": selected_category,
    })

# View to display all closed auction listings
def closed_auctions_view(request):
    closed_listings = AuctionListing.objects.filter(is_active=False)
    return render(request, "auctions/closed_auctions.html", {
        "closed_listings": closed_listings,
    })

# View to handle the creation of a new auction listing
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



# View to handle user login
def login_view(request):
    validation_error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            validation_error = "Invalid username and/or password."
    
    return render(request, "auctions/login.html", {
        "validation_error": validation_error,
    })


# View to handle user logout
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return HttpResponseRedirect(reverse("index"))

# View to handle user registration
def register(request):
    username_error = None
    password_error = None

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        
        # Check if password and confirmation match
        if password != confirmation:
            password_error = "Passwords must match."
        else:
            try:
                # Create a new user
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                messages.success(request, "Registration successful.")
                return HttpResponseRedirect(reverse("index"))
            except IntegrityError:
                username_error = "Username already exists."
    
    return render(request, "auctions/register.html", {
        "username_error": username_error,
        "password_error": password_error,
    })

