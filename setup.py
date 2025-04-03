from setuptools import setup, find_packages

setup(
    name="aws-finops-tools",
    version="0.1.0",
    description="AWS 리소스 비용 최적화를 위한 도구",
    author="Your Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aioboto3>=9.0.0",
        "boto3>=1.18.0",
        "pandas>=1.3.0",  # CSV/TSV 처리에 유용
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "finops=main:main_cli",
        ],
    },
)