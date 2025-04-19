import compileall
import zipfile
import os


def compile_tree(source_tree, zipname, optimize = 1, filter =None):
    print ("zip", os.path.abspath(zipname))

    compileall.compile_dir(source_tree, optimize=1)

    with zipfile.PyZipFile(zipname, 'w', optimize=1) as archive:
        archive.writepy(source_tree, filter)
        archive.writepy(source_tree + "/example")

    return zipname


if __name__ == '__main__':
    compile_tree('src', 'test.zip')