from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, Category, Bid, Comment

# Add comment form
class CommentAdmin(admin.ModelAdmin):
    list_display = ('commenter', 'listing', 'text')
    
    def __str__(self):
        # return first 10 characters of the text
        return self.text[:10]
admin.site.register(User, UserAdmin)
admin.site.register(Listing)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Comment, CommentAdmin)