import langchain_core
import sys

print(f"Python: {sys.version}")
print(f"LangChain Core Version: {langchain_core.__version__}")
print(f"LangChain Core Path: {langchain_core.__file__}")

try:
    from langchain_core.language_models.chat_models import init_chat_model
    print("✅ init_chat_model found!")
except ImportError as e:
    print(f"❌ init_chat_model NOT found: {e}")
    import langchain_core.language_models.chat_models as cm
    print(f"Contents of chat_models: {dir(cm)}")
