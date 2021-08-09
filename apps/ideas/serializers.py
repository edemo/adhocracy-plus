from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags
from rest_framework import serializers

from adhocracy4.categories.models import Category
from adhocracy4.labels.models import Label
from adhocracy4.ratings.models import Rating

from .models import Idea


class LabelListingField(serializers.StringRelatedField):
    def to_internal_value(self, label):
        return Label.objects.get(pk=label)


class DescriptionSerializerField(serializers.Field):

    def to_representation(self, description):
        return strip_tags(description)

    def to_internal_value(self, description):
        return description


class RatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rating
        fields = ('id', 'value')


class IdeaSerializer(serializers.ModelSerializer):

    description = DescriptionSerializerField()
    creator = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    positive_rating_count = serializers.SerializerMethodField()
    negative_rating_count = serializers.SerializerMethodField()
    labels = LabelListingField(many=True)
    category = serializers.StringRelatedField()
    content_type = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    has_rating_permission = serializers.SerializerMethodField()
    has_commenting_permission = serializers.SerializerMethodField()
    has_changing_permission = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = ('pk', 'name', 'description', 'creator', 'created',
                  'reference_number', 'image', 'comment_count',
                  'positive_rating_count', 'negative_rating_count',
                  'labels', 'category', 'content_type', 'user_rating',
                  'has_rating_permission', 'has_commenting_permission',
                  'has_changing_permission')
        read_only_fields = ('pk', 'creator', 'created', 'reference_number')

    def get_creator(self, idea):
        return idea.creator.username

    def get_comment_count(self, idea):
        if hasattr(idea, 'comment_count'):
            return idea.comment_count
        else:
            return 0

    def get_positive_rating_count(self, idea):
        if hasattr(idea, 'positive_rating_count'):
            return idea.positive_rating_count
        else:
            return 0

    def get_negative_rating_count(self, idea):
        if hasattr(idea, 'negative_rating_count'):
            return idea.negative_rating_count
        else:
            return 0

    def get_content_type(self, idea):
        return ContentType.objects.get_for_model(idea).id

    def get_user_rating(self, idea):
        if 'request' in self.context:
            user = self.context['request'].user
            if user.is_authenticated:
                ct = ContentType.objects.get_for_model(idea)
                ratings = Rating.objects.filter(content_type_id=ct.id,
                                                object_pk=idea.pk,
                                                creator=user)
                if ratings.exists():
                    return RatingSerializer(ratings.first()).data
        return None

    def get_has_rating_permission(self, idea):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            return user.has_perm('a4_candy_ideas.rate_idea', idea)
        return False

    def get_has_commenting_permission(self, idea):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            return user.has_perm('a4_candy_ideas.comment_idea', idea)
        return False

    def get_has_changing_permission(self, idea):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            return user.has_perm('a4_candy_ideas.change_idea', idea)
        return False

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        validated_data['module'] = self.context['view'].module
        if 'category_pk' in self.context['request'].POST:
            category_pk = self.context['request'].POST['category_pk']
            category = Category.objects.get(pk=category_pk)
            validated_data['category'] = category

        return super().create(validated_data)
