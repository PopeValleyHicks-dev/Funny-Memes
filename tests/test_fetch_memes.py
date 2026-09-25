import unittest

from scripts.fetch_memes import post_to_item, render_markdown


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


if __name__ == "__main__":
    unittest.main()
