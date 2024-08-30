from django.urls import reverse
from rest_framework import status

from taxi.models import City
from taxi.serializers import CitySerializer
from taxi.tests.base import TestBase

CITY_URL = reverse("taxi:city-list")


def get_city_detail(city_id) -> str:
    return reverse("taxi:city-detail", args=[city_id])


class UnauthorizedCityAPITest(TestBase):
    def test_unauthorized_user_can_list_cities(self):
        res = self.client.get(CITY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthorized_user_cannot_create_cities(self):
        res = self.client.post(CITY_URL, {"name": "test city"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_update_cities(self):
        res = self.client.patch(
            get_city_detail(self.default_city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_delete_cities(self):
        res = self.client.delete(get_city_detail(self.default_city.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserCityAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_user)

    def test_simple_user_cannot_create_cities(self):
        res = self.client.post(CITY_URL, {"name": "test city"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cannot_update_cities(self):
        res = self.client.patch(
            get_city_detail(self.default_city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cannot_delete_cities(self):
        res = self.client.delete(get_city_detail(self.default_city.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCityAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_admin)

    def test_admin_can_create_cities(self):
        res = self.client.post(CITY_URL, {"name": "test city"})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_can_update_cities(self):
        res = self.client.patch(
            get_city_detail(self.default_city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_cities(self):
        res = self.client.delete(get_city_detail(self.default_city.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_city_filters(self):
        city2 = City.objects.create(name="test city2")

        serializer1 = CitySerializer(self.default_city)
        serializer2 = CitySerializer(city2)

        res = self.client.get(CITY_URL, {"name": "city2"})

        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer1.data, res.data)
