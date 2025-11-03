from datetime import timedelta
import os
import uuid
import base64
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status, serializers, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
)
from .models import OTP, RoomRedesign
from .utils import send_otp_email, generate_otp
from .services.openai_service import generate_redesign_image

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='Registration successful. OTP sent to email.'),
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Auth'],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            code = generate_otp()
            OTP.objects.create(
                user=user,
                code=code,
                purpose='verify',
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            send_otp_email(user.email, code, subject='Verify your email')
            return Response({'message': 'Registration successful. OTP sent to email.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description='Email verified successfully'),
            400: OpenApiResponse(description='Invalid or expired code'),
            404: OpenApiResponse(description='User not found'),
        },
        tags=['Auth'],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        otp = OTP.objects.filter(user=user, code=code, purpose='verify', is_used=False).order_by('-created_at').first()
        if not otp or not otp.is_valid():
            return Response({'detail': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)
        otp.is_used = True
        otp.save()
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Returns access and refresh tokens with user data'),
            400: OpenApiResponse(description='Invalid credentials'),
        },
        tags=['Auth'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user, context={'request': request}).data
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data,
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={200: OpenApiResponse(description='OTP sent if email exists')},
        tags=['Auth'],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If the email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)
        code = generate_otp()
        OTP.objects.create(
            user=user,
            code=code,
            purpose='reset',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        send_otp_email(email, code, subject='Password reset code')
        return Response({'message': 'If the email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successful'),
            400: OpenApiResponse(description='Invalid email or code'),
        },
        tags=['Auth'],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid email or code'}, status=status.HTTP_400_BAD_REQUEST)
        otp = OTP.objects.filter(user=user, code=code, purpose='reset', is_used=False).order_by('-created_at').first()
        if not otp or not otp.is_valid():
            return Response({'detail': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        otp.is_used = True
        otp.save()
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description='Password changed successfully')},
        tags=['Auth'],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            'multipart/form-data': inline_serializer(
                name='UpdateProfileForm',
                fields={
                    'first_name': serializers.CharField(required=False, allow_blank=True),
                    'last_name': serializers.CharField(required=False, allow_blank=True),
                    'profile_image': serializers.FileField(required=False, allow_null=True),
                }
            )
        },
        responses={200: OpenApiResponse(description='Profile updated')},
        tags=['Auth'],
    )
    def patch(self, request):
        serializer = UpdateProfileSerializer(instance=request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(UserSerializer(request.user, context={'request': request}).data, status=status.HTTP_200_OK)




class GuestGenerateView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            'multipart/form-data': inline_serializer(
                name='GuestGenerateForm',
                fields={
                    'style_choice': serializers.ChoiceField(choices=[c[0] for c in RoomRedesign.STYLE_CHOICES]),
                    'original_image': serializers.FileField(),
                }
            )
        },
        responses={
            200: OpenApiResponse(description='Generation completed'),
            400: OpenApiResponse(description='Validation error'),
            500: OpenApiResponse(description='Generation failed'),
        },
        tags=['AI'],
    )
    def post(self, request):
        style_choice = request.data.get('style_choice')
        image = request.FILES.get('original_image')
        if not style_choice:
            return Response({'style_choice': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if style_choice not in [c[0] for c in RoomRedesign.STYLE_CHOICES]:
            return Response({'style_choice': ['Invalid choice.']}, status=status.HTTP_400_BAD_REQUEST)
        if not image:
            return Response({'original_image': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        uid = uuid.uuid4().hex
        in_name = f"guest_{uid}_{image.name}"
        in_path = os.path.join('uploads', 'guest', 'inputs', in_name)
        # Save input image to MEDIA_ROOT
        input_rel_path = default_storage.save(in_path, image)
        input_abs_path = os.path.join(settings.MEDIA_ROOT, input_rel_path)

        prompt = f"Redesign this interior room photo into a {style_choice} style. High realism, photorealistic, maintain room layout, professional interior design render."

        try:
            result = generate_redesign_image(prompt=prompt, image_path=input_abs_path)
            output_rel_url = None
            if result.get('image_bytes'):
                decoded = base64.b64decode(result['image_bytes'])
                out_name = f"guest_{uid}.png"
                out_rel_path = os.path.join('uploads', 'guest', 'outputs', out_name)
                default_storage.save(out_rel_path, ContentFile(decoded, name=out_name))
                output_rel_url = f"{settings.MEDIA_URL}{out_rel_path}"

            payload = {
                'id': uid,
                'input_image_url': f"{settings.MEDIA_URL}{input_rel_path}",
                'output_image_url': output_rel_url,
                'style': style_choice,
                'created_at': timezone.now().isoformat(),
                'status': 'completed' if output_rel_url else 'processing',
            }
            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GuestHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        # Optional: return server-side history keyed by device-id
        return Response([], status=status.HTTP_200_OK)