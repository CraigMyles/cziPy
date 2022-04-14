# Global Vars
PROJECT_NAME = cziPy
PYTHON_VERSION = 3.10

# Check for conda installation
ifeq (,$(shell which conda))
	HAS_CONDA=False
else
	HAS_CONDA=True
endif

# Check for cziPy conda environment (This might not work but i've commented it out anyway)
ifeq (,$(shell conda env list | grep 'cziPy'))
    HAS_cziPy_ENV=False
else
    HAS_cziPy_ENV=True
endif

# set up the python environment (for first time use)
create_environment:
ifeq (True,$(HAS_CONDA))
	conda env create
else
	@echo "Conda is not installed. Please install conda and try again."
endif

install_java:
	sudo apt -y install software-properties-common
	# sudo add-apt-repository ppa:webupd8team/java
	sudo apt -y install openjdk-8-jdk
	sudo update-alternatives --config java # select Java 8
	printf '\nexport JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> ~/.bashrc
	export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

export_environment:
	conda env export --no-builds | grep -v "^prefix: " > environment.yml
