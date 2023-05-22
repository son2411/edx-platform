"""
Serializers for the notifications API.
"""
from django.core.exceptions import ValidationError
from rest_framework import serializers

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.notifications.models import Notification, NotificationPreference, \
    get_notification_preference_config, get_notification_channels


class CourseOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseOverview model.
    """

    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name')


class NotificationCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseEnrollment model.
    """
    course = CourseOverviewSerializer()

    class Meta:
        model = CourseEnrollment
        fields = ('course', 'is_active', 'mode')


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification preferences.
    """
    course_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ('id', 'course_name', 'course_id', 'notification_preference_config',)
        read_only_fields = ('id', 'course_name', 'course_id',)
        write_only_fields = ('notification_preference_config',)

    def get_course_name(self, obj):
        """
        Returns course name from course id.
        """
        return CourseOverview.get_from_id(obj.course_id).display_name


class UserNotificationPreferenceUpdateSerializer(serializers.Serializer):
    """
    Serializer for user notification preferences update.
    """

    notification_app = serializers.CharField()
    value = serializers.BooleanField(required=False)
    notification_type = serializers.CharField(required=False)
    notification_channel = serializers.CharField(required=False)

    def validate(self, attrs):
        """
        Validation for notification preference update form
        """
        notification_app = attrs.get('notification_app')
        notification_type = attrs.get('notification_type')
        notification_channel = attrs.get('notification_channel')
        value = attrs.get('value')

        notification_app_config = get_notification_preference_config()

        if not (notification_app and value is not None):
            raise ValidationError(
                'notification_app and value are required.'
            )

        if notification_type and not notification_channel:
            raise ValidationError(
                'notification_channel is required for notification_type.'
            )
        if notification_channel and not notification_type:
            raise ValidationError(
                'notification_type is required for notification_channel.'
            )

        if notification_app not in notification_app_config.keys():  # pylint: disable=consider-iterating-dictionary
            raise ValidationError(
                f'{notification_app} is not a valid notification app.'
            )

        if notification_type:
            notification_types = notification_app_config.get(notification_app).get('notification_types')

            if notification_type not in notification_types.keys() and notification_type != 'core':  # pylint: disable=consider-iterating-dictionary
                raise ValidationError(
                    f'{notification_type} is not a valid notification type.'
                )

        if notification_channel and notification_channel not in get_notification_channels():
            raise ValidationError(
                f'{notification_channel} is not a valid notification channel.'
            )

        return attrs

    def update(self, instance, validated_data):
        """
        Update notification preference config.
        """
        notification_app = validated_data.get('notification_app')
        notification_type = validated_data.get('notification_type')
        notification_channel = validated_data.get('notification_channel')
        value = validated_data.get('value')
        user_notification_preference_config = instance.notification_preference_config

        if notification_type and notification_channel:
            # Update the notification preference for notification_app core
            if notification_type == "core":
                user_notification_preference_config[notification_app]["core"][notification_channel] = value
            # Update the notification preference for specific notification_type
            else:
                user_notification_preference_config[
                    notification_app]["notification_types"][notification_type][notification_channel] = value

        else:
            # Update the notification preference for notification_app
            user_notification_preference_config[notification_app]["enabled"] = value

        instance.save()
        return instance

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model.
    """

    class Meta:
        model = Notification
        fields = (
            'id',
            'app_name',
            'notification_type',
            'content',
            'content_context',
            'content_url',
            'last_read',
            'last_seen',
        )
