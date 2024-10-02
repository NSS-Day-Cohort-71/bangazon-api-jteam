import json
import datetime
from rest_framework import status
from rest_framework.test import APITestCase


class ProductTests(APITestCase):
    def setUp(self) -> None:
        """
        Create a new account and create sample category
        """
        url = "/register"
        data = {
            "username": "steve",
            "password": "Admin8*",
            "email": "steve@stevebrownlee.com",
            "address": "100 Infinity Way",
            "phone_number": "555-1212",
            "first_name": "Steve",
            "last_name": "Brownlee",
        }
        response = self.client.post(url, data, format="json")
        json_response = json.loads(response.content)
        self.token = json_response["token"]
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = "/productcategories"
        data = {"name": "Sporting Goods"}
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        response = self.client.post(url, data, format="json")
        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["name"], "Sporting Goods")

    def test_create_product(self):
        """
        Ensure we can create a new product.
        """
        url = "/products"
        data = {
            "name": "Kite",
            "price": 14.99,
            "quantity": 60,
            "description": "It flies high",
            "category_id": 1,
            "location": "Pittsburgh",
        }
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        response = self.client.post(url, data, format="json")
        json_response = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json_response["name"], "Kite")
        self.assertEqual(json_response["price"], 14.99)
        self.assertEqual(json_response["quantity"], 60)
        self.assertEqual(json_response["description"], "It flies high")
        self.assertEqual(json_response["location"], "Pittsburgh")

    def test_update_product(self):
        """
        Ensure we can update a product.
        """
        self.test_create_product()

        url = "/products/1"
        data = {
            "name": "Kite",
            "price": 24.99,
            "quantity": 40,
            "description": "It flies very high",
            "category_id": 1,
            "created_date": datetime.date.today(),
            "location": "Pittsburgh",
        }
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(url, data, format="json")
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json_response["name"], "Kite")
        self.assertEqual(json_response["price"], 24.99)
        self.assertEqual(json_response["quantity"], 40)
        self.assertEqual(json_response["description"], "It flies very high")
        self.assertEqual(json_response["location"], "Pittsburgh")

    def test_get_all_products(self):
        """
        Ensure we can get a collection of products.
        """
        self.test_create_product()
        self.test_create_product()
        self.test_create_product()

        url = "/products"

        response = self.client.get(url, None, format="json")
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json_response), 3)

    def test_delete_product(self):
        """
        Ensure we can soft delete a product, but the product remains in the database
        """
        # Create 3 products
        self.test_get_all_products()

        # Delete a single product
        url = "/products/1"
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.delete(url, None, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Get all products and ensure product is not in default query
        url = "/products"
        response = self.client.get(url, None, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 2)

        # Ensure the deleted product is still in the database
        url = "/products/deleted"
        response = self.client.get(url, None, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 1)
        

    def test_add_rating_to_product(self):
        """
        Ensure we can add a rating to a product and verify the average rating
        """
        # Create a product using existing test method
        self.test_create_product()

        # Add a rating to the product
        rating_url = "/products/1/rate-product"
        rating_data = {"score": 4, "rating_text": "Great product!"}

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        response = self.client.post(rating_url, rating_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get the updated product to check the rating
        response = self.client.get("/products/1", None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product_data = json.loads(response.content)

        # Verify that average_rating exists and is correct
        self.assertIn("average_rating", product_data)
        self.assertEqual(product_data["average_rating"], 4.0)

        # Add another rating
        rating_data = {"score": 2, "rating_text": "Not as good as expected"}

        response = self.client.post(rating_url, rating_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get the updated product again
        response = self.client.get("/products/1", None, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product_data = json.loads(response.content)

        # Verify that average_rating has been updated correctly
        self.assertEqual(product_data["average_rating"], 3.0)
