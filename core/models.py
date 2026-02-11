from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


# ============================================
# NEWS MODULE MODELS
# ============================================

class NewsCategory(models.Model):
    """News Category Model"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'News Category'
        verbose_name_plural = 'News Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class News(models.Model):
    """News/Article Model with all fields for frontend"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(
        NewsCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='news'
    )
    featured_image = models.ImageField(upload_to='news/featured/')
    thumbnail = models.ImageField(
        upload_to='news/thumbnails/', 
        blank=True, 
        null=True,
        help_text='Small image for listing cards'
    )
    excerpt = models.TextField(
        max_length=300, 
        help_text='Short description for listing cards (max 300 chars)'
    )
    content = models.TextField(help_text='Full article content')
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='news_articles'
    )
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # SEO Fields
    meta_title = models.CharField(
        max_length=60, 
        blank=True, 
        null=True,
        help_text='SEO title (max 60 chars)'
    )
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        null=True,
        help_text='SEO description (max 160 chars)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
        super().save(*args, **kwargs)

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])



# ============================================
# CONTACT MODULE MODEL
# ============================================

class Contact(models.Model):
    """Contact Form Submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    reply_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} - {self.subject}"
