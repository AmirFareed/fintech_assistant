from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_modular_package_directories_exist():
    expected = {
        "api",
        "chunking",
        "embeddings",
        "ingestion",
        "llm",
        "prompts",
        "retrieval",
        "utils",
        "vectordb",
    }
    assert all((PROJECT_ROOT / package / "__init__.py").is_file() for package in expected)


def test_configuration_and_entry_point_exist():
    assert (PROJECT_ROOT / "config.yaml").is_file()
    assert (PROJECT_ROOT / ".env.example").is_file()
    assert (PROJECT_ROOT / "main.py").is_file()


def test_main_exports_flask_application():
    from main import app

    assert app.name == "api.application"


def test_legacy_imports_alias_new_modules():
    import llm.chatbot
    import services.chatbot

    assert services.chatbot is llm.chatbot
