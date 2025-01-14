from django.test import TestCase

from .forms import AuthorForm
from .models import Address, Author


class ModelFormTests(TestCase):
    def test_update(self):
        author = Author.objects.create(
            name="Bob", age=50, address=Address(city="NYC", state="NY", zip_code="10001")
        )
        data = {
            "name": "Bob",
            "age": 51,
            "address-po_box": "",
            "address-city": "New York City",
            "address-state": "NY",
            "address-zip_code": "10001",
        }
        form = AuthorForm(data, instance=author)
        self.assertTrue(form.is_valid())
        form.save()
        author.refresh_from_db()
        self.assertEqual(author.age, 51)
        self.assertEqual(author.address.city, "New York City")

    def test_some_missing_data(self):
        author = Author.objects.create(
            name="Bob", age=50, address=Address(city="NYC", state="NY", zip_code="10001")
        )
        data = {
            "name": "Bob",
            "age": 51,
            "address-po_box": "",
            "address-city": "New York City",
            "address-state": "NY",
            "address-zip_code": "",
        }
        form = AuthorForm(data, instance=author)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["address"], ["Enter all required values."])

    def test_invalid_field_data(self):
        """A field's data (state) is too long."""
        author = Author.objects.create(
            name="Bob", age=50, address=Address(city="NYC", state="NY", zip_code="10001")
        )
        data = {
            "name": "Bob",
            "age": 51,
            "address-po_box": "",
            "address-city": "New York City",
            "address-state": "TOO LONG",
            "address-zip_code": "",
        }
        form = AuthorForm(data, instance=author)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["address"],
            [
                "Ensure this value has at most 2 characters (it has 8).",
                "Enter all required values.",
            ],
        )

    def test_all_missing_data(self):
        author = Author.objects.create(
            name="Bob", age=50, address=Address(city="NYC", state="NY", zip_code="10001")
        )
        data = {
            "name": "Bob",
            "age": 51,
            "address-po_box": "",
            "address-city": "",
            "address-state": "",
            "address-zip_code": "",
        }
        form = AuthorForm(data, instance=author)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["address"], ["This field is required."])

    def test_nullable_field(self):
        """A nullable EmbeddedModelField is removed if all fields are empty."""
        author = Author.objects.create(
            name="Bob",
            age=50,
            address=Address(city="NYC", state="NY", zip_code="10001"),
            billing_address=Address(city="NYC", state="NY", zip_code="10001"),
        )
        data = {
            "name": "Bob",
            "age": 51,
            "address-po_box": "",
            "address-city": "New York City",
            "address-state": "NY",
            "address-zip_code": "10001",
            "billing_address-po_box": "",
            "billing_address-city": "",
            "billing_address-state": "",
            "billing_address-zip_code": "",
        }
        form = AuthorForm(data, instance=author)
        self.assertTrue(form.is_valid())
        form.save()
        author.refresh_from_db()
        self.assertIsNone(author.billing_address)

    def test_rendering(self):
        form = AuthorForm()
        self.assertHTMLEqual(
            str(form.fields["address"].get_bound_field(form, "address")),
            """
            <div>
                <label for="id_address-po_box">PO Box:</label>
                <input id="id_address-po_box" maxlength="50" name="address-po_box" type="text">
            </div>
            <div>
                <label for="id_address-city">City:</label>
                <input type="text" name="address-city" maxlength="20" required id="id_address-city">
            </div>
            <div>
                <label for="id_address-state">State:</label>
                <input type="text" name="address-state" maxlength="2" required
                    id="id_address-state">
            </div>
            <div>
                <label for="id_address-zip_code">Zip code:</label>
                <input type="number" name="address-zip_code" required id="id_address-zip_code">
            </div>""",
        )
