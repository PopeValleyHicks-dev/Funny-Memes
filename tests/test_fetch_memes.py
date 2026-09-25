import unittest
from unittest.mock import patch

from scripts.fetch_memes import collect_memes, post_to_item, render_markdown


class PostToItemTests(unittest.TestCase):
    def test_rejects_nsfw_video_posts(self) -> None:
        post = {
            "id": "abc123",
            "title": "Example",
            "permalink": "/r/memes/comments/abc123/example/",
            "over_18": True,
            "is_video": True,
            "url": "https://example.com/test.jpg",
        }

        self.assertIsNone(post_to_item(post, "memes"))

    def test_uses_preview_image_when_direct_url_is_not_an_image(self) -> None:
        post = {
            "id": "abc123",
            "title": "Preview\nimage",
            "permalink": "/r/memes/comments/abc123/example/",
            "over_18": False,
            "stickied": False,
            "is_video": False,
            "url": "https://reddit.com/gallery/abc123",
            "preview": {
                "images": [
                    {
                        "source": {
                            "url": "https://example.com/image.png?width=100&amp;height=100"
                        }
                    }
                ]
            },
        }

        item = post_to_item(post, "memes")

        self.assertIsNotNone(item)
        self.assertEqual(item["title"], "Preview image")
        self.assertEqual(item["image_url"], "https://example.com/image.png?width=100&height=100")

    def test_rejects_posts_with_empty_preview_images(self) -> None:
        post = {
            "id": "abc123",
            "title": "No image",
            "permalink": "/r/memes/comments/abc123/example/",
            "over_18": False,
            "stickied": False,
            "is_video": False,
            "url": "https://reddit.com/gallery/abc123",
            "preview": {"images": []},
        }

        self.assertIsNone(post_to_item(post, "memes"))

    def test_rejects_posts_with_malformed_preview_images(self) -> None:
        post = {
            "id": "abc123",
            "title": "Bad image",
            "permalink": "/r/memes/comments/abc123/example/",
            "over_18": False,
            "stickied": False,
            "is_video": False,
            "url": "https://reddit.com/gallery/abc123",
            "preview": {"images": ["invalid"]},
        }

        self.assertIsNone(post_to_item(post, "memes"))


class RenderMarkdownTests(unittest.TestCase):
    def test_renders_all_memes(self) -> None:
        markdown = render_markdown(
            [
                {
                    "title": "A meme",
                    "subreddit": "memes",
                    "score": 42,
                    "comments": 7,
                    "post_url": "https://www.reddit.com/test",
                    "image_url": "https://example.com/image.jpg",
                }
            ],
            "2026-09-25T00:00:00+00:00",
        )

        self.assertIn("# Daily Funny Memes", markdown)
        self.assertIn("## 1. A meme", markdown)
        self.assertIn("- Source: r/memes", markdown)
        self.assertIn("- Image: ![A meme](https://example.com/image.jpg)", markdown)


class CollectMemesTests(unittest.TestCase):
    @patch("scripts.fetch_memes.fetch_feed")
    def test_collects_across_feeds_and_deduplicates(self, mock_fetch_feed) -> None:
        mock_fetch_feed.side_effect = [
            {
                "data": {
                    "children": [
                        {
                            "data": {
                                "id": "one",
                                "title": "First meme",
                                "permalink": "/r/memes/comments/one/first/",
                                "over_18": False,
                                "stickied": False,
                                "is_video": False,
                                "url": "https://example.com/one.jpg",
                            }
                        },
                        {
                            "data": {
                                "id": "one",
                                "title": "Duplicate meme",
                                "permalink": "/r/memes/comments/one/duplicate/",
                                "over_18": False,
                                "stickied": False,
                                "is_video": False,
                                "url": "https://example.com/duplicate.jpg",
                            }
                        },
                    ]
                }
            },
            {
                "data": {
                    "children": [
                        {
                            "data": {
                                "id": "two",
                                "title": "Second meme",
                                "permalink": "/r/funny/comments/two/second/",
                                "over_18": False,
                                "stickied": False,
                                "is_video": False,
                                "url": "https://example.com/two.jpg",
                            }
                        }
                    ]
                }
            },
        ]

        items = collect_memes(["memes", "funny"], count=2, limit_per_subreddit=10)

        self.assertEqual(len(items), 2)
        self.assertEqual([item["id"] for item in items], ["one", "two"])

    @patch("scripts.fetch_memes.fetch_feed")
    def test_returns_shortfall_without_raising(self, mock_fetch_feed) -> None:
        mock_fetch_feed.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "one",
                            "title": "Only meme",
                            "permalink": "/r/memes/comments/one/only/",
                            "over_18": False,
                            "stickied": False,
                            "is_video": False,
                            "url": "https://example.com/one.jpg",
                        }
                    }
                ]
            }
        }

        items = collect_memes(["memes"], count=3, limit_per_subreddit=10)

        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
