import setuptools
import caida_client

setuptools.setup(
    name='caida_client',
    version=caida_client.__version__,
    author='Ken Keys',
    author_email='kkeys@caida.org',
    description='Access protected CAIDA services',
    # long_description='file: README.md',
    # long_description_content_type='text/markdown',
    # url='https://...',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'requests_oauthlib',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'get_offline_token=caida_client.get_offline_token:main',
            'offline_query=caida_client.offline_query:main'
        ]
    },
)