from setuptools import setup, find_packages

setup(
    name="app_msbox_11luty",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'pymysql',
        'python-dotenv',
        'bcrypt',
    ],
) 