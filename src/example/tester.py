from importlib.resources import files
def test():
    if __debug__:
        print ("DEBUG")

    print ("not debug")



def resource():
    res = files("example").joinpath("resource.txt").read_text()
    print (res)