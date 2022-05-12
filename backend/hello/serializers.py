from rest_framework import serializers
from .models import Todo
from .models import Post
from .models import SearchRequest


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'title', 'description', 'completed')


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class SearchRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchRequest
        fields = '__all__'
