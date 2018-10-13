from setuptools import setup


setup(
    name='Cryptle',
    version='0.11',
    author='Twelve brothers',
    author_email='',
    description='Cryptle: Algorithmic trading framework',
    packages=['cryptle'],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.5',
    install_requires=[
        'numpy>=1.13',
        'websocket-client>=0.45',
    ],
    extras_require={
        'dev': [
            'pylint>=2',
            'pytest>=3',
        ]
    }
)
