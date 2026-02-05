from django.test import TestCase
from django.urls import reverse

from .models import Category, CustomUser, Topic


class PublicProfileViewTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(username="owner", password="pass12345")
        self.viewer = CustomUser.objects.create_user(username="viewer", password="pass12345")
        self.category = Category.objects.create(name="Новости", slug="novosti")
        self.topic = Topic.objects.create(
            author=self.owner,
            category=self.category,
            title="Topic",
            description="Desc",
        )

    def test_public_profile_available_for_anonymous(self):
        response = self.client.get(reverse("public-profile", kwargs={"username": self.owner.username}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner.username)
        self.assertNotContains(response, "Редактировать профиль")
        self.assertNotContains(response, "Выйти")

    def test_public_profile_shows_owner_controls_for_owner(self):
        self.client.login(username="owner", password="pass12345")

        response = self.client.get(reverse("public-profile", kwargs={"username": self.owner.username}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Редактировать профиль")
        self.assertContains(response, "Выйти")

    def test_home_contains_profile_link_for_topic_author(self):
        response = self.client.get(reverse("home"))

        expected_url = reverse("public-profile", kwargs={"username": self.owner.username})
        self.assertContains(response, expected_url)

    def test_topic_detail_contains_profile_links(self):
        response = self.client.get(reverse("topic-detail", kwargs={"topic_id": self.topic.id}))

        expected_url = reverse("public-profile", kwargs={"username": self.owner.username})
        self.assertContains(response, expected_url)
