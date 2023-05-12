import setuptools
import caida_sso_client

setuptools.setup(
    name='caida_sso_client',
    version=caida_sso_client.__version__,
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
            'get_sso_tokens=caida_sso_client.get_sso_tokens:main',
            'sso_query=caida_sso_client.sso_query:main'
        ]
    },
)
