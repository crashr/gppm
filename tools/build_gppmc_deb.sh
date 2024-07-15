#!/bin/bash

# Ensure necessary tools are installed
for tool in python3 pip dpkg-deb
do
  if ! command -v $tool &> /dev/null
  then
    echo "$tool could not be found"
    exit
  fi
done

PACKAGE_NAME="gppmc"
VERSION="$(cat VERSION)"
RELEASE="$(cat RELEASE)"
MAINTAINER="Roni"
DESCRIPTION="GPU Power and Performance Manager command line tool"
ARCHITECTURE="amd64"

DEST_DIR="build/$PACKAGE_NAME-v$VERSION-${RELEASE}_$ARCHITECTURE"

# Clean build dir 
sudo rm -rf $DEST_DIR

# Ensure the Python project file exists
if [ ! -f "$PACKAGE_NAME/$PACKAGE_NAME.py" ]
then
  echo "$PACKAGE_NAME/$PACKAGE_NAME.py could not be found"
  exit
fi

# Ensure the configuration file exists
if [ ! -f "$PACKAGE_NAME/${PACKAGE_NAME}_config.yaml" ]
then
  echo "$PACKAGE_NAME/${PACKAGE_NAME}_config.yaml could not be found"
  exit
fi

## Ensure the requirements.txt file exists
#if [ ! -f "$PACKAGE_NAME/requirements.txt" ]
#then
#  echo "$PACKAGE_NAME/requirements.txt could not be found"
#  exit
#fi

# Ensure PyInstaller is installed
#if ! pip show PyInstaller &> /dev/null
#then
#  echo "PyInstaller is not installed"
#  exit
#fi

# Create the directory structure
mkdir -p $DEST_DIR/DEBIAN
mkdir -p $DEST_DIR/etc/bash_completion.d
mkdir -p $DEST_DIR/usr/bin
mkdir -p $DEST_DIR/usr/share/bash-completion/completions
mkdir -p $DEST_DIR/usr/share/$PACKAGE_NAME

# Create the control file
cat > $DEST_DIR/DEBIAN/control <<EOF
Package: $PACKAGE_NAME
Version: ${VERSION}-${RELEASE}
Section: base
Priority: optional
Architecture: $ARCHITECTURE
Essential: no
Maintainer: $MAINTAINER
Description: $DESCRIPTION
EOF

# Create a virtual environment and install dependencies
python3 -m venv $PACKAGE_NAME/venv
source $PACKAGE_NAME/venv/bin/activate
pip install -r $PACKAGE_NAME/requirements.txt

# Compile your Python project to a binary
pyinstaller --hidden-import=requests --onefile $PACKAGE_NAME/$PACKAGE_NAME.py --distpath $DEST_DIR/usr/bin

# Create bash completion file
_GPPMC_COMPLETE=bash_source $DEST_DIR/usr/bin/$PACKAGE_NAME > $DEST_DIR/usr/share/bash-completion/completions/$PACKAGE_NAME

# Deactivate the virtual environment
deactivate

# Create a basic configuration file
cp $PACKAGE_NAME/${PACKAGE_NAME}_config.yaml $DEST_DIR/usr/share/$PACKAGE_NAME/$PACKAGE_NAME.yaml

sudo chown -R root:root build/*

# Build the package
sudo dpkg-deb --build $DEST_DIR

# Ensure the package is built successfully
if [ ! -f "$DEST_DIR.deb" ]
then
  echo "Failed to build $PACKAGE_NAME.deb"
  exit
fi

# Cleanup
sudo rm -rf ./build/$PACKAGE_NAME
rm -rf ./$PACKAGE_NAME/venv
rm -rf ./*.spec
