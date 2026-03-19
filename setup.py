from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="skill-service",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="本地 Skill 运行服务 - 支持命令行和 API 接口运行 skills",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/skill-service",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "click>=8.1.0",
        "pyyaml>=6.0",
        "aiofiles>=23.2.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "skill-service=skill_service.main:cli",
        ],
    },
)
