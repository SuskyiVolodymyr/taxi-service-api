from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from taxi.models import Car, Driver, City
from taxi.serializers import CarSerializer
from taxi.tests.base import TestBase
from taxi_service.settings import AUTH_USER_MODEL

CAR_URL = reverse("taxi:car-list")


def get_car_detail(car_id) -> str:
    return reverse("taxi:car-detail", args=[car_id])


class UnauthorizedCarAPITest(TestBase):
    def test_unauthorized_user_cant_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def sample_car(driver: Driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def sample_driver(self):
        return Driver.objects.create(
            user=self.user,
            license_number="123456",
            age=18,
            city=City.objects.create(name="test city"),
            sex="M",
        )

    def test_unauthorized_user_cant_create_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.post(CAR_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_update_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cant_delete_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        res = self.client.delete(get_car_detail(car.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class SimpleUserCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)
        self.user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )

    def test_simple_user_cant_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def sample_car(driver: Driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def sample_driver(self):
        return Driver.objects.create(
            user=self.user2,
            license_number="123456",
            age=18,
            city=City.objects.create(name="test city"),
            sex="M",
        )

    def test_simple_user_cant_create_cars(self):
        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.post(CAR_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_update_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_simple_user_cant_delete_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        res = self.client.delete(get_car_detail(car.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class DriverCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.user.is_driver = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        self.user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )

    @staticmethod
    def sample_car(driver: Driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def sample_driver(self, user: AUTH_USER_MODEL = None):
        if user is None:
            user = self.user
        return Driver.objects.create(
            user=user,
            license_number="123456",
            age=18,
            city=City.objects.create(name="test city"),
            sex="M",
        )

    def test_driver_can_create_cars(self):
        self.sample_driver()
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
        driver1 = self.sample_driver()
        driver2 = self.sample_driver(user=self.user2)
        car1 = self.sample_car(driver1)
        car2 = self.sample_car(driver2)

        serializer1 = CarSerializer(car1)
        serializer2 = CarSerializer(car2)

        res = self.client.get(CAR_URL)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_driver_can_update_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_driver_can_delete_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        res = self.client.delete(get_car_detail(car.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


class AdminCarAPITest(TestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)

    @staticmethod
    def sample_car(driver: Driver):
        return Car.objects.create(
            model="test model",
            number="test number",
            driver=driver,
        )

    def sample_driver(self, user: AUTH_USER_MODEL = None) -> Driver:
        if user is None:
            user = self.user
        return Driver.objects.create(
            user=user,
            license_number="123456",
            age=18,
            city=City.objects.create(name="test city"),
            sex="M",
        )

    def test_admin_can_list_cars(self):
        res = self.client.get(CAR_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_list_all_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        serializer = CarSerializer(car)

        res = self.client.get(CAR_URL)

        self.assertIn(serializer.data, res.data)

    def test_car_list_with_driver_filter(self):
        self.user2 = get_user_model().objects.create_user(
            email="test2@test.com",
            first_name="test2",
            last_name="test2",
            password="test1234",
        )
        driver = self.sample_driver()
        driver2 = self.sample_driver(user=self.user2)
        car1 = self.sample_car(driver)
        car2 = self.sample_car(driver2)

        serializer1 = CarSerializer(car1)
        serializer2 = CarSerializer(car2)

        res = self.client.get(CAR_URL, {"driver": driver.id})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_admin_can_update_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        payload = {
            "model": "test model",
            "number": "test number",
        }
        res = self.client.patch(get_car_detail(car.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_cars(self):
        driver = self.sample_driver()
        car = self.sample_car(driver)

        res = self.client.delete(get_car_detail(car.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
