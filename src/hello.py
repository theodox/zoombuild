from dotenv import load_dotenv
import tqdm
import os
import time


def main():
    load_dotenv()
    USER = os.environ["USER"]
    print(f"Hello from zoombuild {USER}")
    example = """I am a very very long line of text, when I was written I went way over to the right side of the editor windo"""

    def I_am_a_ridiculously_long_function_name(
        an_annoying_long_variable_name, another_long_var_name
    ):
        _ignore = 123
        print(example)

    for n in tqdm.tqdm(range(10)):
        time.sleep(0.25)


if __name__ == "__main__":
    main()
