from dotenv import load_dotenv
import tqdm
import os
import time
from example import tester
from importlib.resources import files
from io import StringIO
import example
import example.submodule

def main():
    res = files(__name__).joinpath(".env")#.read_text()
    strm = StringIO(res.read_text())
    load_dotenv(stream = strm)
    USER = os.environ["USER"]
    print (os.environ['BLAH'])
    print(f"Hello from zoombuild {USER}")
    fred = """I am a very very long line of text, when I was written I went way over to the right side of the editor windo"""

    def I_am_a_ridiculously_long_function_name(
        an_annoying_long_variable_name, another_long_var_name
    ):
        _ignore = 123
        print(fred)

    for n in tqdm.tqdm(range(10)):
        time.sleep(0.25)

    tester.test()
    tester.resource()
    example.whoo()
    print(example.submodule)
    example.submodule.poo()
    print(dir(example.submodule))
if __name__ == "__main__":
    print (sys.argv)
    main()
