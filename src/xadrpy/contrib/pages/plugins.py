from xadrpy.templates.libs import Plugin
import re
from django.core.urlresolvers import resolve
from xadrpy.router.models import Route
from django.template.loader import render_to_string
from django.template.context import Context

unnecessary_p = re.compile("<p>\s*&nbsp;\s*</p>$")


class MenuPlugin(Plugin):
    alias = "x-menu"
    
    def render(self, context, template="xadrpy/pages/menu.html"):
        parent = None
        request = context.get('request')
        func, args, kwargs = resolve(request.path)
        selected = kwargs.get('route', context.get('route', getattr(request,'route', None)))
        if not selected:
            selected_key = context.get('route_key', getattr(request, 'route_key', None))
            if selected_key:
                selected = Route.objects.get(key=selected_key)
        if selected:
            ancestors = [ancestor.id for ancestor in selected.get_ancestors(include_self=False)]
        ctx = {
            'items': Route.objects.filter(parent=parent, menu_title__isnull=False),
            'selected': selected,
            'ancestors': ancestors,
            'parent': parent,
        }
        return render_to_string(template, ctx, context)

class HMenuPlugin(Plugin):
    alias = "x-hmenu"

    def render(self, context, template="xadrpy/pages/plugins/hmenu.html"):
        parent = None
        request = context.get('request')
        func, args, kwargs = resolve(request.path)
        selected = kwargs.get('route', context.get('route', getattr(request,'route', None)))
        if not selected:
            selected_key = context.get('route_key', getattr(request, 'route_key', None))
            if selected_key:
                selected = Route.objects.get(key=selected_key)
        if selected:
            ancestors = [ancestor.id for ancestor in selected.get_ancestors(include_self=False)]
        ctx = {
            'items': Route.objects.filter(parent=parent, menu_title__isnull=False),
            'selected': selected,
            'ancestors': ancestors,
            'parent': parent,
        }
        return render_to_string(template, ctx, context)

class CommentsPlugin(Plugin):
    alias = "x-comments"
    template = "xadrpy/pages/plugins/comments.html"

    def render(self, context, entry):
        ctx = Context({
            'entry': entry
        })
        ctx.update(context)
        return self.get_template().render(ctx)
    
class FacebookActivityPlugin(Plugin):
    alias = "x-facebook_activity"
    template = "xadrpy/pages/plugins/facebook_activity.html"
    
    def render(self, context, width=200, height=300, router=None):
        context.update({"width": width, "height": height})
        return self.get_template().render(context)
            
class FacebookCommentsPlugin(Plugin):
    alias = "x-facebook_comments"
    template = "xadrpy/pages/plugins/facebook_comments.html"
    
    def render(self, context, width="650", num_posts=5, router=None):
        context.update({"width": width, "num_posts": num_posts})
        return self.get_template().render(context)
            
