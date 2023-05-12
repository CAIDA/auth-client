import setuptools
import caida_oidc_client

setuptools.setup(
    name='caida_oidc_client',
    version=caida_oidc_client.__version__,
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
            'get_oidc_tokens=caida_oidc_client.get_oidc_tokens:main',
            'oidc_query=caida_oidc_client.oidc_query:main'
        ]
    },
)
