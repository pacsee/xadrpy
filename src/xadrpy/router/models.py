from django.db import models
from django.contrib.sites.models import Site
from xadrpy.models.fields.nullchar_field import NullCharField
from xadrpy.models.inheritable import TreeInheritable
import conf
from django.utils.translation import ugettext_lazy as _, get_language
from django.conf.urls import patterns, include, url
from django.utils.functional import lazy
from xadrpy.i18n.utils import i18n_patterns
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, pre_save
import os
import hashlib
import xadrpy
from django.conf import settings
from xadrpy.i18n.models import Translation
from xadrpy.i18n.fields import TranslationForeignKey
from xadrpy.utils.signals import autodiscover_signal
from xadrpy.utils.imports import get_installed_apps_module, get_class
from xadrpy.models.fields.dict_field import DictField
from xadrpy.models.fields.language_code_field import LanguageCodeField
import logging
import libs
from xadrpy.models.fields.class_field import ClassField
logger = logging.getLogger("x-router")

class Route(TreeInheritable):
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))
    modified = models.DateTimeField(auto_now=True, verbose_name=_("Modified"))
    master = models.ForeignKey('self', blank=True, null=True, verbose_name=_("Master"), related_name="+")
    site = models.ForeignKey(Site, verbose_name=_("Site"), default=conf.DEFAULT_SITE_ID)
    language_code = LanguageCodeField(verbose_name=_("Language code"), blank=True, null=True, default=None)
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    image = models.ImageField(upload_to="images", blank=True, null=True, verbose_name = _("Image"))
    slug = NullCharField(max_length=255, verbose_name=_("URL part"))
    i18n = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True, verbose_name=_("Is enabled"))
    visible = models.BooleanField(default=True, verbose_name=_("Is visible"))
    signature = NullCharField(max_length=128, editable=False, default="")
    name = NullCharField(max_length=255, unique=True)
    application_name = NullCharField(max_length=128, verbose_name=_("Application name"))
    meta = DictField()
#    meta_title = models.CharField(max_length=255, blank=True, verbose_name=_("Meta title"), default="")
#    overwrite_meta_title = models.BooleanField(default=False, verbose_name=_("Overwrite meta title"))
#    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name=_("Meta keywords"), default="")
#    meta_description = models.TextField(blank=True, verbose_name=_("Meta description"), default="")
    
    need_reload = True
    
    class Meta:
        unique_together = ('site', 'language_code', 'parent', 'slug')
        verbose_name = _("Route")
        verbose_name_plural = _("Routes")
        db_table = "xadrpy_router_route"

    def __unicode__(self):
        return self.title
    
    def get_regex(self, postfix="$", slash="/", language_code=None):
        root_language_code = self.get_root_language_code()
        if not self.parent:
            regex = root_language_code and "^%s/" % root_language_code or "^"
        else:
            regex = self.parent.get_regex(postfix="", slash="/", language_code=language_code)
        slug = self.get_slug(language_code)
        if slug:
            slug = slug+slash
        regex += slug 
        return regex + postfix

    def get_slug(self, language_code):
        return self.translation(language_code=language_code).slug or self.slug or ""
    
    def get_title(self):
        return self.translation().title

    def get_translated_regex(self, postfix="$", slash="/"):
        language_code = get_language()
        return self.get_regex(postfix=postfix, slash=slash, language_code=language_code)
    
    get_translated_regex = lazy(get_translated_regex, unicode)
    
    def patterns(self, *args, **kwargs):
        if not self.parent and self.i18n:
            return i18n_patterns(*args, **kwargs)
        return patterns(*args, **kwargs)
    
    def get_urls(self, kwargs={}):
        if self.app:
            return self.app.get_urls(kwargs)
        return []
    
    def append_pattern(self, url_patterns):
        if not self.enabled: 
            return
        root_language_code = self.get_root_language_code()
        kwargs = root_language_code and {conf.LANGUAGE_CODE_KWARG: root_language_code} or {}
        urls = self.get_urls(kwargs)
        if not urls: return
        url_patterns+=self.patterns('', *urls)
    
    def get_root_language_code(self):
        return self.get_root().language_code
    
    def get_master(self):
        self._master = getattr(self, "_master", False)
        if self._master==False:
            self._master=None
            if self.master:
                self._master = self.master.descendant
            elif isinstance(self.get_parent(), Route):
                master = self.get_parent().get_master()
                if master:
                    self._master = master.descendant
        return self._master
    
    def get_application(self):
        if hasattr(self, "_app"):
            return self._app
        if not self.application_name:
            self._app = None
            return None
        try:
            self._app = get_class(self.application_name,libs.Application)(self)
        except:
            self._app = None 
        return self._app
    
    app = property(get_application)
    
    def get_meta(self):
        return conf.META_HANDLER_CLS(self)
    
    def get_signature(self):
        return u"%s:%s-%s-%s-%s-%s-%s" % (conf.VERSION, self.site.id, not self.parent and self.language_code or None, self.slug, not self.parent and self.i18n, self.enabled, self.application_name)

    def get_context(self, request, args=(), kwargs={}):
        return {}

    
    def permit(self, request, view, args, kwargs):
        pass
    

