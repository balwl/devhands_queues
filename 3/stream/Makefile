SRC = app/src
BIN = app/bin
LIB = app/libs
NS = io.devhands

# Find all Java source files
SOURCES := $(shell find $(SRC) -name *.java)

# Build the classpath
CLASSPATH = $(BIN):$(LIB)/*

all: build run

# Compile the Java sources
build:
	javac -cp "$(CLASSPATH)" -d $(BIN) $(SOURCES)

build_one: CLASS
	javac -cp "$(CLASSPATH)" -d $(BIN) $(shell find $(SRC) -name $(CLASS).java)

# Run the main class with a parameter
run: CLASS build_one
	java -cp "$(CLASSPATH)" -Dorg.slf4j.simpleLogger.defaultLogLevel=error -Dlog4j.configuration=file:log4j.properties $(NS).$(CLASS)

# Clean the build directory
clean:
	rm -rf $(BIN)

CLASS:
	@ if [ -z "$(CLASS)" ]; then \
		echo "Usage: make run CLASS=<ClassName>"; \
		exit 1; \
	fi

.PHONY: all build build_one run clean