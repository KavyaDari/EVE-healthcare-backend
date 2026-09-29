from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers.auth import SignupSerializer, UserSerializer
from ..services.auth import register_user
from drf_spectacular.utils import extend_schema

@extend_schema(
    request=SignupSerializer,
    responses={201: UserSerializer},
)
class SignupView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = register_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)
