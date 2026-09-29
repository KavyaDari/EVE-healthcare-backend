from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..permissions import IsStaffOrReadOnly
from drf_spectacular.utils import extend_schema


from ..selectors import (
    list_centres, get_centre, list_tests, get_test, 
    list_centre_tests, get_centre_test
)
from ..services import (
    create_centre, update_centre, delete_centre,
    create_test, update_test, delete_test,
    add_test_to_centre, update_centre_test_price, remove_test_from_centre
)
from ..serializers import (
    DiagnosticCentreSerializer, DiagnosticTestSerializer,
    CentreTestReadSerializer, CentreTestWriteSerializer, CentreTestUpdateSerializer
)

class CentreListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        centres = list_centres()
        return Response(DiagnosticCentreSerializer(centres, many=True).data)
    @extend_schema(
        request=DiagnosticCentreSerializer,
        responses={201: DiagnosticCentreSerializer},
    )
    def post(self, request):
        serializer = DiagnosticCentreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        centre = create_centre(**serializer.validated_data)
        return Response(DiagnosticCentreSerializer(centre).data, status=status.HTTP_201_CREATED)

class CentreDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request, pk):
        centre = get_centre(pk)
        return Response(DiagnosticCentreSerializer(centre).data)

    def patch(self, request, pk):
        centre = get_centre(pk)
        serializer = DiagnosticCentreSerializer(centre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        centre = update_centre(centre, **serializer.validated_data)
        return Response(DiagnosticCentreSerializer(centre).data)

    def delete(self, request, pk):
        centre = get_centre(pk)
        delete_centre(centre)
        return Response(status=status.HTTP_204_NO_CONTENT)

class TestListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request):
        tests = list_tests()
        return Response(DiagnosticTestSerializer(tests, many=True).data)

    @extend_schema(
        request=DiagnosticTestSerializer,
        responses={201: DiagnosticTestSerializer},
    )
    def post(self, request):
        serializer = DiagnosticTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        test = create_test(**serializer.validated_data)
        return Response(DiagnosticTestSerializer(test).data, status=status.HTTP_201_CREATED)

class TestDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request, pk):
        test = get_test(pk)
        return Response(DiagnosticTestSerializer(test).data)

    def patch(self, request, pk):
        test = get_test(pk)
        serializer = DiagnosticTestSerializer(test, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        test = update_test(test, **serializer.validated_data)
        return Response(DiagnosticTestSerializer(test).data)

    def delete(self, request, pk):
        test = get_test(pk)
        delete_test(test)
        return Response(status=status.HTTP_204_NO_CONTENT)

class CentreTestListCreateView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def get(self, request, centre_id):
        get_centre(centre_id)  # Validate centre exists
        centre_tests = list_centre_tests(centre_id)
        return Response(CentreTestReadSerializer(centre_tests, many=True).data)


    @extend_schema(
        request=CentreTestWriteSerializer,
        responses={201: CentreTestReadSerializer},
    )
    def post(self, request, centre_id):
        centre = get_centre(centre_id)
        serializer = CentreTestWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        test = get_test(serializer.validated_data['test_id'])
        centre_test = add_test_to_centre(centre, test, serializer.validated_data['price'])
        
        return Response(CentreTestReadSerializer(centre_test).data, status=status.HTTP_201_CREATED)

class CentreTestDetailView(APIView):
    permission_classes = [IsStaffOrReadOnly]

    def patch(self, request, centre_id, test_id):
        centre_test = get_centre_test(centre_id, test_id)
        serializer = CentreTestUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        centre_test = update_centre_test_price(centre_test, serializer.validated_data['price'])
        return Response(CentreTestReadSerializer(centre_test).data)

    def delete(self, request, centre_id, test_id):
        centre_test = get_centre_test(centre_id, test_id)
        remove_test_from_centre(centre_test)
        return Response(status=status.HTTP_204_NO_CONTENT)
