from django.contrib import admin

from .models import Post, Group, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "slug",)
    search_fields = ("title",)
    list_filter = ("slug",)
    empty_value_display = "-пусто-"
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Group, GroupAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "author", "text", "created",)
    search_fields = ("author",)
    list_filter = ("created",)
    empty_value_display = "-пусто-"


admin.site.register(Comment, CommentAdmin)


class FollowAdmin(admin.ModelAdmin):
    list_display = ("pk", "author", "user")
    search_fields = ("author",)
    empty_value_display = "-пусто-"


admin.site.register(Follow, FollowAdmin)
