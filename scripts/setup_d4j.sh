#!/bin/bash

# ----------------------------------------
# 1. Install Required Tools if Missing
# ----------------------------------------
for tool in javac mvn ant perl cpanminus; do
    if ! command -v $tool &>/dev/null; then
        sudo apt install -y default-jdk maven ant perl cpanminus
        sudo cpanm String::Interpolate
        sudo cpanm DBI
        break
    fi
done

# ----------------------------------------
# 2. Get Installed JAVA_HOME
# ----------------------------------------
# Use `readlink -f` to resolve symlinks (e.g., /usr/bin/javac -> /usr/lib/jvm/java-11-openjdk-amd64/bin/javac)
JAVA_BIN=$(readlink -f "$(command -v javac)")
JAVA_HOME_DIR=$(dirname "$JAVA_BIN")               # e.g., /usr/lib/jvm/java-11-openjdk-amd64/bin
JAVA_HOME=$(dirname "$JAVA_HOME_DIR")              # one level up = /usr/lib/jvm/java-11-openjdk-amd64

# Export in current session
export JAVA_HOME="$JAVA_HOME"
export PATH="$JAVA_HOME/bin:$PATH"

# Show versions
javac -version
mvn --version
ant -version

# ----------------------------------------
# 3. Setup Working Directory
# ----------------------------------------
work_dir="$HOME/.d4j_src"
mkdir -p "$work_dir"

# Java/Build options
export _JAVA_OPTIONS="-Xmx6144M -XX:MaxHeapSize=4096M"
export MAVEN_OPTS="-Xmx1024M"
export ANT_OPTS="-Xmx6144M -XX:MaxHeapSize=4096M"

# ----------------------------------------
# 4. Clone and Initialize Defects4J
# ----------------------------------------
cd "$work_dir"
if [ ! -d "$work_dir/defects4j" ]; then
    git clone https://github.com/rjust/defects4j.git
    cd "$work_dir/defects4j"
    ./init.sh

    # Append environment variables to ~/.bashrc if not already present
    grep -qxF "export JAVA_HOME=\"$JAVA_HOME\"" ~/.bashrc || echo "export JAVA_HOME=\"$JAVA_HOME\"" >> ~/.bashrc
    grep -qxF 'export PATH="$JAVA_HOME/bin:$PATH"' ~/.bashrc || echo 'export PATH="$JAVA_HOME/bin:$PATH"' >> ~/.bashrc

    grep -qxF 'export D4J_HOME="$HOME/.d4j_src/defects4j"' ~/.bashrc || echo 'export D4J_HOME="$HOME/.d4j_src/defects4j"' >> ~/.bashrc
    grep -qxF 'export PATH="$D4J_HOME/framework/bin:$PATH"' ~/.bashrc || echo 'export PATH="$D4J_HOME/framework/bin:$PATH"' >> ~/.bashrc

    grep -qxF "export TZ='America/Los_Angeles'" ~/.bashrc || echo "export TZ='America/Los_Angeles'" >> ~/.bashrc
    grep -qxF 'export LC_ALL=en_US.UTF-8' ~/.bashrc || echo 'export LC_ALL=en_US.UTF-8' >> ~/.bashrc
    grep -qxF 'export LANG=en_US.UTF-8' ~/.bashrc || echo 'export LANG=en_US.UTF-8' >> ~/.bashrc
    grep -qxF 'export LANGUAGE=en_US.UTF-8' ~/.bashrc || echo 'export LANGUAGE=en_US.UTF-8' >> ~/.bashrc
fi

cd "$work_dir"
if [ ! -d "$work_dir/pitest" ]; then
    git clone https://github.com/yheechan/pitest.git
    cd "$work_dir/pitest"
    mvn clean package -DskipTests
    
    PITEST_JAR="$work_dir/pitest/pitest-command-line/target/pitest-command-line-dev-SNAPSHOT.jar"
    PIT_REPORTER_CLASS="org.pitest.mutationtest.commandline.MutationCoverageReport"
    JUNIT4_JAR="$D4J_HOME/framework/projects/lib/junit-4.12-hamcrest-1.3.jar"

    grep -qxF "export PITEST_JAR=\"$PITEST_JAR\"" ~/.bashrc || echo "export PITEST_JAR=\"$PITEST_JAR\"" >> ~/.bashrc
    grep -qxF "export PIT_REPORTER_CLASS=\"$PIT_REPORTER_CLASS\"" ~/.bashrc || echo "export PIT_REPORTER_CLASS=\"$PIT_REPORTER_CLASS\"" >> ~/.bashrc
    grep -qxF "export JUNIT4_JAR=\"$JUNIT4_JAR\"" ~/.bashrc || echo "export JUNIT4_JAR=\"$JUNIT4_JAR\"" >> ~/.bashrc
fi

    
