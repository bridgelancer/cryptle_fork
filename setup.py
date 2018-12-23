from setuptools import setup, find_packages

import cryptle


setup(
    name='cryptle',
    version=cryptle.get_version(),
    author='Glasphere',
    author_email='',
    description='Cryptle: Algorithmic trading framework',
    packages=find_packages(exclude=['test']),
    package_data={
        'cryptle.backtest': ['*.csv'],
    },
    zip_safe=False,
    python_requires='>=3.6',
    install_requires=[
        'numpy>=1.13',
        'pandas>=0.21.0',
        'scipy>=1.1.0',
        'matplotlib>=2.2.0',
        'requests>=2.18.4',
        'websocket-client>=0.45',
        'scikit-learn>=0.19.1',
    ],
    extras_require={
        'dev': [
            'black',
            'pylint>=2',
            'pytest>=3',
            'Sphinx>=1.7.2',
            'sphinx-autodoc-typehints>=1.5.1',
            'sphinx-rtd-theme>=0.4.0',
        ]
    },
)
