from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..selectors import list_user_bookings, get_user_booking
from ..services import create_booking, cancel_booking
from ..serializers import BookingReadSerializer, BookingCreateSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(
    request=BookingCreateSerializer,
    responses={201: BookingReadSerializer},
)
class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = list_user_bookings(request.user)
        return Response(BookingReadSerializer(bookings, many=True).data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = create_booking(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(BookingReadSerializer(booking).data, status=status.HTTP_201_CREATED)

class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        booking = get_user_booking(request.user, pk)
        return Response(BookingReadSerializer(booking).data)

class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = cancel_booking(request.user, pk)
        return Response(BookingReadSerializer(booking).data)
