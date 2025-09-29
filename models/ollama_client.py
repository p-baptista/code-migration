import ollama
import requests

from models.base_client import BaseClient


class OllamaClient(BaseClient):
    def __init__(self):
        self.client = ollama

    def start_ollama():
        """Starts the Ollama server as a background process."""
        try:
            # Check if Ollama is already running
            subprocess.run(["ollama"], capture_output=True, text=True, check=True)
            print("Ollama is already running.")
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Starting Ollama server...")
            process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)  # Give the server a moment to start
            print("Ollama server started.")
            return process

    def is_ollama_running(self):
        try:
            response = requests.get("http://localhost:11434")
            return response.status_code == 200 and "Ollama is running" in response.text
        except requests.ConnectionError:
            return False

    def generate_prompt(self, template, **kwargs):
        formatted = template.format(**kwargs)
        system_match = self.find_pattern(formatted, "SYSTEM_CONFIG")
        user_match = self.find_pattern(formatted, "USER_CONFIG")

        system_config = self.generate_request_dict("system", system_match[0])
        user_config_1 = self.generate_request_dict("user", user_match[0])

        if kwargs["PROMPT"] != "one_shot":
            return [system_config, user_config_1]

        assistant_match = self.find_pattern(formatted, "ASSISTANT_CONFIG")
        assistant_config = self.generate_request_dict("assistant", assistant_match[0])

        user_config_2 = self.generate_request_dict("user", user_match[1])

        return [system_config, user_config_1, assistant_config, user_config_2]

    def process(self, args):
        try:
            input_code = self.get_input_code(file_path=args.INPUT_PATH)
            template = self.load_template(file_name=args.PROMPT)
            prompt = self.generate_prompt(
                template=template,
                PROMPT=args.PROMPT,
                LANGUAGE_NAME=args.LANGUAGE_NAME,
                OLD_LIB_NAME=args.OLD_LIB_NAME,
                NEW_LIB_NAME=args.NEW_LIB_NAME,
                CODE_BEFORE_MIGRATION=input_code,
            )
            self.client.pull(args.VERSION)
            print(f"Pulled model {args.VERSION}")
            response = self.client.chat(model=args.VERSION, messages=prompt)
            return response["message"]["content"]
        except ValueError as e:
            return f"{self.__class__.__name__} could not generate a response: {e}"
