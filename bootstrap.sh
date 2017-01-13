#!/usr/bin/env bash

setup_ubuntu ()
{

	# enable the multiverse package repositories.
	sudo sed -i "/^# deb.*multiverse/ s/^# //" /etc/apt/sources.list

	if [[ `lsb_release -rs` == "14.04" ]]
	then
		sudo add-apt-repository --yes ppa:fkrull/deadsnakes
	fi

	sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
	wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | sudo apt-key add -

	sudo apt-get update
	sudo apt-get dist-upgrade -y

	echo Creating 2GB swap file \(this is occationally required when fetching extremely large files\).

	# Create swapfile of 2GB with block size 1MB
	sudo /bin/dd if=/dev/zero of=/swapfile bs=1024 count=2097152
	sudo /sbin/mkswap /swapfile
	sudo /sbin/swapon /swapfile
	sudo /bin/echo '/swapfile          swap            swap    defaults        0 0' | sudo tee -a /etc/fstab
	sudo mount -a

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

}

build_py_from_sauce_3_5 ()
{
	sudo  apt-get update
	sudo cd /tmp
	sudo apt-get install libssl-dev openssl
	sudo  cd opt
	sudo wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
	sudo  tar -xvzf Python-3.5.2.tgz

	cd Python-3.5.2
	sudo  ./configure
	sudo make -j 2
	sudo make install
}

build_py_from_sauce_3_4 ()
{
	sudo  apt-get update
	sudo cd /tmp
	sudo apt-get install libssl-dev openssl
	sudo  cd opt
	sudo wget https://www.python.org/ftp/python/3.4.5/Python-3.4.5.tgz
	sudo  tar -xvzf Python-3.4.5.tgz

	cd Python-3.4.5
	sudo  ./configure
	sudo make -j 2
	sudo make install
}

setup_debian ()
{
	sudo apt-get update
	sudo apt-get dist-upgrade -y

	echo Creating 2GB swap file \(this is occationally required when fetching extremely large files\).

	# Create swapfile of 2GB with block size 1MB
	sudo /bin/dd if=/dev/zero of=/swapfile bs=1024 count=2097152
	sudo /sbin/mkswap /swapfile
	sudo /sbin/swapon /swapfile
	sudo /bin/echo '/swapfile          swap            swap    defaults        0 0' | sudo tee -a /etc/fstab
	sudo mount -a

	sudo apt-get install -y build-essential

	sudo apt-get install -y libyaml-dev
	sudo apt-get install -y unrar
	sudo apt-get install -y git
	sudo apt-get install -y wget


	# PIL/Pillow support stuff
	sudo apt-get install -y libtiff5-dev
	sudo apt-get install -y libjpeg-turbo8-dev
	sudo apt-get install -y zlib1g-dev
	sudo apt-get install -y liblcms2-dev
	sudo apt-get install -y libwebp-dev
	sudo apt-get install -y libxml2
	sudo apt-get install -y libxslt1-dev
	sudo apt-get install -y libbz2-dev

	# Install Numpy/Scipy support packages. Yes, scipy depends on FORTAN. Arrrgh
	sudo apt-get install -y gfortran
	sudo apt-get install -y libopenblas-dev
	sudo apt-get install -y liblapack-dev

	# So debian is retarded, and wheezy doesn't ship anything from this decade.
	# Fukkit, build from source
	# build_py_from_sauce_3_5
	build_py_from_sauce_3_4
}

setup_postgres()
{
	sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
	wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | sudo apt-key add -

	sudo apt-get update

	sudo apt-get install -y postgresql-client
	sudo apt-get install -y postgresql-common
	sudo apt-get install -y libpq-dev
	sudo apt-get install -y postgresql-9.6
	sudo apt-get install -y postgresql-server-dev-9.6
	sudo apt-get install -y postgresql-contrib

	echo Setting up Database

	echo 'local   test_db         all                                     md5' | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
	service postgresql reload

	sudo -u postgres psql -c 'CREATE DATABASE test_db;'
	sudo -u postgres psql -c "CREATE USER test_user WITH PASSWORD '2YwzyARHG8agtRdE';"
	sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;'
}

setup_python()
{

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

}

run_tests()
{

	echo Doing setup for user: $1

sudo -u $1 -H bash <<EOF
cd ~/;
git clone https://github.com/fake-name/IntraArchiveDeduplicator.git;
cd IntraArchiveDeduplicator;
chmod +x runTests.sh;

touch settings.py;

./runTests.sh;

EOF

}


platform_str=$(cat /etc/*-release);

if echo $platform_str | grep -i "ubuntu";
then
	echo "Doing ubuntu setup"
	setup_ubuntu
	setup_postgres
	setup_python
	if [[ `lsb_release -rs` == "14.04" ]]
	then
		username="vagrant"
	elif [[ `lsb_release -rs` == "16.04" ]]
	then
		username="ubuntu"
	else
		echo Unknown platform: $(lsb_release -rs)
		exit 1
	fi
	run_tests "$username"
elif echo $platform_str | grep -i "debian";
then
	echo "Doing debian setup"
	setup_debian
	setup_postgres
	setup_python
	run_tests vagrant
else
	echo "Unknown platform";
fi

