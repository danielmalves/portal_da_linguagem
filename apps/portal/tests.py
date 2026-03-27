from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Language services and analytical practice")

    def test_home_page_includes_globe_data_points(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("globe_data_points", response.context)
        self.assertGreaterEqual(len(response.context["globe_data_points"]), 100)
        self.assertContains(response, "globe-data-points")
        self.assertIn("wiki_summary", response.context["globe_data_points"][0])
