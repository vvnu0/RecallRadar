"""Streamlit entrypoint placeholder.

Install Streamlit in your deployment environment to run this optional prototype:
    streamlit run src/streamlit_app.py
"""

from flavor_engine import engine


def build_snapshot():
    return {
        "overview": engine.get_overview(),
        "default_substitutions": engine.search_substitutions("Strawberry"),
        "sensory_dimensions": engine.get_sensory_map()["dimensions"],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build_snapshot(), indent=2))
