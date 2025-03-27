from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save

class Strategy(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)  # Unique slug
    is_active = models.BooleanField(default=True)  # Boolean field for active/inactive status
    parameters = models.JSONField(default=dict, blank=True)  # Store params dynamically
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Auto-generate slug before saving
def generate_slug(instance, new_slug=None):
    slug = slugify(instance.name) if not new_slug else new_slug
    qs = Strategy.objects.filter(slug=slug).exclude(id=instance.id)
    if qs.exists():
        new_slug = f"{slug}-{qs.count()}"
        return generate_slug(instance, new_slug=new_slug)
    return slug

def pre_save_strategy_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generate_slug(instance)

pre_save.connect(pre_save_strategy_receiver, sender=Strategy)