class RouteTranslation(Translation):
    origin = TranslationForeignKey(Route, related_name="+")
    language_code = LanguageCodeField()

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    image = models.ImageField(upload_to="images", blank=True, null=True, verbose_name = _("Image"))
    slug = NullCharField(max_length=255, verbose_name=_("URL part"))
    meta = DictField(default={})

    meta_title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Meta title"))
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Meta keywords"))
    meta_description = models.TextField(blank=True, null=True, verbose_name=_("Meta description"))

    class Meta:
        db_table = "xadrpy_router_route_translation"

RouteTranslation.register(Route)

@receiver(pre_save, sender=None)
def check_signature(sender, instance, **kwargs):
    if isinstance(instance, Route):
        signature = hashlib.md5(instance.get_signature()).hexdigest()
        instance.signature_changed = instance.signature != signature
        if instance.signature_changed:
            logger.info("Route (#%s) signature changed", instance.id)
            instance.signature = signature
            instance.signature_changed = instance.need_reload and conf.WSGI_PATH
    
if conf.TOUCH_WSGI_FILE:
    @receiver(post_save, sender=None)
    def touch_wsgi_file(sender, instance, **kwargs):
        if isinstance(instance, Route) and instance.need_reload and conf.WSGI_PATH and instance.signature_changed:
            with file(conf.WSGI_PATH, 'a'):
                os.utime(conf.WSGI_PATH, None)

#class ViewRoute(Route):
#    view_name = NullCharField(max_length=255)
#    name = NullCharField(max_length=255, unique=True)
#    
#    default_view_name = None
#    
#    class Meta:
#        verbose_name = _("View")
#        verbose_name_plural = _("Views")
#        db_table = "xadrpy_router_view"
#
#    def get_urls(self, kwargs={}):
#        kwargs.update({'router': self.id})
#        if not self.view_name:
#            return []
#        
#        slash = ""
#        if settings.APPEND_SLASH:
#            slash = "/"
#
#        return [url(self.get_translated_regex(slash=slash), self.view_name, kwargs=kwargs, name=self.name)]
#    
#    def get_context(self, request, args=(), kwargs={}):
#        return {}

class IncludeRoute(Route):
    include_name = models.CharField(max_length=255)
    namespace = NullCharField(max_length=255)
#    app_name = NullCharField(max_length=255)

    class Meta:
        verbose_name = _("Include")
        verbose_name_plural = _("Includes")
        db_table = "xadrpy_router_include"

    def get_urls(self, kwargs={}):
        kwargs.update({'router': self.id})
        return url(self.get_translated_regex(postfix=""), include(self.include_name, self.namespace, self.name), kwargs=kwargs)

class StaticRoute(Route):
    path = models.FilePathField(max_length=255, verbose_name=_("Path"))
    mimetype = NullCharField(max_length=255, verbose_name=_("Mime type"))

    class Meta:
        verbose_name = _("Static")
        verbose_name_plural = _("Statics")
        db_table = "xadrpy_router_static"

    def get_regex(self, postfix="$", slash="/"):
        return super(StaticRoute, self).get_regex(postfix=postfix, slash="")

    def get_urls(self, kwargs={}):
        kwargs.update({'router': self.id})
        return [url(self.get_translated_regex(), 'xadrpy.routers.views.static', kwargs=kwargs)]        

class TemplateRoute(Route):
    template_name = models.CharField(max_length=255, verbose_name=_("Template name"))
    mimetype = NullCharField(max_length=255, verbose_name=_("Mime type"))

    class Meta:
        verbose_name = _("Template")
        verbose_name_plural = _("Templates")
        db_table = "xadrpy_router_template"

    def get_regex(self, postfix="$", slash="/"):
        return super(TemplateRoute, self).get_regex(postfix=postfix, slash="")

    def get_urls(self, kwargs={}):
        kwargs.update({'router': self.id})
        return [url(self.get_translated_regex(), 'xadrpy.routers.views.template', kwargs=kwargs)]
    
class RedirectRoute(Route):
    url = NullCharField(max_length=255, null=False, blank=False, verbose_name=_("URL"))
    permanent = models.BooleanField(default=False, verbose_name=_("Permanent"))

    class Meta:
        verbose_name = _("Redirect")
        verbose_name_plural = _("Redirects")
        db_table = "xadrpy_router_redirect"

    def get_urls(self, kwargs={}):
        kwargs.update({'router': self.id})
        return [url(self.get_translated_regex(), 'xadrpy.routers.views.redirect', kwargs=kwargs)] 

