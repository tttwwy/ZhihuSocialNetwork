# general dependencies
sudo apt-get install -y mongodb-server python-bs4 python-numpy python-scipy python-requests python-lxml python-cssselect python-pymongo speedometer

# install scikit-learn
sudo apt-get install -y build-essential python-dev python-setuptools python-numpy python-scipy python-matplotlib libatlas-dev libatlas3gf-base
sudo update-alternatives --set libblas.so.3 /usr/lib/atlas-base/atlas/libblas.so.3
sudo update-alternatives --set liblapack.so.3 /usr/lib/atlas-base/atlas/liblapack.so.3
pip install jieba ipython
pip install --user --install-option="--prefix=" -U scikit-learn
