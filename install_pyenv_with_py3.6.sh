#! /bin/bash
# Author: bugnofree
# Date: 2018-12-07
# Contact: pwnkeeper@gmail.com

# install pyenv
haspyenv=NO
hash pyenv 2>/dev/null && haspyenv=YES
if [[ $haspyenv == "NO" ]]
then
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    shim='
    # pyenv
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    if command -v pyenv 1>/dev/null 2>&1; then
        eval "$(pyenv init -)"
    fi
    '
    shconf=~/.bashrc
    shname=$(basename $(echo $SHELL))
    if [[ $shname == "zsh" ]]
    then
        shconf=~/.zshrc
    fi
    echo "$shim" >> $shconf
fi

# install python 3.6.0
haspy36=NO && pyenv versions --bare | grep -E "3\.6|3\.7|3\.8" 2>&1 >/dev/null && haspy36=YES
if [[ $haspy36 == "NO" ]]
then
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev
    pyenv install 3.6.0
    pyenv local 3.6.0
    pip3 install paramiko
fi
exec $SHELL
