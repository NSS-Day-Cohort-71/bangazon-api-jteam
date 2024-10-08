import datetime
import json
from rest_framework import status
from rest_framework.test import APITestCase


class PaymentTests(APITestCase):
    def setUp(self) -> None:
        """
        Create a new account and create sample category
        """
        url = "/register"
        data = {"username": "steve", "password": "Admin8*", "email": "steve@stevebrownlee.com",
                "address": "100 Infinity Way", "phone_number": "555-1212", "first_name": "Steve", "last_name": "Brownlee"}
        response = self.client.post(url, data, format='json')
        json_response = json.loads(response.content)
        self.token = json_response["token"]
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_payment_type(self):
        """
        Ensure we can add a payment type for a customer.
        """
        # Add product to order
        url = "/payment-types"
        data = {
            "merchant_name": "American Express",
            "account_number": "111-1111-1111",
            "expiration_date": "2024-12-31",
            "create_date": datetime.date.today()
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.post(url, data, format='json')
        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["merchant_name"], "American Express")
        self.assertEqual(json_response["account_number"], "111-1111-1111")
        self.assertEqual(json_response["expiration_date"], "2024-12-31")
        self.assertEqual(json_response["create_date"], str(datetime.date.today()))

    def test_delete_payment_type(self):
        """
        Ensure we can delete a payment type for a customer.
        """
        # Create a payment type first
        self.test_create_payment_type()

        # Remove payment from customer
        url = "/payment-types/1"
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check if payment type was deleted
        url = "/payment-types"
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.get(url, format='json')

        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Ensure the returned list of payment types is empty
        self.assertEqual(len(json_response), 0)
