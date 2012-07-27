from django.contrib.admin import site, ModelAdmin
from models import Column, Category, Post
from django.utils.translation import ugettext_lazy as _ 
from xadrpy.contrib.blog.forms import PostAdminForm, ColumnAdminForm
from django.contrib.admin.options import StackedInline
from xadrpy.contrib.blog.models import CategoryTranslation, Image
from xadrpy.contrib.pages.admin import PageTranslationInlineAdmin

class ColumnAdmin(ModelAdmin):
    form = ColumnAdminForm
    fieldsets = (
        (None, {
            'fields': ('title','slug', 'resolver', 'content')
        }),
        (_("SEO"), {
            'fields': ('overwrite_meta_title', 'meta_title', 'meta_description', 'meta_keywords')
        }),
        (_('Publication'), {
            'fields': ('user', 'group', 'pub_date', 'published', 'enabled', 'visible', 'show_content', 'comments_enabled', 'comments_unlocked','post_comments_enabled','post_comments_unlocked', 'i18n')
        }),
        (_('Design'), {
            'fields': ('menu_title', 'layout_name', 'skin_name','extra_classes', 'view_name','site', 'master', 'language_code', 'image', 'name',)
        }),
        (_('Extra'), {
            'fields': ('created','modified', 'view_count', )
        }),
    )
    list_display = ('title','slug', 'meta_title','menu_title','language_code', 'pub_date','created','modified', 'name', 'user', 'group', 'enabled','published','visible','show_content','comments_enabled','comments_unlocked','view_count')
    list_display_links = ('title', 'slug')
    list_filter = ('user', 'group', 'enabled','published','visible','show_content','comments_enabled','i18n','site','master','language_code')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title','slug','meta_title','name')
    readonly_fields = ('created', 'modified',)
    inlines = (PageTranslationInlineAdmin,)
    
    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.meta['menu_title'] = form.cleaned_data['menu_title'] 
        obj.meta['layout_name'] = form.cleaned_data['layout_name'] 
        obj.meta['skin_name'] = form.cleaned_data['skin_name'] 
        obj.save()    
    
    def menu_title(self, obj):
        return obj.get_meta().meta['menu_title']

    def layout_name(self, obj):
        return obj.get_meta().meta['layout_name']
    
    def skin_name(self, obj):
        return obj.get_meta().meta['skin_name']

class ImageInlineAdmin(StackedInline):
    model = Image
    sortable_field_name = "position"
    extra=0


class PostAdmin(ModelAdmin):
    form = PostAdminForm
    date_hierarchy = 'pub_date'
    fieldsets = (
        (None, {
            'fields': ('column', 'title', 'slug', 'image',)
        }),
        (None, {
            'fields': ( 'content','pub_date', 'published',)
        }),
        (_('Publication'), {
            'fields': ('user', 'group', 'featured', 'weight', 'source', 'source_url')
        }),
        (_("SEO"), {
            'fields': ('overwrite_meta_title', 'meta_title', 'meta_description', 'meta_keywords')
        }),
        (_('Extra'), {
            'fields': ('view_count', 'comments_enabled', 'comments_unlocked','language_code')
        }),
        (_('Relations'), {
            'fields': ('categories','posts', 'pages')
        }),
    )
    filter_horizontal = ("categories", "posts", "pages")
    list_display = ('column', 'title', 'pub_date', 'user', 'featured', 'published','view_count')
    list_display_links = ('title', )
    list_filter = ('column', 'user', 'featured', 'published')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title',)
    actions = ['make_published']
    inlines = (ImageInlineAdmin,)
    
    def make_published(self, request, queryset):
        rows_updated=0
        for obj in queryset:
            obj.published = True
            obj.save()
            rows_updated+=1
        if rows_updated == 1:
            message_bit = "1 posr was"
        else:
            message_bit = "%s posts were" % rows_updated
        self.message_user(request, "%s successfully marked as published." % message_bit)
    make_published.short_description = "Mark selected posts as published"            

class CategoryTranslationInlineAdmin(StackedInline):
    model = CategoryTranslation


class CategoryAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'column', 'language_code')
    list_display_links = ('title', 'slug')
    list_filter = ('column', 'language_code')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title','slug')
    inlines = (CategoryTranslationInlineAdmin,)
    fieldsets = (
        (None, {
            'fields': ('title', 'slug'),
        }),
        (None, {
            'fields': ('parent', 'column', 'language_code', 'description')
        }),
    )


site.register(Column, ColumnAdmin)
site.register(Category, CategoryAdmin)

site.register(Post, PostAdmin)
