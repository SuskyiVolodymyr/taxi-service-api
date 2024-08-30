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
        city = City.objects.create(name="test city")
        res = self.client.patch(
            get_city_detail(city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_delete_cities(self):
        city = City.objects.create(name="test city")
        res = self.client.delete(get_city_detail(city.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserCityAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_simple_user_cannot_create_cities(self):
        res = self.client.post(CITY_URL, {"name": "test city"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cannot_update_cities(self):
        city = City.objects.create(name="test city")
        res = self.client.patch(
            get_city_detail(city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cannot_delete_cities(self):
        city = City.objects.create(name="test city")
        res = self.client.delete(get_city_detail(city.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCityAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_create_cities(self):
        res = self.client.post(CITY_URL, {"name": "test city"})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_can_update_cities(self):
        city = City.objects.create(name="test city")
        res = self.client.patch(
            get_city_detail(city.id), {"name": "updated city"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        city.refresh_from_db()
        self.assertEqual(city.name, "updated city")

    def test_admin_can_delete_cities(self):
        city = City.objects.create(name="test city")
        res = self.client.delete(get_city_detail(city.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(list(City.objects.filter(id=city.id)), [])

    def test_city_filters(self):
        city1 = City.objects.create(name="test city1")
        city2 = City.objects.create(name="test city2")

        serializer1 = CitySerializer(city1)
        serializer2 = CitySerializer(city2)

        res = self.client.get(CITY_URL, {"name": "city1"})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
