from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Класс формы для создания нового поста.
    """
    class Meta:
        model = Post
        fields = [
            'group',
            'text',
            'image',
        ]


class CommentForm(forms.ModelForm):
    """Класс формы для создания нового комментария.
    """
    class Meta:
        model = Comment
        fields = [
            'text',
        ]
        widgets = {
            'text': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
        }
