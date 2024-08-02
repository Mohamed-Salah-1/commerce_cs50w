from django.db.models import Count
from .models import Notification
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .forms import ListingForm, CommentForm, BidForm
from .models import User, Listing, Bid, Comment, Category


# ------------------------- Index -------------------------------------
def index(request):
    listings = Listing.objects.filter(isActive=True).order_by("-created")
    return render(request, "auctions/index.html", {
        "listings": listings
    })

# -------------------------Login user----------------------------------------
def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            # Check if the user has any notifications
            if Notification.objects.filter(user=user, read=False).exists():
                return redirect('user_dashboard')
            return redirect('index')
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

# -------------------------Register a new user------------------------------------
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        # Ensure password matches confirmation
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

# -------------------------Create a new listing------------------------------------
@login_required(login_url="login")
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.created_by = request.user
            listing.save()
            messages.success(request, "Your listing has been created successfully!")
            return redirect('listing', listing_id=listing.id)
    else:
        form = ListingForm()
    context = {
        "form": form,
    }
    return render(request, "auctions/create_listing.html", context)

# -------------------------listing------------------------------------
def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
    isOwner = listing.created_by == request.user
    if request.method == "POST":
        if "add_to_watchlist" in request.POST:
            user = request.user
            if listing in user.watchlist.all():
                user.watchlist.remove(listing)
            else:
                user.watchlist.add(listing)
            return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

    context = {
        "listing": listing,
        "bid_form": BidForm(),
        "comment_form": CommentForm(),
        "highest_bid": highest_bid.amount if highest_bid else listing.starting_bid,
        "isOwner": isOwner,
    }
    return render(request, "auctions/listing.html", context)
    
''' add new bid'''
@login_required
def add_bid(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    isOwner = listing.created_by == request.user
    
    if request.method == 'POST':
        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            new_bid_amount = bid_form.cleaned_data['amount']
            highest_bid = listing.bids.order_by('-amount').first()
            
            # Validate starting bid against the minimum price
            min_valid_starting_bid = max(listing.price, 0)  # Ensure starting_bid is at least as high as the price
            
            if listing.starting_bid is not None and new_bid_amount < min_valid_starting_bid:
                messages.error(request, "Starting bid cannot be less than the price.")
                return redirect('listing', listing_id=listing_id)
            
            if highest_bid:
                min_valid_bid = max(listing.starting_bid or 0, highest_bid.amount)
            else:
                min_valid_bid = listing.starting_bid or 0
            
            if new_bid_amount > min_valid_bid:
                bid = bid_form.save(commit=False)
                bid.listing = listing
                bid.bidder = request.user
                bid.save()
                messages.success(request, f"Your bid of ${new_bid_amount} was successfully placed!")
            else:
                messages.error(request, f"Bid must be higher than ${min_valid_bid}.")
    
    return redirect('listing', listing_id=listing_id)

@login_required
def closeAuction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if listing.created_by == request.user and listing.isActive:
        listing.isActive = False        
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
        if highest_bid:
            listing.winner = highest_bid.bidder
            listing.final_price = highest_bid.amount
            messages.success(request, f"Auction closed successfully! The winner is ||--> {listing.winner.username} <--|| with a bid of ${listing.final_price}.")

            winner = highest_bid.bidder
            Notification.objects.create(user=winner, message=f"Congratulations! You have won the auction for \"{listing.title}\" with a bid of ${highest_bid.amount}.")
            print(f"Notification created for {winner.username}")
            
        else:
            listing.winner = None
            listing.final_price = listing.starting_bid or listing.price
            messages.warning(request, f"Auction closed successfully! There were no bids on this item. The final price is ${listing.final_price}.")
            
        listing.save()
    elif not listing.isActive:
        messages.info(request, "This auction is already closed.")
    else:
        messages.error(request, "You don't have permission to close this auction.")
    return redirect('listing', listing_id=listing_id)


@login_required    
def add_comment(request, listing_id):
    print("add_comment view called")  # Debugging line
    if request.method == "POST":
        print("Request method is POST")  # Debugging line
        listing = get_object_or_404(Listing, pk=listing_id)
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            print("Comment form is valid")  # Debugging line
            comment = comment_form.save(commit=False)
            comment.listing = listing
            comment.commenter = request.user
            comment.save()
            if comment.pk:
                print("Comment was saved to the database")  # Debugging line
                print(f"Comment saved: {comment.text} by {comment.commenter} on {comment.listing}")
            else:
                print("Comment was not saved to the database")  # Debugging line
        else:
            print("Comment form is invalid")  # Debugging line
            print(comment_form.errors)  # Print form errors for debugging
    else:
        print("Request method is not POST")  # Debugging line
    return redirect('listing', listing_id=listing_id)

        
@login_required
def watchlist(request):
    user = request.user
    watchlist_items = user.watchlist.all()
    context = {
        'watchlist_items': watchlist_items
    }
    return render(request, "auctions/watchlist.html", context)


def categories(request):
    if request.method == "GET":
        categories = Category.objects.annotate(listing_count=Count('listings'))
        return render(request, "auctions/categories.html", {
            "categories": categories
        })
    

def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = category.listings.filter(isActive=True)
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })
    
@login_required
def user_dashboard(request):
    notifications = request.user.notifications.filter(read=False)
    print(f"Notifications for {request.user.username}: {notifications.count()}")
    context = {
        'notifications': notifications,
    }
    return render(request, 'auctions/user_dashboard.html', context)

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('user_dashboard')