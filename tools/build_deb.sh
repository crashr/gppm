#!/bin/bash

# Replace these variables with your own
PACKAGE_NAME="gppm"
VERSION="0.0.0"
MAINTAINER="Roni <noname@nowhere.com>"
DESCRIPTION="GPU Power and Performance Manager"
ARCHITECTURE="amd64"

# Directory where the package files will be stored
DEST_DIR="debian/$PACKAGE_NAME"

# Create the directory structure
mkdir -p $DEST_DIR/DEBIAN
mkdir -p $DEST_DIR/usr/bin
mkdir -p $DEST_DIR/usr/local/lib/$PACKAGE_NAME
mkdir -p $DEST_DIR/etc/$PACKAGE_NAME
mkdir -p $DEST_DIR/var/log/$PACKAGE_NAME
mkdir -p $DEST_DIR/lib/systemd/system

# Create the control file
echo "Package: $PACKAGE_NAME" > $DEST_DIR/DEBIAN/control
echo "Version: $VERSION" >> $DEST_DIR/DEBIAN/control
echo "Section: base" >> $DEST_DIR/DEBIAN/control
echo "Priority: optional" >> $DEST_DIR/DEBIAN/control
echo "Architecture: $ARCHITECTURE" >> $DEST_DIR/DEBIAN/control
echo "Essential: no" >> $DEST_DIR/DEBIAN/control
#echo "Depends: python3, python3-venv" >> $DEST_DIR/DEBIAN/control
echo "Maintainer: $MAINTAINER" >> $DEST_DIR/DEBIAN/control
echo "Description: $DESCRIPTION" >> $DEST_DIR/DEBIAN/control

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

# Create the trigger file
#echo "systemctl daemon-reload" > $DEST_DIR/DEBIAN/triggers

# Create a virtual environment and install dependencies
python3 -m venv $DEST_DIR/usr/local/lib/$PACKAGE_NAME/venv
source $DEST_DIR/usr/local/lib/$PACKAGE_NAME/venv/bin/activate
pip install -r requirements.txt

# Compile your Python project to a binary
# Replace 'your_main_script.py' with the name of your main script
python -m PyInstaller --onefile gppmd.py --distpath $DEST_DIR/usr/bin
python -m PyInstaller --onefile gppm.py --distpath $DEST_DIR/usr/bin

# Deactivate the virtual environment
deactivate

# Create a sample configuration file
echo "This is a sample configuration file for gppm." > $DEST_DIR/etc/$PACKAGE_NAME/config.ini

# Create the systemd service file
echo "[Unit]" > $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "Description=GPU Power and Performance Manager Daemon" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "[Service]" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "ExecStart=/usr/bin/gppmd" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "Restart=always" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "User=root" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "Group=root" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "StandardOutput=syslog" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}.service
echo "StandardError=syslog" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "SyslogIdentifier=gppmd" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "[Install]" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service
echo "WantedBy=multi-user.target" >> $DEST_DIR/lib/systemd/system/${PACKAGE_NAME}d.service

#sudo chown -R root:root $DEST_DIR

# Build the package
dpkg-deb --build $DEST_DIR
