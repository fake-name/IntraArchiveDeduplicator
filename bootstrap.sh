#!/usr/bin/env bash

# enable the multiverse package repositories.
sed -i "/^# deb.*multiverse/ s/^# //" /etc/apt/sources.list

apt-get update
apt-get dist-upgrade -y

echo Creating 2GB swap file \(this is occationally required when fetching extremely large files\).

# Create swapfile of 2GB with block size 1MB
/bin/dd if=/dev/zero of=/swapfile bs=1024 count=2097152
/sbin/mkswap /swapfile
/sbin/swapon /swapfile
/bin/echo '/swapfile          swap            swap    defaults        0 0' >> /etc/fstab

sudo apt-get install -y python3.5 python3.5-dev build-essential postgresql-client postgresql-common libpq-dev postgresql-9.5 unrar
sudo apt-get install -y postgresql-server-dev-9.5 postgresql-contrib libyaml-dev git wget

# PIL/Pillow support stuff
sudo apt-get install -y libtiff5-dev libjpeg-turbo8-dev zlib1g-dev liblcms2-dev libwebp-dev libxml2 libxslt1-dev

# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
sudo apt-get install -y gfortran libopenblas-dev liblapack-dev


echo Installing required python libraries
# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py -nv
sudo python3 get-pip.py
rm get-pip.py


# And numpy itself
pip3 install numpy
pip3 install scipy

# Install the libraries we actually need
pip3 install rarfile python-magic cython psycopg2 Colorama
pip3 install python-sql rpyc server_reloader
pip3 install Coverage Bitstring nose
pip3 install pytz apscheduler
pip3 install git+https://github.com/fake-name/UniversalArchiveInterface.git

# So pillow keeps changing the behaviour of image.resize. Arrrgh.
pip3 install pillow=='3.3.1'



echo Setting up Database

echo 'local   test_db         all                                     md5' >> /etc/postgresql/9.3/main/pg_hba.conf
service postgresql reload

sudo -u postgres psql -c 'CREATE DATABASE test_db;'
sudo -u postgres psql -c "CREATE USER test_user WITH PASSWORD '2YwzyARHG8agtRdE';"
sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;'


sudo -u vagrant bash <<EOF
git clone https://github.com/fake-name/IntraArchiveDeduplicator.git
cd IntraArchiveDeduplicator
chmod +x runTests.sh

touch settings.py

./runTests.sh

EOF



