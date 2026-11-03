# Optional Huey examples

These files were moved out of src/huey/memory/PY. They are not part of
automatic startup, ingestion, or runtime tool registration.

- example_audio_input.py and example_audio_output.py: local WAV fixtures.
- example_data_loader.py: CSV processing demo.
- example_llm.py: requires the optional AI runtime.
- example_plugin.py and example_tool.py: require compatible PyHuey/PyGPT;
  the tool also requires PySide6.
- example_vector_store.py: educational local vector store.
- example_web_search.py: requires explicitly approved outbound network.
- hardware/vic2_demo.py: Raspberry Pi/Pygame display example.

Only run a chosen example interactively in an isolated development environment
with the necessary optional dependencies. Examples are not production modules.
