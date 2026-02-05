from django.test import TestCase
from django.urls import reverse

from .models import Category, Comment, CustomUser, Notification, Topic, TopicSubscription


class PublicProfileAndSocialFeaturesTests(TestCase):
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
        self.assertContains(response, "Темы")

    def test_home_contains_profile_link_for_topic_author(self):
        response = self.client.get(reverse("home"))
        expected_url = reverse("public-profile", kwargs={"username": self.owner.username})
        self.assertContains(response, expected_url)

    def test_author_auto_subscribed_after_topic_create(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.post(reverse("create_topic_simple"), {
            "category": self.category.id,
            "title": "New Topic",
            "description": "text",
        })
        self.assertEqual(response.status_code, 302)
        created_topic = Topic.objects.get(title="New Topic")
        self.assertTrue(TopicSubscription.objects.filter(user=self.owner, topic=created_topic).exists())

    def test_subscription_generates_notification_on_comment(self):
        TopicSubscription.objects.create(user=self.viewer, topic=self.topic)
        self.client.login(username="owner", password="pass12345")

        self.client.post(reverse("topic-detail", kwargs={"topic_id": self.topic.id}), {
            "content": "new comment",
        })

        self.assertTrue(
            Notification.objects.filter(recipient=self.viewer, topic=self.topic, notification_type=Notification.TYPE_COMMENT).exists()
        )

    def test_mentions_create_notifications(self):
        self.client.login(username="owner", password="pass12345")

        self.client.post(reverse("topic-detail", kwargs={"topic_id": self.topic.id}), {
            "content": "Привет, @viewer, проверь пост",
        })

        mention = Notification.objects.filter(recipient=self.viewer, notification_type=Notification.TYPE_MENTION).first()
        self.assertIsNotNone(mention)

    def test_notifications_page_accessible(self):
        Comment.objects.create(author=self.owner, topic=self.topic, content="@viewer hello")
        Notification.objects.create(
            recipient=self.viewer,
            actor=self.owner,
            topic=self.topic,
            notification_type=Notification.TYPE_MENTION,
            message="test",
        )

        self.client.login(username="viewer", password="pass12345")
        response = self.client.get(reverse("notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Уведомления")


class DirectMessageAndReactionNotificationsTests(TestCase):
    def setUp(self):
        self.alice = CustomUser.objects.create_user(username="alice", password="pass12345")
        self.bob = CustomUser.objects.create_user(username="bob", password="pass12345")
        self.category = Category.objects.create(name="Ивенты", slug="events")
        self.topic = Topic.objects.create(author=self.alice, category=self.category, title="Topic", description="D")

    def test_chat_view_available_and_can_send_message(self):
        self.client.login(username="alice", password="pass12345")
        send_url = reverse("chat-with-user", kwargs={"username": self.bob.username})

        response = self.client.post(send_url, {"content": "Привет"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.alice.sent_messages.filter(recipient=self.bob, content="Привет").exists())

    def test_like_topic_creates_notification_for_author(self):
        self.client.login(username="bob", password="pass12345")

        response = self.client.post(reverse("toggle-topic-like", kwargs={"topic_id": self.topic.id}))
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.alice,
                actor=self.bob,
                topic=self.topic,
                notification_type=Notification.TYPE_LIKE,
            ).exists()
        )

    def test_reply_comment_creates_reply_notification(self):
        parent = Comment.objects.create(author=self.alice, topic=self.topic, content="parent")
        self.client.login(username="bob", password="pass12345")

        response = self.client.post(reverse("topic-detail", kwargs={"topic_id": self.topic.id}), {
            "content": "reply",
            "parent_id": str(parent.id),
        })
        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.alice,
                actor=self.bob,
                topic=self.topic,
                notification_type=Notification.TYPE_REPLY,
            ).exists()
        )
