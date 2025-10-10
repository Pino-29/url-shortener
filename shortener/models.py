from django.db import models
from django.db.models import F
from django.utils import timezone
import string
import random


class URL(models.Model):
    """Model to store shortened URLs."""
    
    original_url = models.URLField(max_length=2048, help_text="The original long URL")
    short_code = models.CharField(
        max_length=10, 
        unique=True, 
        db_index=True,
        help_text="The unique short code for the URL"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    clicks = models.PositiveIntegerField(default=0, help_text="Number of times this URL was accessed")
    is_active = models.BooleanField(default=True, help_text="Whether this short URL is active")
    
    class Meta:
        verbose_name = "URL"
        verbose_name_plural = "URLs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"
    
    def increment_clicks(self):
        """Increment the click counter using F() expression."""
        # This updates the database directly without loading the object
        URL.objects.filter(pk=self.pk).update(clicks=F('clicks') + 1)
        # Refresh the instance to reflect the new value
        self.refresh_from_db(fields=['clicks'])
    
    @staticmethod
    def generate_short_code(length=6):
        """Generate a random short code."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    def save(self, *args, **kwargs):
        """Override save to generate short_code if not provided."""
        # Only generate short_code if we're not doing a partial update
        # or if update_fields includes short_code
        update_fields = kwargs.get('update_fields')
        if not self.short_code and (update_fields is None or 'short_code' in update_fields):
            # Generate unique short code
            while True:
                short_code = self.generate_short_code()
                if not URL.objects.filter(short_code=short_code).exists():
                    self.short_code = short_code
                    break
            # If update_fields was specified, add short_code to it
            if update_fields is not None:
                kwargs['update_fields'] = list(update_fields) + ['short_code']
        super().save(*args, **kwargs)
