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

PACKAGE_NAME="gppmd"
VERSION="$(cat VERSION)"
RELEASE="$(cat RELEASE)"
MAINTAINER="Roni"
DESCRIPTION="GPU Power and Performance Manager daemon"
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

# Ensure the requirements.txt file exists
if [ ! -f "$PACKAGE_NAME/requirements.txt" ]
then
  echo "$PACKAGE_NAME/requirements.txt could not be found"
  exit
fi

## Ensure PyInstaller is installed
#if ! pip show PyInstaller &> /dev/null
#then
#  echo "PyInstaller is not installed"
#  exit
#fi

# Create the directory structure
mkdir -p $DEST_DIR/DEBIAN
mkdir -p $DEST_DIR/usr/bin
mkdir -p $DEST_DIR/etc/$PACKAGE_NAME
mkdir -p $DEST_DIR/etc/$PACKAGE_NAME/llamacpp_configs
mkdir -p $DEST_DIR/var/log/$PACKAGE_NAME
mkdir -p $DEST_DIR/lib/systemd/system

# Create the control file
cat > $DEST_DIR/DEBIAN/control <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: base
Priority: optional
Architecture: $ARCHITECTURE
Essential: no
Maintainer: $MAINTAINER
Description: $DESCRIPTION
EOF

# Create the postinst script
cat > $DEST_DIR/DEBIAN/postinst <<EOF
#!/bin/sh
set -e

case "\$1" in
  configure)
    systemctl daemon-reload
    ;;
  *)
    ;;
esac
EOF

chmod +x $DEST_DIR/DEBIAN/postinst

# Create a virtual environment and install dependencies
#python3 -m venv $DEST_DIR/usr/local/lib/$PACKAGE_NAME/venv
#source $DEST_DIR/usr/local/lib/$PACKAGE_NAME/venv/bin/activate
#pip install -r $PACKAGE_NAME/requirements.txt
python3 -m venv $PACKAGE_NAME/venv
source $PACKAGE_NAME/venv/bin/activate
pip install -r $PACKAGE_NAME/requirements.txt

# Compile your Python project to a binary
pyinstaller --onefile $PACKAGE_NAME/$PACKAGE_NAME.py --distpath $DEST_DIR/usr/bin

# Deactivate the virtual environment
deactivate

# Create a basic configuration file
cp $PACKAGE_NAME/${PACKAGE_NAME}_config.yaml $DEST_DIR/etc/$PACKAGE_NAME/$PACKAGE_NAME.yaml

# Create a basic configuration file
cp $PACKAGE_NAME/llamacpp_configs/examples.yaml $DEST_DIR/etc/$PACKAGE_NAME/llamacpp_configs/examples.yaml

# Create the systemd service file
cat > $DEST_DIR/lib/systemd/system/$PACKAGE_NAME.service <<EOF
[Unit]
Description=GPU Power and Performance Manager Daemon

[Service]
ExecStart=/usr/bin/$PACKAGE_NAME
Restart=always
User=root
Group=root
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$PACKAGE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Ensure the systemd service file is created successfully
if [ ! -f "$DEST_DIR/lib/systemd/system/$PACKAGE_NAME.service" ]
then
  echo "Failed to create $PACKAGE_NAME.service"
  exit
fi

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
