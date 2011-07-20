
VENV=vendor

find . -name "*.pyc" | xargs rm

pushd $VENV
virtualenv $VENV
source $VENV/bin/activate

cd /var/www/apiserver

pip install -q -r requirements.txt

git submodule sync -q
git submodule update --init

python main.py

