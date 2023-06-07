from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from .models import Pet
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request):
        pets = Pet.objects.all()

        pets_pagination = self.paginate_queryset(pets, request, view=self)

        serializer = PetSerializer(data=pets_pagination, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        validate_data_serializer = PetSerializer(data=request.data)

        if not validate_data_serializer.is_valid():
            return Response(
                data=validate_data_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        pet_data = validate_data_serializer.validated_data.copy()
        group_request_data = pet_data.pop("group")
        trait_request_data = pet_data.pop("traits")

        new_pet = Pet.objects.create(**pet_data)

        group_data, created = Group.objects.get_or_create(
            scientific_name=group_request_data["scientific_name"],
            defaults=group_request_data,
        )

        new_pet.group = group_data

        traits_list = [
            Trait.objects.get_or_create(name=trait["name"], defaults=trait)[0]
            for trait in trait_request_data
        ]

        new_pet.traits.set(traits_list)

        new_pet.save()

        formatter_serializer = PetSerializer(instance=new_pet)

        return Response(data=formatter_serializer.data, status=status.HTTP_201_CREATED)
