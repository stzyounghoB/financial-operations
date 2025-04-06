from setuptools import setup, find_packages

# git tag 기반 버전 관리로 변경
setup(
    name="aws_finops_tools",
    # version="1.0.0",  # 하드코딩된 버전 제거
    use_scm_version=True,  # git tag를 버전으로 사용
    setup_requires=["setuptools_scm"],  # setuptools_scm 의존성 추가
    description="AWS 리소스 비용 최적화를 위한 도구",
    author="YoungHo Cha",
    packages=find_packages(),
    install_requires=[
        "aioboto3>=9.0.0",
        "boto3>=1.18.0", 
        "pandas>=1.3.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "finops=aws_finops_tools.main:main_cli",  # 경로 변경
        ],
    },
)