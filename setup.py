from setuptools import setup, find_packages

setup(
    name='patisson_appLauncher',
    version='1.0.4',
    packages=find_packages(),
    install_requires=[
        "httpx",
        "pydantic"
    ],
    extras_require={
        "uvicorn": ["uvicorn"],
        "gunicorn": ["gunicorn"],
        "graphql": ["ariadne"],
        "fastapi": ["fastapi"],
        "jaeger": [
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation",
            "opentelemetry-exporter-jaeger"
            ],
        "async-fastapi-pack": [
            "uvicorn",
            "fastapi",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation",
            "opentelemetry-exporter-jaeger"
            "opentelemetry-instrumentation-fastapi",
        ]
    },
    author='EliseyGodX',
    description='tools for connecting and managing Consul',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Patisson-Company/_AppLauncher',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)