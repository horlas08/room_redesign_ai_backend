from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from .models import User, OTP, RoomRedesign


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        # authenticate() expects the keyword matching USERNAME_FIELD which is 'email' on our User model,
        # but the backend signature uses 'username'. Passing as 'username' ensures compatibility.
        user = authenticate(request=self.context.get('request'), username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('User is inactive')
        attrs['user'] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class RoomRedesignRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomRedesign
        fields = ('id', 'original_image', 'style_choice')
        read_only_fields = ('id',)


class RoomRedesignResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomRedesign
        fields = ('id', 'style_choice', 'result_image', 'result_base64', 'status', 'created_at')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'profile_image', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_image')
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'profile_image': {'required': False, 'allow_null': True},
        }
