"""
Setup configuration for Azure DevOps AI Manufacturing MCP
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("docs/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Core requirements (non-optional)
core_requirements = [
    "aiohttp>=3.8.0,<4.0.0",
    "aiosqlite>=0.17.0,<1.0.0", 
    "cryptography>=3.4.8,<5.0.0",
    "python-dateutil>=2.8.0,<3.0.0"
]

# Optional requirements for enhanced functionality
optional_requirements = {
    "redis": ["aioredis>=2.0.0,<3.0.0"],
    "postgresql": ["asyncpg>=0.27.0,<1.0.0"],
    "mysql": ["aiomysql>=0.1.1,<1.0.0"],
    "monitoring": [
        "prometheus-client>=0.14.0,<1.0.0",
        "psutil>=5.8.0,<6.0.0",
        "memory-profiler>=0.60.0,<1.0.0"
    ],
    "cli": [
        "click>=8.0.0,<9.0.0",
        "rich>=12.0.0,<14.0.0"
    ],
    "validation": ["pydantic>=1.10.0,<3.0.0"],
    "dev": [
        "pytest>=7.0.0,<8.0.0",
        "pytest-asyncio>=0.21.0,<1.0.0",
        "pytest-cov>=4.0.0,<5.0.0",
        "black>=22.0.0,<24.0.0",
        "flake8>=5.0.0,<7.0.0",
        "mypy>=1.0.0,<2.0.0"
    ],
    "docs": [
        "sphinx>=5.0.0,<7.0.0",
        "sphinx-rtd-theme>=1.0.0,<2.0.0",
        "myst-parser>=0.18.0,<1.0.0"
    ]
}

# All optional requirements combined
all_optional = []
for reqs in optional_requirements.values():
    all_optional.extend(reqs)

optional_requirements["all"] = all_optional

setup(
    name="azure-devops-ai-manufacturing-mcp",
    version="1.0.0",
    author="Azure DevOps AI Manufacturing Team",
    author_email="ai-manufacturing@company.com",
    description="Comprehensive Azure DevOps MCP module for AI-driven software manufacturing processes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/azure-devops-ai-manufacturing-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.8",
    install_requires=core_requirements,
    extras_require=optional_requirements,
    entry_points={
        "console_scripts": [
            "azure-devops-manufacturing=azure_devops_ai_manufacturing_mcp.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "azure_devops_ai_manufacturing_mcp": [
            "docs/*.md",
            "examples/*.py",
            "tests/*.py",
            "AI_COMPLETION.md"
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-org/azure-devops-ai-manufacturing-mcp/issues",
        "Source": "https://github.com/your-org/azure-devops-ai-manufacturing-mcp",
        "Documentation": "https://azure-devops-ai-manufacturing-mcp.readthedocs.io/",
    },
    keywords="azure-devops ai manufacturing mcp automation workflow git integration",
    zip_safe=False,
)
