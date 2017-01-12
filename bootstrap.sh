#!/usr/bin/env bash

# enable the multiverse package repositories.
sudo sed -i "/^# deb.*multiverse/ s/^# //" /etc/apt/sources.list

if [[ `lsb_release -rs` == "14.04" ]]
then
	sudo add-apt-repository --yes ppa:fkrull/deadsnakes
	sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
	wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | sudo apt-key add -
fi


sudo apt-get update
sudo apt-get dist-upgrade -y

echo Creating 2GB swap file \(this is occationally required when fetching extremely large files\).

# Create swapfile of 2GB with block size 1MB
/bin/dd if=/dev/zero of=/swapfile bs=1024 count=2097152
/sbin/mkswap /swapfile
/sbin/swapon /swapfile
/bin/echo '/swapfile          swap            swap    defaults        0 0' >> /etc/fstab

sudo apt-get install -y python3.5 python3.5-dev build-essential postgresql-client postgresql-common libpq-dev postgresql-9.6 unrar
sudo apt-get install -y postgresql-server-dev-9.6 postgresql-contrib libyaml-dev git wget

# Replace system python on 14.04
# Probably not the best idea if you use the system seriously, but
# I don't care for testing.
if [[ `lsb_release -rs` == "14.04" ]]
then
	sudo mv /usr/bin/python3 /usr/bin/python3-old
	sudo ln -s /usr/bin/python3.5 /usr/bin/python3
fi

# PIL/Pillow support stuff
sudo apt-get install -y libtiff5-dev libjpeg-turbo8-dev zlib1g-dev liblcms2-dev libwebp-dev libxml2 libxslt1-dev

# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
sudo apt-get install -y gfortran libopenblas-dev liblapack-dev


echo Installing required python libraries
# Install pip (You cannot use the ubuntu repos for this, because they will also install python3.2)
wget https://bootstrap.pypa.io/get-pip.py -nv
sudo python3.5 get-pip.py
rm get-pip.py


# And numpy itself
sudo pip3 install numpy
sudo pip3 install scipy

# Install the libraries we actually need
sudo pip3 install rarfile python-magic cython psycopg2 Colorama
sudo pip3 install python-sql rpyc server_reloader
sudo pip3 install Coverage Bitstring nose
sudo pip3 install pytz apscheduler
sudo pip3 install git+https://github.com/fake-name/UniversalArchiveInterface.git

# So pillow keeps changing the behaviour of image.resize. Arrrgh.
sudo pip3 install pillow=='3.3.1'



echo Setting up Database

echo 'local   test_db         all                                     md5' | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
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



