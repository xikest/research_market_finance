from setuptools import setup, find_packages


setup(
    name='rmkf',
    version='0.1.6',  
    author='xikest',
    description='Research market finance',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'numpy', 'pandas', 'selenium'
    ],

    entry_points={
        'console_scripts': [
            'install_env_script = my_package.install_env:main',
        ],
    },
    

    url='https://github.com/xikest/research_market_finance',
    project_urls={
        'Source': 'https://github.com/xikest/research_market_finance',
        'Bug Tracker': 'https://github.com/xikest/research_market_finance/issues',
    }
)
