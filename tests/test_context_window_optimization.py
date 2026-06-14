import unittest

from helpers.context_window_helpers import optimize_context_window


class FakeEncoding:
    def encode(self, text):
        return [ord(character) for character in text]

    def decode(self, tokens):
        return "".join(chr(token) for token in tokens)


ENCODING = FakeEncoding()


def section(title, body):
    return f"<<SECTION: {title} >>\n{body}\n<<END_SECTION: {title} >>"


def count_tokens(text):
    return len(ENCODING.encode(text))


class ContextWindowOptimizationTest(unittest.TestCase):
    def test_keeps_high_priority_sections_before_large_lower_priority_content(self):
        structure = section("Repository Structure", "package.json\nREADME.md\nsrc/app.py")
        languages = section("Repository Languages", "TypeScript: 120 lines\nCSS: 10 lines")
        package_json = section("Content of package.json", '{"scripts":{"dev":"vite"}}')
        readme = section("Content of README.md", "README_START " + ("details " * 300) + "README_TAIL")
        changelog = section("Content of CHANGELOG.md", "CHANGELOG_START " + ("noise " * 300) + "CHANGELOG_TAIL")
        context = "\n\n".join([readme, changelog, structure, package_json, languages])
        budget = count_tokens("\n\n".join([structure, languages, package_json])) + 10

        result = optimize_context_window(context, max_tokens=budget, encoding=ENCODING)

        self.assertLessEqual(count_tokens(result), budget)
        self.assertIn("Repository Structure", result)
        self.assertIn("Repository Languages", result)
        self.assertIn('"scripts":{"dev":"vite"}', result)
        self.assertNotIn("README_TAIL", result)
        self.assertNotIn("CHANGELOG_TAIL", result)

    def test_existing_devcontainer_is_preserved_before_readme_content(self):
        structure = section("Repository Structure", ".devcontainer/devcontainer.json\nREADME.md")
        languages = section("Repository Languages", "Python: 20 lines")
        existing_devcontainer = section(
            "Existing devcontainer.json",
            '{"image":"mcr.microsoft.com/devcontainers/python:3.12"}',
        )
        readme = section("Content of README.md", "README_START " + ("details " * 300) + "README_TAIL")
        context = "\n\n".join([readme, structure, existing_devcontainer, languages])
        budget = count_tokens("\n\n".join([structure, languages, existing_devcontainer])) + 10

        result = optimize_context_window(context, max_tokens=budget, encoding=ENCODING)

        self.assertLessEqual(count_tokens(result), budget)
        self.assertIn("mcr.microsoft.com/devcontainers/python:3.12", result)
        self.assertNotIn("README_TAIL", result)

    def test_plain_context_falls_back_to_token_prefix(self):
        context = "alpha " * 300
        budget = 50

        result = optimize_context_window(context, max_tokens=budget, encoding=ENCODING)

        self.assertLessEqual(count_tokens(result), budget)
        self.assertTrue(result.startswith("alpha"))


if __name__ == "__main__":
    unittest.main()
