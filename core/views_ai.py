from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from django.core.files.base import ContentFile
import base64
from .serializers import RoomRedesignRequestSerializer, RoomRedesignResponseSerializer
from .models import RoomRedesign
from .services.openai_service import generate_redesign_image


class RedesignRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            'multipart/form-data': RoomRedesignRequestSerializer,
        },
        responses={
            200: RoomRedesignResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            500: OpenApiResponse(description='Generation failed'),
        },
        tags=['AI'],
    )
    def post(self, request):
        serializer = RoomRedesignRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            redesign = serializer.save(user=request.user)
            prompt = f"Redesign this interior room photo into a {redesign.style_choice} style. High realism, photorealistic, maintain room layout, professional interior design render."
            redesign.prompt = prompt
            redesign.status = 'processing'
            redesign.save()
        try:
            result = generate_redesign_image(prompt=prompt, image_path=redesign.original_image.path)
            if result.get('image_bytes'):
                redesign.result_base64 = result['image_bytes']
                decoded = base64.b64decode(result['image_bytes'])
                image_file = ContentFile(decoded, name=f"redesign_{redesign.id}.png")
                redesign.result_image.save(image_file.name, image_file, save=False)
            redesign.status = 'completed'
            redesign.save()
            return Response(RoomRedesignResponseSerializer(redesign).data, status=status.HTTP_200_OK)
        except Exception as e:
            redesign.status = 'failed'
            redesign.save()
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiResponse(response=RoomRedesignResponseSerializer(many=True))},
        tags=['AI'],
    )
    def get(self, request):
        items = RoomRedesign.objects.filter(user=request.user).order_by('-created_at')
        data = RoomRedesignResponseSerializer(items, many=True).data
        return Response(data, status=status.HTTP_200_OK)
