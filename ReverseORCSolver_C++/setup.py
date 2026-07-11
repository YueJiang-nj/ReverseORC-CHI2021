from setuptools import Extension, setup


setup(
    name="reverse-orc-cpp",
    version="1.0.0",
    description="Native C++ hierarchical ReverseORC solver with a Python API",
    py_modules=["hierarchical_solver_cpp"],
    ext_modules=[
        Extension(
            "_reverse_orc_cpp",
            ["cpp/hierarchical_solver.cpp"],
            language="c++",
            extra_compile_args=["-std=c++17", "-O3"],
        )
    ],
)
