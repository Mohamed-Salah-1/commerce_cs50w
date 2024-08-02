from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, Category, Bid, Comment

# Add comment form
class CommentAdmin(admin.ModelAdmin):
    list_display = ('commenter', 'listing', 'text')
    
    def __str__(self):
        # return first 10 characters of the text
        return self.text[:10]
    
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'final_price', 'created_by', 'highest_bidder', 'isActive')
    
    def highest_bidder(self, obj):
        highest_bid = Bid.objects.filter(listing=obj).order_by('-amount').first()
        return highest_bid.bidder.username if highest_bid else None
    
    highest_bidder.short_description = 'Highest Bidder'
    
    def __str__(self):
        # return first 10 characters of the title
        return self.title[:10]

admin.site.register(User, UserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Comment, CommentAdmin)