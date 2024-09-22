from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.serializers import CarSerializer
from taxi.tests.base import TestBase

CAR_URL = reverse("taxi:car-list")


def get_car_detail(car_id) -> str:
    return reverse("taxi:car-detail", args=[car_id])


class UnauthorizedCarAPITest(TestBase):
    def setUp(self):
        super().setUp()

    def test_unauthorized_user_cant_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_create_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.post(CAR_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_update_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(self.default_car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_delete_cars(self):
        res = self.client.delete(get_car_detail(self.default_car.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_user)

    def test_simple_user_cant_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_create_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.post(CAR_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_update_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(self.default_car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_delete_cars(self):
        res = self.client.delete(get_car_detail(self.default_car.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class DriverCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_driver_user)

    def test_driver_can_create_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.post(CAR_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_driver_can_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_driver_can_list_only_his_cars(self):
        driver_user_2 = self.sample_user(
            email="driver_user_2@test.com", is_driver=True
        )
        driver2 = self.sample_driver(user=driver_user_2)
        car2 = self.sample_car(driver2)

        serializer1 = CarSerializer(self.default_car)
        serializer2 = CarSerializer(car2)

        res = self.client.get(CAR_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_driver_can_update_cars(self):
        payload = {
            "model": "updated test model",
            "number": "updated test number",
        }
        res = self.client.patch(get_car_detail(self.default_car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_driver_can_delete_cars(self):
        res = self.client.delete(get_car_detail(self.default_car.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


class AdminCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.default_admin)

    def test_admin_can_list_all_cars(self):
        serializer = CarSerializer(self.default_car)

        res = self.client.get(CAR_URL)

        self.assertIn(serializer.data, res.data)

    def test_car_list_with_driver_filter(self):
        driver_user_2 = self.sample_user(
            email="driver_user_2@test.com", is_driver=True
        )
        driver2 = self.sample_driver(user=driver_user_2)
        car2 = self.sample_car(driver2)

        serializer1 = CarSerializer(self.default_car)
        serializer2 = CarSerializer(car2)

        res = self.client.get(CAR_URL, {"driver": self.default_driver.id})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_admin_can_update_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(self.default_car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_cars(self):
        res = self.client.delete(get_car_detail(self.default_car.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
