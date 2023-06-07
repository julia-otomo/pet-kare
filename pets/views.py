from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Pet
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request):
        trait = request.query_params.get("trait", None)

        if trait:
            pets = Pet.objects.filter(traits__name__contains=trait)
        else:
            pets = Pet.objects.all()

        pets_pagination = self.paginate_queryset(pets, request, view=self)

        serializer = PetSerializer(instance=pets_pagination, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        validate_data_serializer = PetSerializer(data=request.data)

        validate_data_serializer.is_valid(raise_exception=True)

        pet_data = validate_data_serializer.validated_data.copy()
        group_request_data = pet_data.pop("group")
        trait_request_data = pet_data.pop("traits")

        group_data, created = Group.objects.get_or_create(
            scientific_name__iexact=group_request_data["scientific_name"],
            defaults=group_request_data,
        )

        new_pet = Pet.objects.create(**pet_data, group=group_data)

        traits_list = [
            Trait.objects.get_or_create(name__iexact=trait["name"], defaults=trait)[0]
            for trait in trait_request_data
        ]

        new_pet.traits.set(traits_list)

        new_pet.save()

        formatter_serializer = PetSerializer(instance=new_pet)

        return Response(data=formatter_serializer.data, status=status.HTTP_201_CREATED)


class PetDetailsView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet_data = get_object_or_404(Pet, id=pet_id)

        pet_serializer = PetSerializer(instance=pet_data)

        return Response(data=pet_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet_data = get_object_or_404(Pet, id=pet_id)

        pet_serializer = PetSerializer(data=request.data, partial=True)

        pet_serializer.is_valid(raise_exception=True)

        pet_validated = pet_serializer.validated_data

        if pet_validated.get("group"):
            group_request_data = pet_validated.pop("group")

            group_data, created = Group.objects.get_or_create(
                scientific_name__iexact=group_request_data["scientific_name"],
                defaults=group_request_data,
            )

            pet_data.group = group_data

        if pet_validated.get("traits"):
            trait_request_data = pet_validated.pop("traits")

            traits_list = [
                Trait.objects.get_or_create(name__iexact=trait["name"], defaults=trait)[
                    0
                ]
                for trait in trait_request_data
            ]

            pet_data.traits.set(traits_list)

        for key, value in pet_validated.items():
            setattr(pet_data, key, value)

        pet_data.save()

        pet_format_serializer = PetSerializer(instance=pet_data)

        return Response(data=pet_format_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pet_id) -> Response:
        pet_data = get_object_or_404(Pet, id=pet_id)

        pet_data.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
