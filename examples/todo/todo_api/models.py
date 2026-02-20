from django.db import models
from django.contrib.auth.models import User


class Tag(models.Model):
    """Tag model for categorizing todos"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#3B82F6")  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Todo(models.Model):
    """Todo model with all fields for testing djapy features"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='todos'
    )
    tags = models.ManyToManyField(Tag, related_name='todos', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Additional fields for testing
    estimated_hours = models.FloatField(null=True, blank=True)
    actual_hours = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['completed', '-created_at']),
            models.Index(fields=['priority']),
            models.Index(fields=['owner', 'completed']),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment model for todos"""
    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.todo.title}"